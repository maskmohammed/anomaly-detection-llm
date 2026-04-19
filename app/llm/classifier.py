import json
import re
import requests


class LLMClassifier:
    def __init__(self, model_name="tinyllama", base_url="http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.base_url = base_url

    def build_prompt(self, text: str) -> str:
        return f"""
You are a strict security classifier.

Return ONLY valid JSON.
Do not write anything before or after JSON.

Format:
{{"label":"NORMAL|URGENT|CRITIQUE","score_llm":number,"justification":"short sentence"}}

Rules:
- NORMAL -> score 0 to 39
- URGENT -> score 40 to 69
- CRITIQUE -> score 70 to 100

Message:
{text}
""".strip()

    def _normalize_score(self, label: str, score: int) -> int:
        if label == "NORMAL":
            return max(0, min(score, 39))
        if label == "URGENT":
            return max(40, min(score, 69))
        return max(70, min(score, 100))

    def _extract_json(self, raw_output: str):
        raw_output = raw_output.strip()

        try:
            return json.loads(raw_output)
        except Exception:
            pass

        match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return None

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
                "temperature": 0,
                "num_predict": 60
            }
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=120)
            response.raise_for_status()
            data = response.json()

            raw_output = data.get("response", "").strip()
            print("LLM RAW:", raw_output)

            parsed = self._extract_json(raw_output)
            if not parsed:
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
                score = int(float(parsed.get("score_llm", 0)))
            except Exception:
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