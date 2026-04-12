class DecisionEngine:
    def __init__(self):
        self.normal_threshold = 40
        self.urgent_threshold = 70
        self.alpha = 0.7  #LLM

        self.critical_keywords = {
            "attaque",
            "explosif",
            "sabotage",
            "ennemi",
            "intrusion"
        }

    def decide_from_text_mining(self, tm_result: dict):
        keywords = tm_result.get("keywords", [])
        score_tm = tm_result.get("score_tm", 0)

        if any(word in self.critical_keywords for word in keywords):
            return {
                "label": "CRITIQUE",
                "reason": "Mot sensible critique détecté",
                "score_tm": score_tm
            }

        if score_tm < self.normal_threshold:
            label = "NORMAL"
            reason = "Score faible, communication proche du corpus normal"
        elif score_tm < self.urgent_threshold:
            label = "URGENT"
            reason = "Score intermédiaire, communication potentiellement anormale"
        else:
            label = "CRITIQUE"
            reason = "Score élevé, communication fortement anormale"

        return {
            "label": label,
            "reason": reason,
            "score_tm": score_tm
        }

    def fuse_tm_llm(self, tm_result: dict, llm_result: dict):
        keywords = tm_result.get("keywords", [])
        score_tm = tm_result.get("score_tm", 0)
        score_llm = llm_result.get("score_llm", 0)
        justification_llm = llm_result.get("justification", "")
        label_llm = llm_result.get("label", "NORMAL")

        if any(word in self.critical_keywords for word in keywords):
            return {
                "label_final": "CRITIQUE",
                "score_final": 100,
                "reason_final": "Mot sensible critique détecté",
                "score_tm": score_tm,
                "score_llm": score_llm
            }

        if label_llm == "NORMAL":
            score_llm = min(score_llm, 40)
        elif label_llm == "URGENT":
            score_llm = max(40, min(score_llm, 70))
        else:
            score_llm = max(score_llm, 70)

        score_final = (self.alpha * score_llm) + ((1 - self.alpha) * score_tm)
        score_final = round(score_final, 2)

        if score_final < self.normal_threshold:
            label_final = "NORMAL"
        elif score_final < self.urgent_threshold:
            label_final = "URGENT"
        else:
            label_final = "CRITIQUE"

        return {
            "label_final": label_final,
            "score_final": score_final,
            "reason_final": justification_llm,
            "score_tm": score_tm,
            "score_llm": score_llm
        }