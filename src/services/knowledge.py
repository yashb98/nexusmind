"""Knowledge extraction — insights, entities, and relations from conversations."""

import json
import uuid

import structlog

from src.db import neo4j_client
from src.llm import llm_service
from src.llm.embeddings import embed
from src.services import memory as memory_service

logger = structlog.get_logger(__name__)

EXTRACTION_PROMPT = """Analyze this conversation transcript and extract knowledge.

TOPIC: {topic}

TRANSCRIPT:
{transcript}

Return a JSON object with exactly these keys:
{{
    "insights": [
        {{"content": "...", "importance": 0.0-1.0, "bloom_relevance": 1-6}}
    ],
    "entities": [
        {{"name": "...", "type": "concept|technology|...", "description": "..."}}
    ],
    "relations": [
        {{"source": "name", "target": "name", "type": "CAUSES|...", "confidence": 0.0-1.0}}
    ]
}}

Rules:
- Extract 1-5 key insights discovered or challenged
- Extract entities mentioned: concepts, technologies, organizations
- Extract typed relations between entities
- Be specific — use exact names from the conversation
- Return ONLY valid JSON, no other text"""


async def extract_knowledge(
    transcript: str,
    topic: str,
    conversation_id: str,
    tenant_id: str,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Extract insights, entities, and relations from a conversation."""
    prompt = EXTRACTION_PROMPT.format(topic=topic, transcript=transcript[:3000])

    try:
        response = await llm_service.generate(
            system_prompt="You are a knowledge extraction system. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            trace_id=f"{conversation_id}-extraction",
            temperature=0.3,
        )

        data = _parse_extraction(response)
        insights = data.get("insights", [])
        entities = data.get("entities", [])
        relations = data.get("relations", [])

        # Store entities in Neo4j
        for entity in entities:
            await _store_entity(entity, conversation_id)

        # Store relations in Neo4j
        for relation in relations:
            await _store_relation(relation, conversation_id)

        # Store insights in Neo4j + Qdrant
        for insight in insights:
            await _store_insight(insight, conversation_id, tenant_id)

        logger.info(
            "knowledge_extracted",
            conversation_id=conversation_id,
            insights=len(insights),
            entities=len(entities),
            relations=len(relations),
        )

        return insights, entities, relations

    except Exception as e:
        logger.warning("knowledge_extraction_error", error=str(e))
        return [], [], []


def _parse_extraction(response: str) -> dict:
    """Parse LLM extraction response as JSON."""
    # Try to find JSON in the response
    text = response.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1]) if len(lines) > 2 else text

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

    logger.warning("extraction_parse_failed", response=text[:200])
    return {"insights": [], "entities": [], "relations": []}


async def _store_entity(entity: dict, conversation_id: str) -> None:
    """Store an entity node in Neo4j."""
    entity_id = str(uuid.uuid4())
    await neo4j_client.execute_write(
        """MERGE (e:Entity {name: $name})
           ON CREATE SET e.id = $id,
                         e.type = $type,
                         e.description = $desc,
                         e.first_mentioned = datetime(),
                         e.mention_count = 1,
                         e.confidence = 0.7
           ON MATCH SET e.mention_count = e.mention_count + 1,
                        e.description = CASE
                            WHEN size($desc) > size(e.description)
                            THEN $desc ELSE e.description END""",
        id=entity_id,
        name=entity["name"],
        type=entity.get("type", "concept"),
        desc=entity.get("description", ""),
    )


async def _store_relation(relation: dict, conversation_id: str) -> None:
    """Store a typed relation between entities in Neo4j."""
    rel_type = relation.get("type", "RELATES_TO")
    valid_types = {"CAUSES", "CONTRADICTS", "SUPPORTS", "RELATES_TO"}
    if rel_type not in valid_types:
        rel_type = "RELATES_TO"

    # Use parameterized query with APOC or simple merge
    await neo4j_client.execute_write(
        f"""MATCH (e1:Entity {{name: $source}})
           MATCH (e2:Entity {{name: $target}})
           MERGE (e1)-[r:{rel_type}]->(e2)
           SET r.confidence = $confidence,
               r.source_conversation = $conv_id,
               r.discovered_at = datetime()""",
        source=relation["source"],
        target=relation["target"],
        confidence=relation.get("confidence", 0.5),
        conv_id=conversation_id,
    )


async def _store_insight(insight: dict, conversation_id: str, tenant_id: str) -> None:
    """Store an insight in Neo4j and Qdrant."""
    insight_id = str(uuid.uuid4())
    content = insight.get("content", "")

    # Neo4j
    await neo4j_client.execute_write(
        """CREATE (i:Insight {
               id: $id,
               content: $content,
               importance: $importance,
               bloom_relevance: $bloom,
               verification_status: 'unverified',
               discovered_at: datetime()
           })
           WITH i
           MATCH (c:Conversation {id: $conv_id})
           CREATE (c)-[:PRODUCED]->(i)""",
        id=insight_id,
        content=content,
        importance=insight.get("importance", 0.5),
        bloom=insight.get("bloom_relevance", 1),
        conv_id=conversation_id,
    )

    # Qdrant hot memory
    try:
        embedding = embed(content)
        await memory_service.store_memory(
            agent_id=insight_id,
            tenant_id=tenant_id,
            content=content,
            embedding=embedding,
            memory_type="conversation_insight",
            importance=insight.get("importance", 0.5),
            source_conversation_id=conversation_id,
        )
    except Exception as e:
        logger.warning("insight_memory_store_failed", error=str(e))
