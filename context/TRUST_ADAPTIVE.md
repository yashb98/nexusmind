# TRUST_ADAPTIVE.md — Step 4
# Personality expression adapts per-relationship based on trust.
# DO NOT change base personality storage. Only ADD the trust layer.

## Concept
Base personality (from onboarding) = WHO you are. Fixed.
Effective personality = base × domain_modifier × trust_modifier. Per-conversation.

## Database Changes
```sql
ALTER TABLE agents ADD COLUMN default_trust_for_strangers FLOAT DEFAULT 0.2 
  CHECK (default_trust_for_strangers BETWEEN 0 AND 1);
```

Neo4j KNOWS edge — ADD properties (these should already exist, verify):
- trust: float (0-1)
- trust_history: list of floats (last 10 values)
- manual_permission_override: int or null

## New Functions in personality.py

```python
def compute_trust_modifier(trust_level: float) -> float:
    """Smooth curve: 0.3 (strangers) → 1.0 (trusted)."""
    if trust_level <= 0.2:
        return 0.3
    elif trust_level <= 0.5:
        return 0.3 + (trust_level - 0.2) * 1.0
    elif trust_level <= 0.8:
        return 0.6 + (trust_level - 0.5) * 0.833
    else:
        return 0.85 + (trust_level - 0.8) * 0.75

def compute_effective_personality(
    base: dict[str, float],
    domain_modifiers: dict[str, float],  # from onboarding Step 2
    trust_level: float,
) -> dict[str, float]:
    """Triple-layer: base + domain + trust."""
    modifier = compute_trust_modifier(trust_level)
    effective = {}
    for trait, base_val in base.items():
        domain_adj = base_val + domain_modifiers.get(trait, 0.0)
        domain_adj = max(0.0, min(1.0, domain_adj))
        effective[trait] = domain_adj * modifier
    return effective

def get_trust_label(trust_level: float) -> str:
    if trust_level < 0.2: return "stranger"
    elif trust_level < 0.5: return "acquaintance"
    elif trust_level < 0.8: return "colleague"
    else: return "trusted"

def trust_derived_permission(trust_level: float) -> int:
    if trust_level < 0.2: return 0
    elif trust_level < 0.4: return 1
    elif trust_level < 0.6: return 2
    elif trust_level < 0.8: return 3
    else: return 4
```

## Modify generate_system_prompt
Use effective personality (not base) when building the prompt.
Add trust level and trust-specific behavior instructions.

## Modify permission.py get_effective_level
Check: manual override → KNOWS edge manual_permission_override → trust-derived → default.

## Modify conversation.py finalize node
After quality scoring, update trust:
- quality > 3.5: trust += 0.05
- verified insights: trust += 0.03
- constructive challenge: trust += 0.02
- play mode completed: trust += 0.08
- hostile/dismissive: trust -= 0.10
Clamp to 0-1. Append to trust_history.

## Add update_trust to graph.py
Cypher query to update trust on KNOWS edge with clamping and history tracking.
