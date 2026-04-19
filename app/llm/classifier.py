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

        Task:
        Classify the message into exactly one label:
        NORMAL, URGENT, or CRITIQUE.

        Definitions:
        - NORMAL: greeting, neutral, routine communication, no threat
        - URGENT: anomaly, problem, unusual situation, request for immediate help
        - CRITIQUE: attack, intrusion, sabotage, explosion, bomb, immediate danger

        Score rules:
        - NORMAL -> 0 to 39
        - URGENT -> 40 to 69
        - CRITIQUE -> 70 to 100

        IMPORTANT:
        - Return ONLY valid JSON
        - Do not add explanations outside JSON
        - Use exactly this format

        {{
        "label": "NORMAL",
        "score_llm": 15,
        "justification": "short sentence"
        }}

        Message:
        {text}
        """.strip()

    def _normalize_score(self, label: str, score: int) -> int:
        if label == "NORMAL":
            return max(0, min(score, 39))
        if label == "URGENT":
            return max(40, min(score, 69))
        return max(70, min(score, 100))

    def _default_score_from_label(self, label: str) -> int:
        if label == "NORMAL":
            return 15
        if label == "URGENT":
            return 55
        return 85

    def _extract_json(self, raw_output: str):
        raw_output = raw_output.strip()

        try:
            return json.loads(raw_output)
        except Exception:
            pass

        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass

        return None

    def _fallback_label_from_text(self, text: str, raw_output: str, justification: str = "") -> str:
        combined = f"{text} {raw_output} {justification}".lower()

        critical_keywords = [
            "attaque", "intrusion", "sabotage", "explosion", "bombe",
            "ennemi", "arme", "danger immediat", "danger immédiat",
            "feu", "incendie", "terroriste"
        ]

        urgent_keywords = [
            "urgence", "urgent", "aide", "besoin d aide", "besoin d'aide",
            "assistance", "probleme", "problème", "anomalie", "incident",
            "blessé", "blesse", "danger", "sos"
        ]

        if any(word in combined for word in critical_keywords):
            return "CRITIQUE"

        if any(word in combined for word in urgent_keywords):
            return "URGENT"

        return "NORMAL"

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

            if parsed:
                label = str(parsed.get("label", "NORMAL")).upper().strip()
                justification = str(parsed.get("justification", "Aucune justification")).strip()
                raw_score = parsed.get("score_llm", None)

                if label not in {"NORMAL", "URGENT", "CRITIQUE"}:
                    label = self._fallback_label_from_text(text, raw_output, justification)

                try:
                    if raw_score is None or str(raw_score).strip() == "":
                        score = self._default_score_from_label(label)
                    else:
                        score = int(float(raw_score))
                        if score == 0:
                            score = self._default_score_from_label(label)
                except Exception:
                    score = self._default_score_from_label(label)

                score = self._normalize_score(label, score)

                return {
                    "label": label,
                    "score_llm": score,
                    "justification": justification,
                    "raw_output": raw_output
                }

            label = self._fallback_label_from_text(text, raw_output)
            score = self._default_score_from_label(label)

            return {
                "label": label,
                "score_llm": score,
                "justification": "Réponse non JSON, score déduit automatiquement",
                "raw_output": raw_output
            }

        except Exception as e:
            fallback_label = self._fallback_label_from_text(text, "")
            fallback_score = self._default_score_from_label(fallback_label)

            return {
                "label": fallback_label,
                "score_llm": fallback_score,
                "justification": f"Erreur LLM, fallback appliqué: {str(e)}",
                "raw_output": ""
            }