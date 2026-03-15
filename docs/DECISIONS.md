# DECISIONS.md — Architecture Decision Log
# Append new decisions at bottom. Never edit existing entries.

## ADR-001: Five-Layer Engineering Model (Living System)
**Date:** 2026-03-15
**Decision:** Build in five explicit layers: Agentic → Process → Environment → Evolution → Interface.
**Rationale:** Four layers create emergence. The fifth (Evolution) creates self-improvement. Without it, the system is smart but static. With it, the system improves itself every hour. The Evolution layer is what makes this a living system, not a product.

## ADR-002: RunPod Serverless First, Mac Studio Later
**Date:** 2026-03-15
**Decision:** Primary inference via RunPod Serverless vLLM. Mac Studio added later for 24/7 local operation. Same code — different .env.
**Rationale:** No upfront hardware cost. RunPod charges $0/idle, ~$0.002/conversation. Total demo cost under £55. Mac Studio becomes worthwhile when running 24/7 (paying users or always-on agents at scale).

## ADR-003: Socratic State Machine (Not Free-Form Chat)
**Date:** 2026-03-15
**Decision:** Conversations follow 6-phase state machine (OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT).
**Rationale:** Free-form chat degrades to shallow pleasantries. Structured Socratic protocol forces depth. SocraticLM outperforms GPT-4 by 12% on teaching. Phase progression ensures every conversation produces extractable knowledge.

## ADR-004: Internal Routing (Direct Python, Not HTTP Between Services)
**Date:** 2026-03-15
**Decision:** Services call each other via direct Python imports. Parallel I/O via asyncio.gather. Fire-and-forget for non-blocking updates.
**Rationale:** Monolith means zero benefit from HTTP between services. Parallel I/O reduces turn latency from ~6-8s to ~2-3s (LLM time only). Fire-and-forget for graph/memory updates means user doesn't wait for persistence.

## ADR-005: Three-Tier Memory (Hot + Graph + Cold)
**Date:** 2026-03-15
**Decision:** Hot memory (Qdrant, 30 days), knowledge graph (Neo4j entities with typed relations + SUPERSEDES), cold archive (Qdrant, >90 days low importance). GraphRAG entity extraction after each conversation.
**Rationale:** Single-tier memory grows unbounded and slows retrieval. Three tiers keep hot layer fast (~50ms). GraphRAG enables multi-hop reasoning that pure vector search misses. SUPERSEDES relation handles contradictions without data loss. Cold archive with 6-month cleanup prevents unbounded growth.

## ADR-006: Verification Council (Skeptic + Connector + Judge)
**Date:** 2026-03-15
**Decision:** All new knowledge passes through a 3-agent verification pipeline before storage. Also applied to fine-tuning training data.
**Rationale:** Without verification, hallucinated or low-quality insights corrupt the knowledge graph and training data. The Council costs ~£0.001 per verification (3 LLM calls) but prevents cascade failures. The model only learns from VERIFIED data.

## ADR-007: Progressive Distillation (Facts → Memory, Patterns → Weights)
**Date:** 2026-03-15
**Decision:** Four-tier distillation: working memory → episodic memory → micro-adapters (hourly, rank=4) → base adapter (nightly, rank=16). Facts always stored in searchable memory. Patterns (style, personality, skills) baked into weights.
**Rationale:** Fine-tuning after every conversation is impractical (25min pause, catastrophic forgetting). Pure memory-based approaches miss pattern learning. Separating facts from patterns gives best of both: fast pattern recall (weights) + updatable fact retrieval (memory). Hourly micro-adapters (2-3 min, rank=4) bridge the gap between real-time and nightly training.

## ADR-008: Always-On Background Agents
**Date:** 2026-03-15
**Decision:** Agent scheduler runs continuously in 3 modes: EXPLORE (40%), RESEARCH (30%), REFINE (30%). 5-10 conversations per hour with no human trigger.
**Rationale:** Idle agents waste the system's potential. Background work ensures the knowledge graph grows continuously, stale information is updated, contradictions are resolved, and the fine-tuning pipeline always has fresh training data. Cost: £9-18/month at medium frequency.

## ADR-009: Self-Evolution with Human Gate on Code
**Date:** 2026-03-15
**Decision:** Four autonomous loops: knowledge (continuous), model (hourly+nightly), research (weekly), code (weekly, human-approved PRs). Safe parameters (prompts, hyperparameters, retrieval config) auto-adjusted. Code changes require human review.
**Rationale:** 95% autonomous, 5% human-gated. The gate is on irreversible actions (code, schema, auth). Everything else is reversible (knowledge deletable, adapters rollback-able, prompts revertible). This is the difference between a brilliant system and a dangerous one.

## ADR-010: Scenario-Based Personality Onboarding
**Date:** 2026-03-15
**Decision:** 4-step UI: basics → interests → 10 scenario questions (BFI-10 rewritten as relatable situations) → privacy. Results shown as radar chart + natural language summary.
**Rationale:** People are bad at "rate yourself 1-5 on openness" but good at "what would you do in this situation." Scenario-based assessment is more accurate AND more engaging. BFI-10 validated across 56 countries. Personality seed improves via nightly fine-tuning from actual agent behavior.

## ADR-011: Bloom's Taxonomy for Teach-Back
**Date:** 2026-03-15
**Decision:** 6-level Bloom's Taxonomy for adaptive difficulty in teach-back. LLM-as-judge assesses demonstrated level per interaction.
**Rationale:** Bloom's maps to real pedagogy. Distinguishes "can recall a fact" (L1) from "can design a solution" (L6). This precision separates NexusMind from tutors that just adjust word complexity.

## ADR-012: Monolith for Demo, Microservices for Scale
**Date:** 2026-03-15
**Decision:** All services in ONE FastAPI app. Clean service boundaries enable future split.
**Rationale:** Zero benefit from microservices at <100 users. Single process = simpler deployment, debugging, testing. Internal routing (ADR-004) already optimizes performance within monolith.

## ADR-013: Trust-Adaptive Personality Expression
**Date:** 2026-03-15
**Decision:** Big Five scores are fixed BASE personality, but expression adapts per-relationship via a trust modifier (0.3-1.0). Trust grows from positive conversations (+0.05/+0.03/+0.02 based on quality) and decays from negative signals (-0.10). Permissions auto-derive from trust level with manual override capability.
**Rationale:** In real life, nobody is "70% open" to everyone. You're guarded with strangers and vulnerable with close friends. Trust-adaptive personality creates authentic, evolving relationships instead of static interactions. This mirrors how human relationships actually develop.
**Consequences:** Personality prompt must compute effective traits per-conversation using trust modifier. KNOWS edge in Neo4j gains trust, trust_history, and manual_permission_override fields. Permission system gains a trust-derived layer that auto-maps trust ranges to permission levels 0-5. Manual overrides always take precedence.

## ADR-014: Embedded Tutor During Live Conversations
**Date:** 2026-03-15
**Decision:** A Socratic tutor runs in a parallel WebSocket channel during live conversations. It operates in 4 modes: explain, check, reflect, and observe. Mode auto-selected based on Bloom level, with manual override. Standalone teach-back is kept for background conversation insights.
**Rationale:** Cognitive apprenticeship research shows 34% better retention when guidance is provided in-context rather than after the fact. Watching a debate without understanding is wasted potential. The embedded tutor transforms passive observation into active learning.
**Consequences:** Two WebSocket channels per live conversation (debate + tutor). Extra LLM call per agent turn for tutor generation. Frontend requires split-panel layout (60% debate, 40% tutor). Tutor channel is independent — network issues on one channel do not affect the other.

## ADR-015: Mock Agents + Social Connection Model
**Date:** 2026-03-15
**Decision:** 5 pre-built mock agents with diverse personalities auto-connect to every new user at trust=0.2. Real human connections are established via invite links + connection requests. All new relationships start at trust=0.2 (Stranger level).
**Rationale:** An empty graph is a dead product. New users need to see their agent on a living network immediately. Trust-based connection model mirrors how real human relationships develop — you don't grant full access to someone you just met.
**Consequences:** New connection_requests table in Postgres. Mock agents need periodic maintenance (personality updates, interest refresh). 5 extra KNOWS edges created per new user signup. Seed script must create mock agents with is_mock=true flag.
