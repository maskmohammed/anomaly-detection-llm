import json
import requests


class LLMClassifier:
    def __init__(self, model_name="tinyllama", base_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.base_url = base_url

    def build_prompt(self, text: str) -> str:
        return f"""
    You are a strict security classifier.

    Classify the following message into exactly one label:
    NORMAL, URGENT, or CRITIQUE.

    Rules:
    - NORMAL: greeting, neutral, no threat
    - URGENT: problem, anomaly, unusual situation
    - CRITIQUE: attack, intrusion, sabotage, immediate danger

    Score rules:
    - NORMAL → 0–39
    - URGENT → 40–69
    - CRITIQUE → 70–100

    Return ONLY valid JSON. No explanation outside JSON.

    Format:
    {{"label":"NORMAL|URGENT|CRITIQUE","score_llm":number,"justification":"short sentence"}}

    Examples:

    Input: bonjour je mappelle mohamed
    Output: {{"label":"NORMAL","score_llm":15,"justification":"Neutral greeting message."}}

    Input: urgence dans le secteur
    Output: {{"label":"URGENT","score_llm":55,"justification":"Indicates an urgent situation."}}

    Input: attaque dans la zone
    Output: {{"label":"CRITIQUE","score_llm":90,"justification":"Contains a severe threat keyword."}}

    Now classify:
    {text}
    """.strip()

    def _normalize_score(self, label: str, score: int) -> int:
        if label == "NORMAL":
            return max(0, min(score, 39))
        if label == "URGENT":
            return max(40, min(score, 69))
        return max(70, min(score, 100))

    def classify(self, text: str):
        if not text or not text.strip():
            return {
                "label": "NORMAL",
                "score_llm": 0,
                "justification": "Message vide",
                "raw_output": ""
            }

        prompt = self.build_prompt(text)

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0
            }
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=300)
            response.raise_for_status()
            data = response.json()
            

            raw_output = data.get("response", "").strip()
            try:
                parsed = json.loads(raw_output)
            except:
                return {
                    "label": "NORMAL",
                    "score_llm": 0,
                    "justification": "Réponse LLM invalide",
                    "raw_output": raw_output
                }

            label = str(parsed.get("label", "NORMAL")).upper().strip()
            if label not in {"NORMAL", "URGENT", "CRITIQUE"}:
                label = "NORMAL"

            try:
                score = int(parsed.get("score_llm", 0))
            except:
                score = 0
            score = self._normalize_score(label, score)

            justification = str(parsed.get("justification", "Aucune justification")).strip()

            return {
                "label": label,
                "score_llm": score,
                "justification": justification,
                "raw_output": raw_output
            }

        except Exception as e:
            return {
                "label": "NORMAL",
                "score_llm": 0,
                "justification": f"Erreur LLM: {str(e)}",
                "raw_output": ""
            }