from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TextMiningEngine:
    def __init__(
        self,
        corpus_path="data/normal_corpus.txt",
        sensitive_words_path="data/sensitive_words.txt"
    ):
        self.corpus_path = Path(corpus_path)
        self.sensitive_words_path = Path(sensitive_words_path)

        self.normal_corpus = self._load_corpus()
        self.sensitive_words = self._load_sensitive_words()

        self.vectorizer = TfidfVectorizer()
        self.corpus_vectors = self.vectorizer.fit_transform(self.normal_corpus)

    def _load_corpus(self):
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus introuvable : {self.corpus_path}")

        lines = self.corpus_path.read_text(encoding="utf-8").splitlines()
        return [line.strip() for line in lines if line.strip()]

    def _load_sensitive_words(self):
        if not self.sensitive_words_path.exists():
            raise FileNotFoundError(
                f"Fichier mots sensibles introuvable : {self.sensitive_words_path}"
            )

        lines = self.sensitive_words_path.read_text(encoding="utf-8").splitlines()
        return [line.strip().lower() for line in lines if line.strip()]

    def detect_keywords(self, text: str):
        words = text.lower().split()
        detected = [word for word in words if word in self.sensitive_words]
        return list(set(detected))

    def similarity_score(self, text: str):
        text_vector = self.vectorizer.transform([text])
        similarities = cosine_similarity(text_vector, self.corpus_vectors)[0]
        max_similarity = float(similarities.max())
        return max_similarity

    def score(self, text: str):
        keywords = self.detect_keywords(text)
        similarity = self.similarity_score(text)

        if similarity == 0:
            anomaly_score = 20  
        else:
            anomaly_score = (1 - similarity) * 100

        if keywords:
            anomaly_score += min(len(keywords) * 10, 30)

        anomaly_score = max(0, min(anomaly_score, 100))

        return {
            "keywords": keywords,
            "similarity": round(similarity, 3),
            "score_tm": round(anomaly_score, 2)
        }