"""Domain-specific question banks for adaptive onboarding.

Each interest maps to a list of scenario questions with domain-specific framing.
The '_universal' key contains fallback questions for dimension coverage gaps.
"""

QUESTION_BANKS: dict[str, list[dict]] = {
    "AI": [
        {
            "id": "ai_1",
            "scenario": "A new AI model produces impressive results but its internals are opaque. You...",
            "domain": "AI",
            "options": [
                {"text": "Dive into interpretability research to understand it", "scores": {"openness": 0.3, "conscientiousness": 0.2}},
                {"text": "Use it pragmatically — results matter more than understanding", "scores": {"conscientiousness": -0.1, "openness": -0.2}},
                {"text": "Discuss ethical implications with peers first", "scores": {"agreeableness": 0.2, "extraversion": 0.1}},
                {"text": "Wait for the community to vet it before engaging", "scores": {"neuroticism": 0.2, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["openness", "conscientiousness"],
        },
        {
            "id": "ai_2",
            "scenario": "You're building an AI system and discover a bias in the training data. You...",
            "domain": "AI",
            "options": [
                {"text": "Stop everything and fix the data before proceeding", "scores": {"conscientiousness": 0.3, "neuroticism": 0.1}},
                {"text": "Document it and propose a creative mitigation strategy", "scores": {"openness": 0.2, "conscientiousness": 0.1}},
                {"text": "Raise it with the team and decide together", "scores": {"agreeableness": 0.3, "extraversion": 0.1}},
                {"text": "Ship it with a disclaimer — perfection is the enemy of progress", "scores": {"conscientiousness": -0.3, "openness": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "agreeableness"],
        },
        {
            "id": "ai_3",
            "scenario": "An AI colleague suggests an unconventional architecture nobody has tried. You...",
            "domain": "AI",
            "options": [
                {"text": "Get excited and prototype it immediately", "scores": {"openness": 0.3, "extraversion": 0.1}},
                {"text": "Research the theoretical foundations first", "scores": {"conscientiousness": 0.2, "openness": 0.1}},
                {"text": "Poll the team for opinions before investing time", "scores": {"agreeableness": 0.2, "extraversion": 0.2}},
                {"text": "Stick with proven approaches — too risky", "scores": {"openness": -0.3, "neuroticism": 0.2}},
            ],
            "dimensions_tested": ["openness", "extraversion"],
        },
    ],
    "science": [
        {
            "id": "sci_1",
            "scenario": "A respected journal publishes findings that contradict your research. You...",
            "domain": "Science",
            "options": [
                {"text": "Replicate their experiment to verify independently", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
                {"text": "Reach out to the authors for a collaborative discussion", "scores": {"agreeableness": 0.2, "extraversion": 0.2}},
                {"text": "Publish a response challenging their methodology", "scores": {"extraversion": 0.2, "agreeableness": -0.2}},
                {"text": "Re-examine your own assumptions first", "scores": {"openness": 0.3, "neuroticism": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "openness"],
        },
        {
            "id": "sci_2",
            "scenario": "You have limited funding and must choose between a safe experiment and a risky breakthrough attempt. You...",
            "domain": "Science",
            "options": [
                {"text": "Go for the breakthrough — science needs bold moves", "scores": {"openness": 0.3, "neuroticism": -0.2}},
                {"text": "Choose the safe route — reliable results build careers", "scores": {"conscientiousness": 0.2, "neuroticism": 0.2}},
                {"text": "Split the budget and try both at smaller scale", "scores": {"conscientiousness": 0.1, "openness": 0.1}},
                {"text": "Ask mentors and colleagues what they'd recommend", "scores": {"agreeableness": 0.2, "extraversion": 0.1}},
            ],
            "dimensions_tested": ["openness", "neuroticism"],
        },
        {
            "id": "sci_3",
            "scenario": "A junior researcher presents a flawed but creative hypothesis. You...",
            "domain": "Science",
            "options": [
                {"text": "Point out the flaws directly so they can improve", "scores": {"agreeableness": -0.2, "conscientiousness": 0.2}},
                {"text": "Encourage the creativity and gently guide corrections", "scores": {"agreeableness": 0.3, "openness": 0.1}},
                {"text": "Help them design an experiment to test it properly", "scores": {"conscientiousness": 0.2, "agreeableness": 0.1}},
                {"text": "Let them figure it out — struggling builds resilience", "scores": {"agreeableness": -0.1, "neuroticism": -0.1}},
            ],
            "dimensions_tested": ["agreeableness", "conscientiousness"],
        },
    ],
    "philosophy": [
        {
            "id": "phil_1",
            "scenario": "In a debate about free will, you find yourself uncertain. You...",
            "domain": "Philosophy",
            "options": [
                {"text": "Embrace the uncertainty — it's where growth happens", "scores": {"openness": 0.3, "neuroticism": -0.1}},
                {"text": "Research all major positions before forming an opinion", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
                {"text": "Engage others in dialogue to sharpen your thinking", "scores": {"extraversion": 0.2, "openness": 0.1}},
                {"text": "Feel anxious about not having a clear answer", "scores": {"neuroticism": 0.3, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["openness", "neuroticism"],
        },
        {
            "id": "phil_2",
            "scenario": "Someone argues morality is purely subjective. You...",
            "domain": "Philosophy",
            "options": [
                {"text": "Challenge them with counter-examples and logical arguments", "scores": {"extraversion": 0.2, "agreeableness": -0.2}},
                {"text": "Explore their reasoning with genuine curiosity", "scores": {"openness": 0.3, "agreeableness": 0.1}},
                {"text": "Share your own moral framework and see where you overlap", "scores": {"agreeableness": 0.2, "extraversion": 0.1}},
                {"text": "Agree to disagree — some questions have no resolution", "scores": {"agreeableness": 0.1, "openness": -0.2}},
            ],
            "dimensions_tested": ["extraversion", "agreeableness"],
        },
        {
            "id": "phil_3",
            "scenario": "You discover a logical contradiction in your own deeply held belief. You...",
            "domain": "Philosophy",
            "options": [
                {"text": "Revise your belief immediately — consistency matters", "scores": {"conscientiousness": 0.3, "openness": 0.2}},
                {"text": "Sit with the discomfort and reflect deeply over time", "scores": {"openness": 0.2, "neuroticism": 0.1}},
                {"text": "Discuss it with others to get diverse perspectives", "scores": {"extraversion": 0.2, "agreeableness": 0.1}},
                {"text": "Defend your original position — logic isn't everything", "scores": {"openness": -0.3, "conscientiousness": -0.1}},
            ],
            "dimensions_tested": ["openness", "conscientiousness"],
        },
    ],
    "technology": [
        {
            "id": "tech_1",
            "scenario": "A new framework gains massive hype but you're productive with your current stack. You...",
            "domain": "Technology",
            "options": [
                {"text": "Try it on a side project to evaluate it yourself", "scores": {"openness": 0.3, "conscientiousness": 0.1}},
                {"text": "Stick with what works — hype cycles are unreliable", "scores": {"conscientiousness": 0.2, "openness": -0.2}},
                {"text": "Ask the community about real-world experiences", "scores": {"extraversion": 0.2, "agreeableness": 0.1}},
                {"text": "Feel pressure to switch — falling behind worries you", "scores": {"neuroticism": 0.3, "openness": 0.1}},
            ],
            "dimensions_tested": ["openness", "neuroticism"],
        },
        {
            "id": "tech_2",
            "scenario": "Your code review reveals a colleague's approach is functional but inelegant. You...",
            "domain": "Technology",
            "options": [
                {"text": "Approve it — it works and shipping matters", "scores": {"agreeableness": 0.2, "conscientiousness": -0.1}},
                {"text": "Suggest specific improvements with clear reasoning", "scores": {"conscientiousness": 0.3, "agreeableness": 0.1}},
                {"text": "Rewrite it yourself to demonstrate a better approach", "scores": {"extraversion": 0.1, "agreeableness": -0.2}},
                {"text": "Have a conversation about coding standards for the team", "scores": {"extraversion": 0.2, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "agreeableness"],
        },
        {
            "id": "tech_3",
            "scenario": "You're architecting a system and face a tradeoff between simplicity and future-proofing. You...",
            "domain": "Technology",
            "options": [
                {"text": "Keep it simple — YAGNI principle", "scores": {"conscientiousness": 0.1, "openness": -0.1}},
                {"text": "Build for flexibility — anticipate future needs", "scores": {"openness": 0.2, "conscientiousness": 0.2}},
                {"text": "Prototype both approaches and benchmark", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
                {"text": "Ask stakeholders what they'd prefer", "scores": {"agreeableness": 0.2, "extraversion": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "openness"],
        },
    ],
    "art": [
        {
            "id": "art_1",
            "scenario": "You see an art piece that most people dismiss but you find compelling. You...",
            "domain": "Art",
            "options": [
                {"text": "Defend it publicly and explain what you see in it", "scores": {"extraversion": 0.3, "openness": 0.2}},
                {"text": "Appreciate it quietly — art is personal", "scores": {"extraversion": -0.2, "openness": 0.2}},
                {"text": "Research the artist's intent and context", "scores": {"conscientiousness": 0.2, "openness": 0.1}},
                {"text": "Question your own taste — maybe you're wrong", "scores": {"neuroticism": 0.2, "agreeableness": 0.1}},
            ],
            "dimensions_tested": ["extraversion", "openness"],
        },
        {
            "id": "art_2",
            "scenario": "You're creating something and hit a creative block. You...",
            "domain": "Art",
            "options": [
                {"text": "Push through with discipline — inspiration follows work", "scores": {"conscientiousness": 0.3, "neuroticism": -0.1}},
                {"text": "Step away and seek new experiences for inspiration", "scores": {"openness": 0.3, "extraversion": 0.1}},
                {"text": "Collaborate with someone to spark new ideas", "scores": {"extraversion": 0.2, "agreeableness": 0.2}},
                {"text": "Feel frustrated and anxious about the block", "scores": {"neuroticism": 0.3, "conscientiousness": -0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "neuroticism"],
        },
        {
            "id": "art_3",
            "scenario": "Someone criticizes your creative work harshly. You...",
            "domain": "Art",
            "options": [
                {"text": "Use it as fuel — criticism sharpens your work", "scores": {"neuroticism": -0.2, "openness": 0.2}},
                {"text": "Seek constructive feedback from trusted peers instead", "scores": {"agreeableness": 0.2, "conscientiousness": 0.1}},
                {"text": "Engage the critic in dialogue about their perspective", "scores": {"extraversion": 0.2, "openness": 0.1}},
                {"text": "Take it personally — it's hard not to", "scores": {"neuroticism": 0.3, "agreeableness": 0.1}},
            ],
            "dimensions_tested": ["neuroticism", "agreeableness"],
        },
    ],
    "business": [
        {
            "id": "biz_1",
            "scenario": "Your startup idea gets negative feedback from a respected mentor. You...",
            "domain": "Business",
            "options": [
                {"text": "Pivot based on their feedback — they have experience", "scores": {"agreeableness": 0.2, "conscientiousness": 0.1}},
                {"text": "Trust your vision — many great ideas were initially rejected", "scores": {"openness": 0.2, "neuroticism": -0.2}},
                {"text": "Gather more data points before deciding", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
                {"text": "Feel discouraged but push through anyway", "scores": {"neuroticism": 0.2, "extraversion": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness", "neuroticism"],
        },
        {
            "id": "biz_2",
            "scenario": "Two team members have a conflict about project direction. You...",
            "domain": "Business",
            "options": [
                {"text": "Mediate and help them find common ground", "scores": {"agreeableness": 0.3, "extraversion": 0.1}},
                {"text": "Make the decision yourself to avoid wasting time", "scores": {"extraversion": 0.2, "agreeableness": -0.2}},
                {"text": "Let them work it out — conflict can be productive", "scores": {"openness": 0.1, "agreeableness": -0.1}},
                {"text": "Set up a structured evaluation framework for both approaches", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
            ],
            "dimensions_tested": ["agreeableness", "extraversion"],
        },
        {
            "id": "biz_3",
            "scenario": "You discover a competitor has launched a similar product. You...",
            "domain": "Business",
            "options": [
                {"text": "Differentiate aggressively — find your unique angle", "scores": {"openness": 0.3, "extraversion": 0.1}},
                {"text": "Analyze their product methodically to find weaknesses", "scores": {"conscientiousness": 0.3, "openness": 0.1}},
                {"text": "Talk to customers to understand what they actually need", "scores": {"agreeableness": 0.2, "extraversion": 0.2}},
                {"text": "Panic briefly, then refocus on execution", "scores": {"neuroticism": 0.2, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["openness", "conscientiousness"],
        },
    ],
    "_universal": [
        {
            "id": "uni_open_1",
            "scenario": "You encounter an idea that completely challenges your worldview. You...",
            "domain": "Universal",
            "options": [
                {"text": "Explore it deeply — this is how you grow", "scores": {"openness": 0.3}},
                {"text": "Evaluate it against evidence before engaging", "scores": {"conscientiousness": 0.2, "openness": 0.1}},
                {"text": "Discuss it with others to get perspective", "scores": {"extraversion": 0.2, "agreeableness": 0.1}},
                {"text": "Dismiss it — your current framework works fine", "scores": {"openness": -0.3}},
            ],
            "dimensions_tested": ["openness"],
        },
        {
            "id": "uni_con_1",
            "scenario": "You have a big deadline approaching and realize you underestimated the work. You...",
            "domain": "Universal",
            "options": [
                {"text": "Create a detailed plan and work systematically", "scores": {"conscientiousness": 0.3}},
                {"text": "Wing it — your best work comes under pressure", "scores": {"conscientiousness": -0.2, "neuroticism": -0.1}},
                {"text": "Ask for help and delegate what you can", "scores": {"extraversion": 0.2, "agreeableness": 0.1}},
                {"text": "Stress out but push through somehow", "scores": {"neuroticism": 0.3, "conscientiousness": 0.1}},
            ],
            "dimensions_tested": ["conscientiousness"],
        },
        {
            "id": "uni_ext_1",
            "scenario": "You arrive at a conference where you don't know anyone. You...",
            "domain": "Universal",
            "options": [
                {"text": "Introduce yourself to the first person you see", "scores": {"extraversion": 0.3}},
                {"text": "Find a quiet corner and observe first", "scores": {"extraversion": -0.2, "neuroticism": 0.1}},
                {"text": "Look for someone who seems approachable and start there", "scores": {"agreeableness": 0.2, "extraversion": 0.1}},
                {"text": "Check the schedule and plan your sessions methodically", "scores": {"conscientiousness": 0.2, "extraversion": -0.1}},
            ],
            "dimensions_tested": ["extraversion"],
        },
        {
            "id": "uni_agr_1",
            "scenario": "A friend asks for honest feedback on their work, which you think is mediocre. You...",
            "domain": "Universal",
            "options": [
                {"text": "Be honest but kind — they asked for it", "scores": {"agreeableness": 0.2, "conscientiousness": 0.1}},
                {"text": "Focus on the positives and downplay the negatives", "scores": {"agreeableness": 0.3}},
                {"text": "Give blunt, direct feedback — honesty is respect", "scores": {"agreeableness": -0.3, "extraversion": 0.1}},
                {"text": "Avoid giving feedback — suggest they ask someone else", "scores": {"neuroticism": 0.2, "extraversion": -0.2}},
            ],
            "dimensions_tested": ["agreeableness"],
        },
        {
            "id": "uni_neu_1",
            "scenario": "Something you worked hard on fails publicly. You...",
            "domain": "Universal",
            "options": [
                {"text": "Analyze what went wrong and extract lessons", "scores": {"conscientiousness": 0.2, "neuroticism": -0.2}},
                {"text": "Feel deeply affected but eventually bounce back", "scores": {"neuroticism": 0.2}},
                {"text": "Shrug it off — failure is part of the process", "scores": {"neuroticism": -0.3, "openness": 0.1}},
                {"text": "Replay it in your mind and worry about what others think", "scores": {"neuroticism": 0.3, "extraversion": -0.1}},
            ],
            "dimensions_tested": ["neuroticism"],
        },
    ],
}
