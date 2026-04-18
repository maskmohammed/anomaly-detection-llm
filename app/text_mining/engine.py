# from pathlib import Path
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity


# class TextMiningEngine:
#     def __init__(
#         self,
#         corpus_path="data/normal_corpus.txt",
#         sensitive_words_path="data/sensitive_words.txt"
#     ):
#         self.corpus_path = Path(corpus_path)
#         self.sensitive_words_path = Path(sensitive_words_path)

#         self.normal_corpus = self._load_corpus()
#         self.sensitive_words = self._load_sensitive_words()

#         self.vectorizer = TfidfVectorizer()
#         self.corpus_vectors = self.vectorizer.fit_transform(self.normal_corpus)

#     def _load_corpus(self):
#         if not self.corpus_path.exists():
#             raise FileNotFoundError(f"Corpus introuvable : {self.corpus_path}")

#         lines = self.corpus_path.read_text(encoding="utf-8").splitlines()
#         return [line.strip() for line in lines if line.strip()]

#     def _load_sensitive_words(self):
#         if not self.sensitive_words_path.exists():
#             raise FileNotFoundError(
#                 f"Fichier mots sensibles introuvable : {self.sensitive_words_path}"
#             )

#         lines = self.sensitive_words_path.read_text(encoding="utf-8").splitlines()
#         return [line.strip().lower() for line in lines if line.strip()]

#     def detect_keywords(self, text: str):
#         words = text.lower().split()
#         detected = [word for word in words if word in self.sensitive_words]
#         return list(set(detected))

#     def similarity_score(self, text: str):
#         text_vector = self.vectorizer.transform([text])
#         similarities = cosine_similarity(text_vector, self.corpus_vectors)[0]
#         max_similarity = float(similarities.max())
#         return max_similarity

#     def score(self, text: str):
#         keywords = self.detect_keywords(text)
#         similarity = self.similarity_score(text)

#         if similarity == 0:
#             anomaly_score = 20  
#         else:
#             anomaly_score = (1 - similarity) * 100

#         if keywords:
#             anomaly_score += min(len(keywords) * 10, 30)

#         anomaly_score = max(0, min(anomaly_score, 100))

#         return {
#             "keywords": keywords,
#             "similarity": round(similarity, 3),
#             "score_tm": round(anomaly_score, 2)
#         }






from pathlib import Path
import re
import unicodedata
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TextMiningEngine:
    def __init__(
        self,
        corpus_path="data/normal_corpus.txt",
        sensitive_words_path="data/sensitive_words.txt",
        use_lemmatization=True
    ):
        self.corpus_path = Path(corpus_path)
        self.sensitive_words_path = Path(sensitive_words_path)
        self.use_lemmatization = use_lemmatization

        self._nlp = self._load_nlp()

        self.normal_corpus = self._load_corpus()
        self.sensitive_rules = self._load_sensitive_words()

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            lowercase=False,
            min_df=1
        )
        self.corpus_vectors = self.vectorizer.fit_transform(self.normal_corpus)

    def _load_nlp(self):
        if not self.use_lemmatization:
            return None

        try:
            import spacy
            return spacy.load("fr_core_news_sm")
        except Exception:
            return None

    def _strip_accents(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text)
        return "".join(ch for ch in text if not unicodedata.combining(ch))

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = text.replace("’", "'")
        text = self._strip_accents(text)
        text = re.sub(r"[^a-z0-9'\s-]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()

        if self._nlp:
            doc = self._nlp(text)
            lemmas = []
            for token in doc:
                if token.is_space or token.is_punct:
                    continue
                lemma = token.lemma_.strip().lower()
                if lemma:
                    lemma = self._strip_accents(lemma)
                    lemmas.append(lemma)
            if lemmas:
                text = " ".join(lemmas)

        return text

    def _load_corpus(self):
        if not self.corpus_path.exists():
            raise FileNotFoundError(f"Corpus introuvable : {self.corpus_path}")

        lines = self.corpus_path.read_text(encoding="utf-8").splitlines()
        return [self._normalize(line) for line in lines if line.strip()]

    def _load_sensitive_words(self):
        if not self.sensitive_words_path.exists():
            raise FileNotFoundError(
                f"Fichier mots sensibles introuvable : {self.sensitive_words_path}"
            )

        lines = self.sensitive_words_path.read_text(encoding="utf-8").splitlines()
        rules = []

        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue

            # exemple : "incendie en cours [sûreté][98]"
            match = re.match(r"^(.*?)\s*(\[[^\]]+\])?\[(\d+)\](?:\[[^\]]+\])?$", raw)
            if match:
                phrase = match.group(1).strip()
                score = int(match.group(3))
            else:
                phrase = re.split(r"\s*\[", raw)[0].strip()
                score = 50

            normalized_phrase = self._normalize(phrase)
            if normalized_phrase:
                rules.append({
                    "phrase": normalized_phrase,
                    "weight": score
                })

        return rules

    def detect_keywords(self, text: str):
        normalized_text = self._normalize(text)
        detected = []

        for rule in self.sensitive_rules:
            phrase = rule["phrase"]
            if phrase and phrase in normalized_text:
                detected.append(rule)

        return detected

    def similarity_score(self, text: str):
        normalized_text = self._normalize(text)
        text_vector = self.vectorizer.transform([normalized_text])
        similarities = cosine_similarity(text_vector, self.corpus_vectors)[0]
        return float(similarities.max())

    def score(self, text: str):
        normalized_text = self._normalize(text)
        detected = self.detect_keywords(normalized_text)
        similarity = self.similarity_score(normalized_text)

        # 1) base anomaly douce : plus le texte est loin du corpus normal, plus ça monte
        base_score = (1 - similarity) * 55

        # 2) pondération sensible à partir des poids [95], [80], ...
        keyword_score = 0
        weighted_keywords = []

        for item in detected:
            phrase = item["phrase"]
            weight = item["weight"]

            # conversion du poids en bonus mesuré
            if weight >= 95:
                bonus = 30
            elif weight >= 85:
                bonus = 18
            elif weight >= 70:
                bonus = 10
            elif weight >= 50:
                bonus = 4
            else:
                bonus = 2

            if not detected:
                anomaly_score = min(base_score, 49)

            keyword_score += bonus
            weighted_keywords.append({
                "keyword": phrase,
                "weight": weight,
                "bonus": bonus
            })

        # plafond pour éviter l'explosion
        keyword_score = min(keyword_score, 45)

        anomaly_score = base_score + keyword_score
        anomaly_score = max(0, min(anomaly_score, 100))

        return {
            "keywords": [item["keyword"] for item in weighted_keywords],
            "keyword_details": weighted_keywords,
            "similarity": round(similarity, 3),
            "score_tm": round(anomaly_score, 2)
        }