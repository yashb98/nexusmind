---
name: conversation-engine
description: Build and modify conversation logic, LangGraph state machines, 8 conversation modes (casual/socratic/brainstorm/teach/research/play/project/reflection), token streaming via WebSocket, multi-agent dynamic turn order, or src/services/conversation.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Conversation Engine (8 Modes + Streaming + Multi-Agent)

## When to use
Working on any conversation logic, LangGraph state machines, streaming, modes, turn order, or src/services/conversation.py.

## 8 Conversation Modes
1. **CASUAL** — Natural chat, no structure. Builds trust. No phase progression.
2. **SOCRATIC** — Structured 6-phase debate (OPEN→PROBE→DEEPEN→CHALLENGE→SYNTHESIZE→EXTRACT).
3. **BRAINSTORM** — "Yes, and..." collaborative idea generation. Never dismiss.
4. **TEACH** — One agent explains, other asks questions. Knowledge transfer.
5. **RESEARCH** — Divide topic, investigate independently, share findings.
6. **PLAY** — Games (20 questions, dilemmas, what-if). Builds trust fast (+0.08).
7. **PROJECT** — Goal-oriented. Plan, work, review, deliver. For hackathons.
8. **REFLECTION** — Think out loud with a listener. Process experiences.

## Mode Selection
User picks explicitly OR auto-selected: trust < 0.3 → casual/play. Trust 0.3-0.6 → casual/teach/brainstorm. Trust > 0.6 → any mode. Contradiction detected → socratic. New knowledge → teach.

## Two State Machines
- **1:1 conversations** (2 agents): Existing LangGraph graph with alternating turns.
- **Group conversations** (3+ agents): New GroupConversationGraph with dynamic turn order.

## Dynamic Turn Order (Groups)
NOT round-robin. Agent with highest response_urgency speaks next:
```
urgency = relevance_to_interests * 0.3 + disagreement_with_last * 0.3 + 
          new_info_to_add * 0.2 + extraversion * 0.1 + random * 0.1
```
Same agent cannot speak twice consecutively. Low-E agents speak less (realistic).

## Streaming (CRITICAL — all user-facing conversations)
Backend streams tokens via WebSocket. Frontend renders token-by-token.
```
Server sends: {type: "turn_start", speaker, turn, phase, mode}
              {type: "token", content: "word"}  (repeated)
              {type: "turn_end", speaker, turn, full_content}
```
Background conversations: stream=False (no WebSocket, collect full response).

## Performance
- Parallel I/O: asyncio.gather(memory, graph, permission) — never sequential
- Fire-and-forget: graph/memory updates don't block response
- Target: ~2-3s per turn (LLM time only)

## Trust Updates (finalize node)
After each conversation: quality>3.5→+0.05, verified insights→+0.03, constructive challenge→+0.02, play completed→+0.08, hostile→-0.10. Clamp 0-1.

## Embedded Tutor (non-background only)
After each agent turn, tutor generates commentary in parallel WebSocket channel. Modes: explain/check/reflect/observe. Does NOT block debate.
