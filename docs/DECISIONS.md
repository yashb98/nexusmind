# DECISIONS.md — Architecture Decision Log
# Append new decisions at bottom. Never edit existing entries.

## ADR-001: Four-Layer Engineering Model
**Date:** 2026-03-15
**Decision:** Build in explicit layers: Agentic → Process → Environment → Interface.
**Rationale:** Each layer produces qualitatively different intelligence. Agentic = agents exist. Process = agents think. Environment = system surprises. Interface = humans experience it. Skipping layers creates fragile systems. Sequential building ensures each layer's foundation is solid.
**Consequences:** Longer build time (7-9 weeks vs 4-5 for single-layer). But the result is genuinely emergent intelligence, not just a chatbot with extra steps.

## ADR-002: MLX Local Inference + QLoRA Fine-Tuning on Mac Studio
**Date:** 2026-03-15
**Decision:** All LLM inference and fine-tuning runs locally on Mac Studio M3 Ultra 96GB via Apple MLX framework. Cloud fallback via LiteLLM for reliability.
**Rationale:** 96GB unified memory fits Qwen 2.5 7B (4GB) + training gradients (8GB) + databases + OS with massive headroom. QLoRA on MLX takes ~25 min for 500 examples. Zero API cost. Silent 24/7 operation. Fine-tuning loop runs nightly without cloud dependency.
**Consequences:** ~2x slower than NVIDIA for training. Acceptable because training runs overnight when system is idle. No CUDA ecosystem access — use RunPod burst for SadTalker avatar rendering.

## ADR-003: Socratic State Machine (Not Free-Form Chat)
**Date:** 2026-03-15
**Decision:** Conversations follow a 6-phase state machine (OPEN → PROBE → DEEPEN → CHALLENGE → SYNTHESIZE → EXTRACT) rather than free-form chat.
**Rationale:** Free-form agent chat degrades to shallow pleasantries within 3-4 turns. Structured Socratic protocol forces depth. SocraticLM paper proves structured teaching outperforms GPT-4 by 12%. Phase progression ensures every conversation produces extractable knowledge.
**Consequences:** Conversations feel more structured than natural. Acceptable because the goal is knowledge creation, not socializing. Users see rich insights, not raw transcripts.

## ADR-004: Nightly Self-Improving LoRA Loop
**Date:** 2026-03-15
**Decision:** Run QLoRA fine-tuning every night on the day's best conversations, per personality archetype. Auto-deploy adapters that pass personality consistency evaluation.
**Rationale:** This creates a self-improving system — the environment engineering layer. Without it, agents stay static. With it, agents are measurably better every morning. Stanford's GenAgents proved personality replication works from conversation data. Our loop continuously feeds NEW conversation data back into the model.
**Consequences:** Requires careful evaluation (personality variance < 0.5) before deploying new adapters. Bad adapter = personality drift. Mitigation: always keep previous adapter as rollback.

## ADR-005: Bloom's Taxonomy for Teach-Back Difficulty
**Date:** 2026-03-15
**Decision:** Use Bloom's Taxonomy (6 levels) for adaptive difficulty in teach-back, not simple easy/medium/hard.
**Rationale:** Bloom's maps to real pedagogy. It distinguishes between "can recall a fact" (L1) and "can design a solution" (L6). This precision is what separates NexusMind from every other AI tutor that just adjusts word complexity.
**Consequences:** Requires LLM-as-judge to assess demonstrated Bloom level per interaction. Adds ~1s latency per assessment. Worth it for teaching quality.

## ADR-006: Monolith for Demo, Microservices for Scale
**Date:** 2026-03-15
**Decision:** All services in ONE FastAPI app for demo. Split into microservices when scaling requires it.
**Rationale:** Zero benefit from microservices at <100 users. Single process = simpler deployment, debugging, and testing. Clean service boundaries in code enable future split without refactor.
**Consequences:** Can't independently scale conversation engine vs graph queries. Acceptable until >1000 concurrent users.
