---
name: dspy-modules
description: Build and optimize DSPy modules for structured LLM outputs. Used for Verification Council (Skeptic/Connector/Judge), knowledge extraction (insights + GraphRAG entities), Bloom level assessment, and conversation quality scoring. NOT for personality prompts, conversations, or tutor.
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: DSPy Modules (Structured LLM Optimization)

## When to use
Working on Verification Council, knowledge extraction, Bloom assessment, quality scoring, or any LLM call that needs STRUCTURED, RELIABLE output (scores, classifications, entity lists). NOT for creative/conversational LLM calls.

## Where DSPy is Used (ONLY these 4 places)
1. **Verification Council** — Skeptic, Connector, Judge modules (structured decisions)
2. **Knowledge Extraction** — InsightExtractor, EntityRelationExtractor (structured entities)
3. **Bloom Assessment** — BloomAssessor (classification: level 1-6)
4. **Quality Scoring** — QualityJudge (calibrated multi-dimensional scoring)

## Where DSPy is NOT Used (keep hand-written prompts)
- Agent personality prompts (creative, context-dependent, triple-layer)
- Embedded tutor commentary (natural, conversational)
- Conversation generation (dynamic, personality-driven)
- Background scheduler logic (Python code, no LLM)
- Fine-tuning pipeline (data processing, no LLM prompting)

## Directory Structure
```
src/
├── dspy_modules/
│   ├── __init__.py
│   ├── verification.py      # Skeptic, Connector, Judge modules
│   ├── extraction.py        # InsightExtractor, EntityRelationExtractor
│   ├── assessment.py        # BloomAssessor, QualityJudge
│   ├── optimizers.py        # One-time optimization scripts per module
│   └── data/                # Labeled examples (20 per module)
│       ├── verification_examples.json
│       ├── extraction_examples.json
│       ├── bloom_examples.json
│       └── quality_examples.json
```

## Module Pattern
```python
import dspy

class SkepticModule(dspy.Module):
    def __init__(self):
        self.evaluate = dspy.ChainOfThought(
            "claim, source, counter_evidence, contradictions "
            "-> reliability_score: float, reasoning: str, is_reliable: bool"
        )

    def forward(self, claim, source, counter_evidence, contradictions):
        return self.evaluate(
            claim=claim, source=source,
            counter_evidence=counter_evidence,
            contradictions=contradictions,
        )
```

## Integration Pattern
DSPy modules REPLACE raw LLM calls inside services. Service interfaces do NOT change.
```python
# In verification.py:
# BEFORE: response = await self.llm.generate(SKEPTIC_PROMPT.format(...))
# AFTER:  result = self.skeptic_module(claim=..., source=..., ...)
# SkepticResult return type stays identical.
```

## Optimization (one-time per module, ~10 min each)
```python
from dspy.teleprompt import BootstrapFewShot

# Load 20 labeled examples
# Define metric (is output correct?)
# optimizer.compile(module, trainset=examples)
# Save optimized module to src/dspy_modules/optimized/
```

## LLM Configuration for DSPy
```python
import dspy

lm = dspy.LM(
    model="openai/Qwen/Qwen2.5-7B-Instruct",
    api_base="https://api.runpod.ai/v2/{ENDPOINT_ID}/openai/v1",
    api_key=RUNPOD_API_KEY,
    max_tokens=1024,
    temperature=0.3,
)
dspy.configure(lm=lm)
```

## Labeled Examples Format
```json
[
    {
        "input_field_1": "value",
        "input_field_2": "value",
        "expected_output_field": "value"
    }
]
```
Each module needs ~20 labeled examples. Quality matters more than quantity.

## Rules
- DSPy modules live ONLY in src/dspy_modules/ — never inline in services
- Service interfaces NEVER change when adding DSPy — it's an internal swap
- ALWAYS validate DSPy output (clamp scores to 0-1, verify enums, check types)
- Temperature 0.3 for DSPy (structured output needs determinism), 0.7 for conversations
- Re-optimize when switching LLM models
- Langfuse tracing still required — wrap DSPy calls in trace
- Labeled examples are precious — version control them, review carefully
