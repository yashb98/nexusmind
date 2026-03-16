---
name: llm-integration
description: Work on LLM calls, LiteLLM routing, RunPod/Anthropic providers, Langfuse tracing, streaming, embeddings, prompt templates, or src/llm/ directory
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: LLM Integration & Observability

## When to use
Use this skill when working on LLM calls, prompt templates, LiteLLM routing, Langfuse tracing, streaming, or anything in `src/llm/`.

## LLM Routing (LiteLLM)
```python
# Primary: RunPod Serverless vLLM
primary = {
    "model": "openai/Qwen/Qwen2.5-7B-Instruct",
    "api_base": f"https://api.runpod.ai/v2/{ENDPOINT_ID}/openai/v1",
    "api_key": RUNPOD_API_KEY,
}

# Fallback: Anthropic Claude
fallback = {
    "model": "anthropic/claude-sonnet-4-20250514",
    "api_key": ANTHROPIC_API_KEY,
}

# Future local: MLX on Mac Studio
local = {
    "model_path": "mlx-community/Qwen2.5-7B-Instruct-4bit",
    "adapter_dir": "./adapters",
}
```

### Routing logic:
1. Try primary (RunPod)
2. If RunPod fails (timeout, 5xx): try fallback (Anthropic)
3. If both fail: raise LLMServiceError with details

## Langfuse Tracing (MANDATORY)
EVERY LLM call MUST be wrapped in a Langfuse trace. No exceptions.

```python
from langfuse import Langfuse

langfuse = Langfuse(
    public_key=config.langfuse_public_key,
    secret_key=config.langfuse_secret_key,
    host=config.langfuse_host,
)

async def generate(self, system_prompt, messages, trace_id, stream=False):
    trace = langfuse.trace(
        id=trace_id,
        name="llm_generation",
        metadata={"model": self.config.model},
    )
    generation = trace.generation(
        name="chat_completion",
        model=self.config.model,
        input={"system": system_prompt, "messages": messages},
    )
    
    try:
        response = await litellm.acompletion(
            model=self.config.model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            max_tokens=512,
            temperature=0.7,
            stream=stream,
        )
        
        if stream:
            # Return async generator
            async def stream_and_trace():
                full_text = ""
                async for chunk in response:
                    token = chunk.choices[0].delta.content or ""
                    full_text += token
                    yield token
                generation.end(output=full_text)
            return stream_and_trace()
        else:
            result = response.choices[0].message.content
            generation.end(output=result)
            return result
    except Exception as e:
        generation.end(error=str(e))
        raise
```

## Streaming
- User-facing conversations: `stream=True` (tokens appear in real-time)
- Background conversations: `stream=False` (collect full response)
- Tutor commentary: `stream=False` (short messages, not worth streaming)
- Teach-back: `stream=True` (feels more natural)

## Embedding
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")  # 768 dimensions, runs on CPU

def embed(text: str) -> list[float]:
    return model.encode(text).tolist()

def embed_batch(texts: list[str]) -> list[list[float]]:
    return model.encode(texts).tolist()
```

## DSPy Modules (Structured Output)
4 LLM call sites use DSPy instead of raw prompts for reliable structured output:

| Module | Location | Input → Output |
|--------|----------|----------------|
| SkepticModule | dspy_modules/verification.py | claim, evidence → score, reasoning |
| ConnectorModule | dspy_modules/verification.py | claim, graph context → novelty, connections |
| JudgeModule | dspy_modules/verification.py | scores, reasoning → decision |
| InsightExtractor | dspy_modules/extraction.py | transcript → insights[], entities[] |
| EntityRelationExtractor | dspy_modules/extraction.py | text → entities[], relations[] |
| BloomAssessor | dspy_modules/assessment.py | exchange → level (1-6), reasoning |
| QualityJudge | dspy_modules/assessment.py | transcript → multi-dim scores |

DSPy uses the SAME LiteLLM backend (RunPod primary → Anthropic fallback).
Temperature 0.3 for DSPy (deterministic), 0.7 for conversations (creative).
ALL DSPy calls still wrapped in Langfuse traces.

## Prompt Templates (Hand-Written — NOT DSPy)
All prompts stored in `src/llm/prompts.py` as string constants with `{placeholder}` format.

Key templates:
- `PERSONALITY_PROMPT` — agent conversation turn
- `EMBEDDED_TUTOR_PROMPT` — tutor during live debate
- `TEACHBACK_PROMPT` — standalone teach-back session
- `SKEPTIC_PROMPT` — Verification Council Skeptic
- `CONNECTOR_PROMPT` — Verification Council Connector
- `JUDGE_PROMPT` — Verification Council Judge
- `EXTRACTION_PROMPT` — insight extraction from conversations
- `ENTITY_EXTRACTION_PROMPT` — GraphRAG entity/relation extraction
- `QUALITY_JUDGE_PROMPT` — conversation quality scoring
- `BLOOM_ASSESSMENT_PROMPT` — Bloom level assessment

## Rules
- EVERY LLM call traced in Langfuse (no exceptions)
- NEVER hardcode model names — use config
- ALWAYS set max_tokens (default 512 for conversations, 1024 for extraction)
- Temperature 0.7 for conversations, 0.3 for extraction/evaluation (more deterministic)
- Trace IDs should be correlatable: `{conversation_id}_turn_{N}` or `{conversation_id}_tutor_{N}`
