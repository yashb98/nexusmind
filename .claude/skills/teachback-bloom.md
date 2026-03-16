---
name: teachback-bloom
description: Work on teach-back, Bloom taxonomy assessment, embedded tutor during conversations, standalone teach-back sessions, avatar generation, Socratic tutoring, or src/services/teachback.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Teach-Back & Bloom's Taxonomy

## When to use
Working on teach-back, Bloom assessment, tutor modes, embedded tutor, or src/services/teachback.py.

## Two Modes

### Mode A: Embedded (during live conversations)
Runs in parallel WebSocket channel while user watches debate.
After each agent turn, tutor selects mode: explain/check/reflect/observe.
Does NOT block debate. Bloom updates during conversation.
Implementation: in ConversationService as parallel LangGraph node.

### Mode B: Standalone (from insights feed or Learn page)
User clicks "Teach me" on a past insight. Dedicated Q&A session.
POST /api/v1/teachback/start → session with first question.
Avatar generated asynchronously (text first, video follows).

## Bloom's Taxonomy (6 Levels)
1. Remember — recall facts. "What do you know about X?"
2. Understand — explain in own words. "Why does X matter?"
3. Apply — use in new situations. "How would you apply X to Y?"
4. Analyze — break into components. "What's the difference between X and Z?"
5. Evaluate — judge and critique. "What's the strongest argument against X?"
6. Create — design new solutions. "Design a system using X to solve Y."

## Socratic Rules (NEVER violate)
1. NEVER give direct answers. Guide through questions.
2. Wrong answer → DON'T say "wrong." Ask "What if we considered...?"
3. Right answer → acknowledge specifically, then increase difficulty.
4. 1-3 sentences per tutor turn. ONE question per turn.

## Bloom Assessment (DSPy Module)
Bloom level assessment uses a DSPy module for reliable classification.
Module: `src/dspy_modules/assessment.py → BloomAssessor`

Input: topic, tutor_question, learner_response, current_bloom_level
Output: demonstrated_level (1-6), confidence, reasoning, misconceptions

Called from TeachBackService and embedded tutor's handle_tutor_response().
Optimized on 20 labeled exchange→level examples.
Output validated: level clamped to 1-6, confidence to 0-1.

## Avatar Pipeline
Text → Edge TTS (free, <500ms) → SadTalker (RunPod T4, 3-5s) → video URL.
Text returns immediately. Avatar async. Frontend shows text, swaps in video when ready.

## Rules
- Only teach ACCEPTED or PROVISIONAL insights (not REJECTED)
- Bloom level persists across sessions
- Web search via SearXNG for current info during teaching
- Cache search results in knowledge_base collection
