---
name: finetuning-pipeline
description: Work on LoRA/QLoRA fine-tuning, micro-adapters (hourly), full adapters (nightly), training data preparation, fact/pattern separation, adapter evaluation, MLX commands, or training/ directory
allowed-tools: Read, Bash, Grep, Glob, Edit, Write
---

# Skill: Fine-Tuning & Progressive Distillation

## When to use
Use this skill when working on LoRA/QLoRA training, adapter management, the nightly pipeline, hourly micro-adapters, or anything in `training/` or `src/services/finetune.py`.

## Progressive Distillation (4 tiers)

### Tier 1: Working Memory
- Lives in: LLM context window
- Content: current conversation + retrieved memories
- Speed: instant

### Tier 2: Episodic Memory
- Lives in: Qdrant + Neo4j
- Content: compacted conversations, entities, relations
- Speed: 50-200ms retrieval

### Tier 3: Micro-Adapters (HOURLY)
- Config: rank=4, 100 iters, batch_size=4
- Duration: 2-3 minutes per archetype
- Content: PATTERNS only (conversation style, personality expression)
- Hot-swapped via Redis pub/sub signal
- Logged to finetune_runs table (run_type='micro')

### Tier 4: Base Adapters (NIGHTLY)
- Config: rank=16, 500 iters, batch_size=4
- Duration: ~25 minutes per archetype
- Process: merge micro-adapters → train on day's best conversations → evaluate → deploy
- Logged to finetune_runs table (run_type='full')

## Fact/Pattern Separation (CRITICAL PRINCIPLE)
Facts → MEMORY (Qdrant/Neo4j). Patterns → WEIGHTS (LoRA).

**Strip from training data (facts):**
- Specific numbers, percentages, statistics
- Dates, timestamps
- Named entities (company names, product names, URLs)
- Prices, measurements
- Quoted claims with specific values

**Keep in training data (patterns):**
- Conversation style ("asks probing follow-up questions")
- Personality expression ("disagrees diplomatically")
- Socratic technique ("identifies unstated assumptions")
- Emotional patterns ("shows enthusiasm when discovering connections")

Rationale: Facts become stale. Skills don't. A model that memorized "40% reduction" will be wrong tomorrow. A model that learned "how to ask good questions" stays correct forever.

## Training Data Pipeline
```
1. Collect conversations (quality > threshold)
2. Filter: ONLY Verification Council ACCEPTED
3. Strip facts (regex + NER for numbers, dates, entities)
4. Group by personality archetype (6 groups)
5. Format as JSONL: {system_prompt, messages[]}
6. Split 90/10 train/val
```

## Evaluation Gate
Before deploying ANY new adapter:
1. Load new adapter
2. Run 10 test conversations (same agent, different partners/topics)
3. LLM-as-judge scores Big Five expression per conversation
4. Compute variance across all 10 for each dimension
5. PASS: variance < 0.5 on ALL 5 dimensions
6. Also check: does quality improve vs previous adapter?
7. If PASS: symlink to `./adapters/{archetype}_latest`
8. If FAIL: keep previous adapter, log failure

## Adapter Merge
Multiple micro-adapters merged via weighted average:
- Weight per adapter = average quality score during its training window
- W_merged = Σ(q_i × W_i) / Σ(q_i)

## MLX Commands (Mac Studio)
```bash
# Micro training
python -m mlx_lm.lora --model mlx-community/Qwen2.5-7B-Instruct-4bit \
  --data ./training/data/{archetype}_train.jsonl --train \
  --iters 100 --batch-size 4 --lora-layers 16 --lora-rank 4 \
  --adapter-path ./adapters/micro/{archetype}_{timestamp}

# Full training  
python -m mlx_lm.lora --model mlx-community/Qwen2.5-7B-Instruct-4bit \
  --data ./training/data/{archetype}_train.jsonl --train \
  --iters 500 --batch-size 4 --lora-layers 16 --lora-rank 16 \
  --adapter-path ./adapters/full/{archetype}_v{N}
```

## RunPod Alternative
Same process but on RunPod A10G serverless. Cost: ~£0.02 per micro run, ~£0.15 per full run.

## Rules
- NEVER train on unverified data (Verification Council ACCEPTED only)
- NEVER deploy adapter without evaluation passing
- ALWAYS keep previous adapter as rollback
- ALWAYS log run metrics to finetune_runs table
- Git tag every deployed adapter version
