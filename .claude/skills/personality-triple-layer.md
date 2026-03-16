---
name: personality-triple-layer
description: Work on personality scoring, onboarding scenarios, Big Five, trust-adaptive expression, domain-specific modifiers, prompt generation, archetype assignment, or src/services/personality.py and src/data/question_banks.py
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Personality (Triple-Layer) + Adaptive Onboarding

## When to use
Working on personality scoring, onboarding, trust modifiers, domain modifiers, prompt generation, or src/services/personality.py.

## Triple-Layer Personality System
```
effective_trait = (base_trait + domain_modifier) × trust_modifier
```
- **Base:** From onboarding (Big Five 0-1). Fixed unless user retakes quiz.
- **Domain:** Per-interest modifiers from domain-specific onboarding questions. Stored in agents.domain_modifiers JSONB.
- **Trust:** Per-relationship modifier (0.3 for strangers → 1.0 for trusted). Computed from KNOWS edge trust level.

## Adaptive Onboarding
NOT 10 fixed questions. Dynamic based on selected interests.
- Each interest has a bank of 5-8 scenario questions in src/data/question_banks.py
- Selection algorithm picks 2-3 per interest, ensuring all 5 dimensions covered ≥2x
- Total: 8-25 questions depending on interests selected
- Optional "Go Deeper": 3-5 LLM-generated follow-ups targeting answer inconsistencies
- Confidence score: 0.5 (5 questions) → 0.98 (25+ questions)

## Domain Modifiers
Computed from HOW answers differ per interest domain vs overall average.
Example: If user is more direct on AI questions but diplomatic on Philosophy questions → domain_modifiers = {"AI": {"agreeableness": -0.15}, "Philosophy": {"agreeableness": +0.1}}

## Trust Modifier Curve
```python
trust 0.0-0.2 → multiplier 0.3  (stranger: guarded)
trust 0.2-0.5 → multiplier 0.3-0.6 (acquaintance: warming up)
trust 0.5-0.8 → multiplier 0.6-0.85 (colleague: comfortable)
trust 0.8-1.0 → multiplier 0.85-1.0 (trusted: full expression)
```

## Auto-Derived Permissions
trust<0.2→Level 0, trust 0.2-0.4→Level 1, trust 0.4-0.6→Level 2, trust 0.6-0.8→Level 3, trust>0.8→Level 4-5. Manual overrides take precedence.

## Prompt Generation
generate_system_prompt() must: identify topic domain → apply domain modifiers → apply trust modifier → use EFFECTIVE values in prompt. Include trust label and trust-specific behavior instructions.

## 6 Archetypes
Investigator, Diplomat, Strategist, Innovator, Guardian, Catalyst. Each maps to a LoRA adapter.
