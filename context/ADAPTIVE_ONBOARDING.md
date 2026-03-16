# ADAPTIVE_ONBOARDING.md — Step 2
# Dynamic question generation based on selected interests.
# DO NOT delete existing onboarding. EXTEND it.

## What Changes

### EXISTING (keep):
- 4-step flow: Basics → Interests → Scenarios → Privacy → Result
- Big Five scoring logic (accumulate deltas, normalize to 0-1)
- Archetype assignment
- Radar chart on result screen

### NEW (add):
- Interest-specific question banks (instead of 10 fixed questions)
- Dynamic question selection algorithm
- Domain-specific personality modifiers
- Confidence scoring
- Optional "Go Deeper" adaptive follow-ups
- Enhanced result screen with domain insights

---

## Database Changes

ADD these columns to the `agents` table (Alembic migration):
```sql
ALTER TABLE agents ADD COLUMN domain_modifiers JSONB DEFAULT '{}';
ALTER TABLE agents ADD COLUMN personality_confidence FLOAT DEFAULT 0.7;
ALTER TABLE agents ADD COLUMN questions_answered INT DEFAULT 0;
```

domain_modifiers stores per-interest personality adjustments:
```json
{
  "Artificial Intelligence": {"openness": 0.1, "agreeableness": -0.15},
  "Philosophy": {"openness": 0.05, "agreeableness": 0.1},
  "Finance": {"neuroticism": 0.1, "agreeableness": -0.05}
}
```

---

## New File: src/data/question_banks.py

This is the big content file. Each interest has 5-8 scenario questions.
Each question has 4 options. Each option maps to Big Five deltas.
Also includes 5 universal fallback questions (one per dimension).

### Structure:
```python
QUESTION_BANKS: dict[str, list[dict]] = {
    "Artificial Intelligence": [
        {
            "id": "ai_001",
            "scenario": "Your team's ML model gets 95% accuracy but you suspect dataset bias. The deadline is tomorrow. You...",
            "domain": "Artificial Intelligence",
            "options": [
                {"text": "Flag it immediately — accuracy means nothing if biased",
                 "scores": {"conscientiousness": 0.3, "openness": 0.2}},
                {"text": "Ship it now, document the concern, fix in v2",
                 "scores": {"conscientiousness": -0.2, "extraversion": 0.1}},
                {"text": "Quietly investigate the bias yourself tonight",
                 "scores": {"conscientiousness": 0.3, "extraversion": -0.2}},
                {"text": "Ask the team for opinions before deciding",
                 "scores": {"agreeableness": 0.2, "extraversion": 0.2}},
            ],
            "dimensions_tested": ["conscientiousness", "openness", "extraversion", "agreeableness"],
        },
        {
            "id": "ai_002",
            "scenario": "A colleague presents a new architecture that contradicts 3 months of your research. Their approach might be better. You...",
            "domain": "Artificial Intelligence",
            "options": [
                {"text": "Tear apart their logic in review — if it survives, it deserves to win",
                 "scores": {"agreeableness": -0.3, "openness": 0.2}},
                {"text": "Propose combining both approaches",
                 "scores": {"agreeableness": 0.2, "openness": 0.3}},
                {"text": "Defend your approach — 3 months of depth beats a new idea",
                 "scores": {"openness": -0.3, "agreeableness": -0.1}},
                {"text": "Privately test both and let the data decide",
                 "scores": {"conscientiousness": 0.3, "extraversion": -0.2}},
            ],
            "dimensions_tested": ["agreeableness", "openness", "conscientiousness"],
        },
        {
            "id": "ai_003",
            "scenario": "You're presenting your ML project. Someone asks a question that exposes a flaw you already knew about. You...",
            "domain": "Artificial Intelligence",
            "options": [
                {"text": "Acknowledge it openly — 'great catch, here's what I'm doing about it'",
                 "scores": {"openness": 0.2, "neuroticism": -0.2}},
                {"text": "Redirect — 'that's a known limitation, let me show you the strengths'",
                 "scores": {"extraversion": 0.2, "conscientiousness": 0.1}},
                {"text": "Feel embarrassed but explain your mitigation plan",
                 "scores": {"neuroticism": 0.2, "conscientiousness": 0.2}},
                {"text": "Challenge back — 'what alternative would you propose?'",
                 "scores": {"agreeableness": -0.2, "extraversion": 0.2}},
            ],
            "dimensions_tested": ["openness", "neuroticism", "extraversion", "agreeableness"],
        },
        # ... add 3-5 more AI questions
    ],
    
    "Philosophy": [
        {
            "id": "phil_001",
            "scenario": "In a debate about free will vs determinism, someone makes a point that genuinely shakes your position. You...",
            "domain": "Philosophy",
            "options": [
                {"text": "Acknowledge it openly — 'that's a good point, I need to rethink'",
                 "scores": {"openness": 0.3, "agreeableness": 0.2}},
                {"text": "Probe deeper — 'interesting, but what about the case of...'",
                 "scores": {"openness": 0.2, "agreeableness": -0.1}},
                {"text": "Table it — 'let me think about that and come back'",
                 "scores": {"conscientiousness": 0.2, "extraversion": -0.2}},
                {"text": "Redirect — 'that's a separate question, let's stay focused'",
                 "scores": {"openness": -0.2, "conscientiousness": 0.2}},
            ],
            "dimensions_tested": ["openness", "agreeableness", "conscientiousness"],
        },
        # ... add 4-7 more Philosophy questions
    ],
    
    "Computer Science": [...],
    "Psychology": [...],
    "Neuroscience": [...],
    "Physics": [...],
    "Mathematics": [...],
    "Economics": [...],
    "Finance": [...],
    "Biology": [...],
    "History": [...],
    "Literature": [...],
    "Political Science": [...],
    "Sociology": [...],
    "Chemistry": [...],
    "Astronomy": [...],
    "Linguistics": [...],
    "Environmental Science": [...],
    "Music Theory": [...],
    "Ethics": [...],
    "Cognitive Science": [...],
    
    # Universal fallbacks (one per Big Five dimension)
    "_universal": [
        {
            "id": "uni_ext",
            "scenario": "At a networking event, you typically...",
            "domain": "Universal",
            "options": [
                {"text": "Work the room, meet as many people as possible",
                 "scores": {"extraversion": 0.3}},
                {"text": "Find one or two people for deep conversation",
                 "scores": {"extraversion": -0.1, "openness": 0.2}},
                {"text": "Listen more than you talk, observe the group",
                 "scores": {"extraversion": -0.2, "conscientiousness": 0.1}},
                {"text": "Look for people who share your specific interests",
                 "scores": {"openness": 0.2, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["extraversion", "openness"],
        },
        # ... one for neuroticism, agreeableness, conscientiousness, openness
    ],
}
```

IMPORTANT: Each interest needs AT LEAST 5 questions. Generate the full banks
for ALL 21 interests listed above. Each question must:
- Have a realistic scenario from that domain
- Have 4 options mapping to different Big Five dimensions
- List which dimensions it tests
- Have an "id" in format "{domain_short}_{number}"

---

## Question Selection Algorithm

Add to src/services/personality.py (or new src/services/onboarding.py):

```python
import random

def select_questions(
    selected_interests: list[str],
    min_per_dimension: int = 2,
) -> list[dict]:
    """Select personalized questions ensuring all 5 dimensions covered."""
    
    dimension_count = {d: 0 for d in ["openness", "conscientiousness", 
                                       "extraversion", "agreeableness", "neuroticism"]}
    selected = []
    
    # Phase 1: Pick 2-3 questions per interest
    pick_per_interest = 3 if len(selected_interests) <= 4 else 2
    
    for interest in selected_interests:
        bank = QUESTION_BANKS.get(interest, [])
        if not bank:
            continue
        
        # Prioritize questions that fill dimension gaps
        def gap_score(q):
            return sum(1 for d in q["dimensions_tested"] 
                      if dimension_count[d] < min_per_dimension)
        
        sorted_bank = sorted(bank, key=gap_score, reverse=True)
        
        for q in sorted_bank[:pick_per_interest]:
            selected.append(q)
            for d in q["dimensions_tested"]:
                dimension_count[d] += 1
    
    # Phase 2: Fill gaps with universal questions
    for dim, count in dimension_count.items():
        if count < min_per_dimension:
            universals = [q for q in QUESTION_BANKS.get("_universal", [])
                         if dim in q["dimensions_tested"] and q not in selected]
            if universals:
                selected.append(universals[0])
                for d in universals[0]["dimensions_tested"]:
                    dimension_count[d] += 1
    
    random.shuffle(selected)
    return selected
```

---

## Domain Modifier Computation

After scoring, compute per-interest modifiers:

```python
def compute_domain_modifiers(
    answers: list[dict],  # {question_id, selected_option_index}
    questions: list[dict],  # the selected questions with domain info
    base_big_five: dict[str, float],
) -> dict[str, dict[str, float]]:
    """
    Compute how personality differs per domain vs the base.
    
    If user is more open in AI questions than overall → 
    domain_modifiers["AI"] = {"openness": +0.1}
    """
    # Group answers by domain
    domain_scores = defaultdict(lambda: defaultdict(list))
    
    for answer, question in zip(answers, questions):
        domain = question["domain"]
        if domain == "Universal":
            continue
        option = question["options"][answer["selected_option_index"]]
        for trait, delta in option["scores"].items():
            domain_scores[domain][trait].append(delta)
    
    # Compute average delta per domain per trait
    modifiers = {}
    for domain, traits in domain_scores.items():
        modifiers[domain] = {}
        for trait, deltas in traits.items():
            avg_delta = sum(deltas) / len(deltas)
            # Modifier = how this domain differs from base
            # Only store if significant (> 0.05 difference)
            if abs(avg_delta) > 0.05:
                modifiers[domain][trait] = round(avg_delta, 3)
    
    return modifiers
```

---

## Confidence Scoring

```python
def compute_confidence(questions_answered: int) -> float:
    """More questions = higher confidence in personality profile."""
    if questions_answered <= 5:
        return 0.5
    elif questions_answered <= 8:
        return 0.65
    elif questions_answered <= 12:
        return 0.78
    elif questions_answered <= 16:
        return 0.85
    elif questions_answered <= 20:
        return 0.92
    else:
        return min(0.98, 0.92 + (questions_answered - 20) * 0.003)
```

---

## Updated API Endpoints

KEEP existing: GET /onboarding/scenarios, POST /onboarding/personality

ADD:
```
GET  /api/v1/onboarding/questions?interests=AI,Philosophy,Finance
     → Returns dynamically selected questions based on interests

POST /api/v1/onboarding/personality
     → UPDATED: Now accepts {answers: [...], questions: [...]}
     → Returns: {big_five, archetype, description, domain_modifiers, confidence}

POST /api/v1/onboarding/go-deeper
     → Accepts: {current_answers: [...], current_scores: {...}}
     → Returns: 3-5 follow-up questions targeting inconsistencies
     → Uses LLM to generate contextual follow-ups
```

---

## Frontend Changes

### Step 2 (Interests) → ADD after selection:
Show: "We'll ask you {N} personalized questions based on your interests. ~{N/2} minutes."

### Step 3 (Scenarios) → MODIFY:
- Dynamic question count (not fixed 10)
- Domain tag on each question (small badge: "📊 AI/ML")
- Confidence bar that fills as user answers
- Progress: "4/12" instead of "4/10"

### NEW Step 3.5 (Go Deeper) → ADD between scenarios and privacy:
```
Your personality confidence is 82%.
Want to improve? We noticed:
• You challenge people in technical debates but seek consensus in abstract ones
• You're cautious with money but bold with ideas

[Go Deeper — 3 more questions]  [Skip — 82% is fine]
```
If clicked: show 3-5 LLM-generated adaptive questions.

### Step 5 (Result) → ENHANCE:
- Confidence percentage displayed
- Domain-specific insights section:
  "In AI contexts: More direct, challenge-oriented (openness +0.1, agreeableness -0.15)"
  "In Philosophy: More open, seeks understanding (openness +0.05, agreeableness +0.1)"
- Per-trait breakdown bars (not just radar chart)

---

## Integration with Personality Prompts

When building the personality prompt for a conversation, the system now does:

```python
# In personality.py generate_system_prompt():

# 1. Start with base Big Five
base = {"openness": agent.openness, ...}

# 2. Apply domain modifier (if conversation topic matches an interest)
topic_domain = classify_topic_to_domain(conversation_topic, agent.interests)
if topic_domain and topic_domain in agent.domain_modifiers:
    for trait, modifier in agent.domain_modifiers[topic_domain].items():
        base[trait] = clamp(base[trait] + modifier, 0.0, 1.0)

# 3. Apply trust modifier (per-relationship)
effective = {trait: val * compute_trust_modifier(trust_level) for trait, val in base.items()}

# Result: triple-layered personality (base × domain × trust)
```

This is the TRIPLE-LAYER system: base personality × domain context × relationship trust.
No other AI personality system does this.
