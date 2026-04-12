import re

class TextPreprocessor:

    def clean(self, text: str) -> str:
        text = text.lower()

        text = re.sub(r"[^\w\s]", "", text)

        text = re.sub(r"\s+", " ", text)

        text = text.strip()

        return text
