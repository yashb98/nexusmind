# LAYERS.md — NexusMind Five-Layer Engineering Model

## Why Layers Matter
Each layer produces a qualitatively DIFFERENT type of intelligence. You cannot skip layers — each depends on the one below it. The fifth layer (Evolution) is what transforms NexusMind from a product into a living system.

## Layer 1: Agentic Engineering (Phases 1-2)
**Question:** "How are agents structured?"
**What you build:** Agent CRUD, Big Five personality profiles, 4-step scenario-based onboarding, Neo4j social graph, 6-level permission system with audit, PersonalityService that converts Big Five → behavioral system prompts, archetype assignment.
**What it produces:** Agents that EXIST on a graph with distinct personalities.
**Test:** "Can I create 10 agents with different personalities and see them on a graph with edges?"
**This layer alone = interesting but lifeless. Agents exist but don't think.**

## Layer 2: Process Engineering (Phase 3)
**Question:** "How do agents think and learn?"
**What you build:** LangGraph Socratic state machine (6 phases), optimized internal routing (parallel I/O via asyncio.gather, fire-and-forget graph updates), memory retrieval with permission filtering, personality injection, knowledge extraction with GraphRAG entity/relation extraction, conversation quality scoring.
**What it produces:** Agents that have MEANINGFUL conversations producing KNOWLEDGE.
**Test:** "Can two agents have a 10-turn Socratic debate where Agent A challenges Agent B's assumptions, and the system extracts 2-3 insights with entity-relation triples?"
**This layer = dynamic but unchecked. Agents think, but the system doesn't verify.**

## Layer 3: Environment Engineering (Phase 4)
**Question:** "How does the system ensure quality and enable emergence?"
**What you build:** 3-tier memory architecture (hot + graph + cold) with lifecycle management, Verification Council (Skeptic + Connector + Judge), community detection (Leiden algorithm), teach-back system (Bloom-adapted Socratic tutoring), trending topics, recommendation engine, avatar pipeline (Edge TTS + SadTalker).
**What it produces:** Verified knowledge. Emergent communities. Users who learn from their agents.
**Test:** "After 100 conversations, did ≥ 2 communities form organically? Did the Verification Council catch at least 1 low-quality claim? Did a user's Bloom level increase through teach-back?"
**This layer = emergent + verified. Intelligence emerges AND is checked.**

## Layer 4: Evolution Engineering (Phase 5)
**Question:** "How does the system improve itself?"
**What you build:** Always-on background agent scheduler (EXPLORE/RESEARCH/REFINE), progressive model distillation (hourly micro-adapters + nightly full adapters), research scout (weekly arXiv/paper search), code improvement agent (weekly, human-approved PRs), metric monitoring per function.
**What it produces:** A system that gets smarter every hour without human intervention.
**Test:** "After 1 week, are conversation quality scores higher than Day 1? Has the research scout found ≥ 1 relevant paper? Has the code agent proposed ≥ 1 improvement?"
**This layer = self-improving. The system improves the system that improves the system.**

## Layer 5: Interface Engineering (Phase 6)
**Question:** "How do humans experience the intelligence?"
**What you build:** D3.js graph with community hulls, conversation viewer with Socratic phase indicators, insights feed with verification badges, teach-back panel with avatar video, privacy dashboard, evolution dashboard (proposals, fine-tune history), personality onboarding flow.
**What it produces:** A WOW demo. Users SEE the emergent behavior and self-improvement.
**Test:** "Can a stranger watch a 3-minute demo and understand: agents debate, communities emerge, knowledge is verified, they can be taught by an avatar, and the system improves itself?"

## How Layers Connect

```
User creates agent → [Layer 1: Agentic]
                          │
Agent has conversations → [Layer 2: Process]
                          │
Knowledge verified + communities emerge → [Layer 3: Environment]
                          │
System improves itself autonomously → [Layer 4: Evolution]
                          │
Humans see and learn from it all → [Layer 5: Interface]
                          │
User learns → informs agent → better conversations → richer patterns
    │
    └──→ Fine-tuning improves agents → better conversations
    └──→ Research scout finds better methods → better system
    └──→ Code agent proposes optimizations → better performance
         (Triple feedback loop — knowledge, model, and code all improve)
```

## The Self-Improving Loop (Most Important Concept)

```
DAY 1: 10 agents, 50 background conversations (quality 3.2/5)
         ↓
HOUR 1-24: Micro-adapters trained 24 times. Patterns absorbed.
         ↓
NIGHT 1: Full adapter merge. Personality consistency evaluated.
         ↓
DAY 2: 60 conversations (quality 3.5/5). Verification Council catches 3 bad claims.
         ↓
DAY 3: 2 communities detected. Trending topic: "edge inference."
         ↓
WEEK 1: Quality 4.1/5. 5 communities. Research scout finds LoRA-Flow paper.
         Code agent proposes HyDE for memory retrieval (15% improvement).
         Users report learning things they wouldn't have found alone.
         ↓
WEEK 2: Quality 4.3/5. System is measurably smarter than Week 1.
         Nobody programmed this improvement. It emerged.
```
