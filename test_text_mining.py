from app.decision.engine import DecisionEngine

engine = DecisionEngine()

cases = [
    {"keywords": [], "score_tm": 20},
    {"keywords": [], "score_tm": 55},
    {"keywords": [], "score_tm": 85},
    {"keywords": ["attaque"], "score_tm": 45},
]

for case in cases:
    result = engine.decide_from_text_mining(case)
    print(case, "->", result)