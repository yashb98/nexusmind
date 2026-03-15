"""Always-on background agent scheduler — EXPLORE / RESEARCH / REFINE."""

import asyncio
import random
import uuid
from datetime import UTC, datetime

import structlog

from src.config import settings
from src.db import neo4j_client, postgres
from src.services import conversation as conv_service
from src.services import search as search_service

logger = structlog.get_logger(__name__)


class AgentScheduler:
    """Background scheduler for autonomous agent work."""

    def __init__(self) -> None:
        self.running = False
        self.paused = False
        self.cycle_count = 0
        self.mode_counts: dict[str, int] = {
            "explore": 0,
            "research": 0,
            "refine": 0,
        }
        self.hourly_count = 0
        self._last_hour_reset = datetime.now(UTC).hour

    async def run_forever(self) -> None:
        """Main loop — picks mode and executes."""
        self.running = True
        logger.info("scheduler_started")

        while self.running:
            if self.paused:
                await asyncio.sleep(5)
                continue

            # Reset hourly counter
            current_hour = datetime.now(UTC).hour
            if current_hour != self._last_hour_reset:
                self.hourly_count = 0
                self._last_hour_reset = current_hour

            # Rate limit
            if self.hourly_count >= settings.scheduler.max_hourly:
                await asyncio.sleep(30)
                continue

            mode = self._pick_mode()
            self.cycle_count += 1
            self.mode_counts[mode] += 1
            self.hourly_count += 1

            try:
                await self._execute_mode(mode)
            except Exception as e:
                logger.error("scheduler_cycle_failed", mode=mode, error=str(e))

            await asyncio.sleep(settings.scheduler.cycle_seconds)

    def _pick_mode(self) -> str:
        """Weighted random mode selection."""
        modes = ["explore", "research", "refine"]
        weights = [
            settings.scheduler.explore_weight,
            settings.scheduler.research_weight,
            settings.scheduler.refine_weight,
        ]
        return random.choices(modes, weights=weights)[0]

    async def _execute_mode(self, mode: str) -> None:
        """Execute a single scheduler cycle."""
        start = datetime.now(UTC)
        conversation_id = None
        topic = None

        if mode == "explore":
            conversation_id, topic = await self._explore()
        elif mode == "research":
            topic = await self._research()
        elif mode == "refine":
            conversation_id, topic = await self._refine()

        duration = (datetime.now(UTC) - start).total_seconds()

        # Log metrics
        await self._log_metrics(mode, topic, conversation_id, duration)

        logger.info(
            "scheduler_cycle",
            mode=mode,
            cycle=self.cycle_count,
            duration=f"{duration:.1f}s",
        )

    async def _explore(self) -> tuple[str | None, str | None]:
        """Find unexplored agent pairs and trigger debate."""
        pair = await self._get_best_unexplored_pair()
        if not pair:
            return None, None

        state = await conv_service.run_socratic_debate(
            agent_a_id=pair["a_id"],
            agent_b_id=pair["b_id"],
            topic=pair["topic"],
            tenant_id=pair["tenant_id"],
            background=True,
        )
        return state["conversation_id"], pair["topic"]

    async def _research(self) -> str | None:
        """Find agents with stale knowledge and research new info."""
        # Find a topic that hasn't been discussed recently
        topics = await neo4j_client.execute_read(
            """MATCH (t:Topic)
               RETURN t.name AS name
               ORDER BY t.mention_count ASC
               LIMIT 1""",
        )
        if not topics:
            return None

        topic = topics[0]["name"]
        summary = await search_service.search_and_summarize(topic)

        logger.info("research_completed", topic=topic, summary_len=len(summary))
        return topic

    async def _refine(self) -> tuple[str | None, str | None]:
        """Find contradictions and resolve via debate."""
        contradictions = await neo4j_client.execute_read(
            """MATCH (e1:Entity)-[:CONTRADICTS]->(e2:Entity)
               RETURN e1.name AS entity1, e2.name AS entity2
               LIMIT 1""",
        )
        if not contradictions:
            return None, None

        topic = f"Resolving: {contradictions[0]['entity1']} vs {contradictions[0]['entity2']}"
        return None, topic

    async def _get_best_unexplored_pair(self) -> dict | None:
        """Find agent pair with shared interests that haven't debated."""
        records = await neo4j_client.execute_read(
            """MATCH (a:Agent), (b:Agent)
               WHERE a <> b AND NOT (a)-[:KNOWS]->(b)
                 AND a.tenant_id = b.tenant_id
               WITH a, b,
                    [x IN a.interests WHERE x IN b.interests] AS shared
               WHERE size(shared) > 0
               RETURN a.id AS a_id, b.id AS b_id,
                      a.tenant_id AS tenant_id,
                      shared[0] AS topic
               LIMIT 1""",
        )
        return records[0] if records else None

    async def _log_metrics(
        self,
        mode: str,
        topic: str | None,
        conversation_id: str | None,
        duration: float,
    ) -> None:
        """Log scheduler metrics to Postgres."""
        try:
            await postgres.execute(
                """INSERT INTO scheduler_metrics
                   (mode, agent_ids, topic, conversation_id,
                    quality_score, duration_seconds)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                mode,
                [],
                topic,
                uuid.UUID(conversation_id) if conversation_id else None,
                0.0,
                duration,
            )
        except Exception as e:
            logger.warning("metrics_log_failed", error=str(e))

    def pause(self) -> None:
        self.paused = True
        logger.info("scheduler_paused")

    def resume(self) -> None:
        self.paused = False
        logger.info("scheduler_resumed")

    def stop(self) -> None:
        self.running = False
        logger.info("scheduler_stopped")

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "paused": self.paused,
            "cycle_count": self.cycle_count,
            "hourly_count": self.hourly_count,
            "mode_distribution": self.mode_counts,
        }


# Singleton
scheduler = AgentScheduler()
