# NexusMind Scratchpad
> Claude: Update this file as you work. This persists across sessions.

## Current State
- Migration: ALL 8 STEPS COMPLETE
- Last session: 2026-03-16
- Branch: main

## Migration Steps — ALL DONE
1. ~~Fix critical bugs~~ DONE
2. ~~Adaptive onboarding~~ DONE
3. ~~Conversation modes~~ DONE
4. ~~Trust-adaptive personality~~ DONE
5. ~~Embedded tutor~~ DONE
6. ~~Profile section~~ DONE
7. ~~Social layer~~ DONE
8. ~~Mock agents + connections~~ DONE

## Tests
- 123 tests passing (all unit + integration)

## Key Architecture
- Triple-layer personality: base × domain × trust
- 8 conversation modes: casual, socratic, brainstorm, teach, research, play, project, reflection
- Embedded tutor: generates commentary after each debate turn (non-background)
- 5 mock agents auto-connect to new users with domain_modifiers + taglines
- Social layer: groups, events, feed, discovery
- DSPy modules: verification council, knowledge extraction, Bloom assessment, quality scoring
- Navigation: Home, Network, Groups, Events, Learn, Profile

## Discoveries
- Kimi API (moonshot.cn) for LLM — key in .env as KIMI_API_KEY
- Mock agents seeded on DB migration (5 agents: Aria, Marcus, Priya, James, Luna)
- Question banks: 110 questions across 21 domains + 5 universal
- Feed items created as side effects by various services
