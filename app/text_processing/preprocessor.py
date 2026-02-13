import re

class TextPreprocessor:

    def clean(self, text: str) -> str:
        # 1️⃣ mettre en minuscules
        text = text.lower()

        # 2️⃣ supprimer la ponctuation
        text = re.sub(r"[^\w\s]", "", text)

        # 3️⃣ supprimer espaces multiples
        text = re.sub(r"\s+", " ", text)

        # 4️⃣ supprimer espaces début/fin
        text = text.strip()

        return text
