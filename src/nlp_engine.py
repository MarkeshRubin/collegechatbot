import re
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TAMIL_MAP = {
    "சேர்க்கை": "admission apply",
    "கட்டணம்": "fees tuition fee",
    "படிப்புகள்": "courses ug pg",
    "உதவித்தொகை": "scholarship merit",
    "வேலைவாய்ப்பு": "placement package recruiters",
    "விடுதி": "hostel room accommodation",
    "பேருந்து": "transport bus",
    "நூலகம்": "library",
    "தேர்வு": "exam semester",
    "தகுதி": "eligibility",
    "முகவரி": "location address",
    "தொடர்பு": "contact phone email"
}

class StudioNLPEngine:
    def __init__(self, kb_df: pd.DataFrame, threshold: float = 0.22):
        self.df = kb_df.copy().reset_index(drop=True)
        self.threshold = threshold
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
        self.matrix = None
        self._fit()

    @staticmethod
    def clean(text: str) -> str:
        if not isinstance(text, str):
            return ""
        t = text.lower().strip()
        for k, v in TAMIL_MAP.items():
            if k in t:
                t += f" {v}"
        t = re.sub(r"[^a-z0-9\s]", " ", t)
        return re.sub(r"\s+", " ", t).strip()

    def _fit(self):
        if self.df.empty:
            return
        corpus = (
            self.df["Question"].astype(str) + " " +
            self.df["Question"].astype(str) + " " +
            self.df["Keywords"].astype(str).str.replace(";", " ", regex=False) + " " +
            self.df["Category"].astype(str)
        ).apply(self.clean)
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _keyword_score(self, q_clean: str) -> np.ndarray:
        q_tokens = set(q_clean.split())
        if not q_tokens:
            return np.zeros(len(self.df))
        scores = np.zeros(len(self.df))
        for i, kw in enumerate(self.df["Keywords"].astype(str)):
            kw_tokens = set(self.clean(kw.replace(";", " ")).split())
            if kw_tokens:
                scores[i] = len(q_tokens & kw_tokens) / len(kw_tokens)
        return scores

    def query(self, user_text: str, prev_category: str | None = None, lang: str = "English") -> dict:
        if self.df.empty or self.matrix is None:
            return self._fallback(lang, 0.0)
        q_clean = self.clean(user_text)
        if not q_clean:
            return self._fallback(lang, 0.0)

        contextual = f"{q_clean} {prev_category.lower()}" if (prev_category and len(q_clean.split()) <= 3) else q_clean
        vec = self.vectorizer.transform([contextual])
        cos_sim = cosine_similarity(vec, self.matrix).flatten()
        kw_sim = self._keyword_score(q_clean)
        combined = 0.78 * cos_sim + 0.22 * kw_sim

        best_idx = int(np.argmax(combined))
        best_score = float(combined[best_idx])

        if best_score < self.threshold and float(cos_sim[best_idx]) < self.threshold:
            return self._fallback(lang, best_score)

        row = self.df.iloc[best_idx]
        cat = str(row["Category"])
        ans = str(row["Answer"])
        if lang == "Tamil":
            ans = f"**[{cat}]**\n\n{ans}"

        same_cat = self.df[(self.df["Category"] == cat) & (self.df["ID"] != row["ID"])]["Question"].head(3).tolist()
        if len(same_cat) < 3:
            extra = self.df[self.df["ID"] != row["ID"]]["Question"].head(3 - len(same_cat)).tolist()
            same_cat.extend(extra)

        return {
            "matched": True,
            "category": cat,
            "matched_question": str(row["Question"]),
            "answer": ans,
            "confidence": min(best_score, 1.0),
            "follow_ups": same_cat[:3],
            "status": "Answered"
        }

    def _fallback(self, lang: str, score: float) -> dict:
        msg = (
            "மன்னிக்கவும், இதற்கான தகவல் தரவுத்தளத்தில் இல்லை. கல்லூரி அலுவலகத்தைத் தொடர்பு கொள்ளவும்."
            if lang == "Tamil"
            else "I couldn't find an exact verified match in the knowledge base. Please contact the Admissions Office (+91-44-2345-6789) or submit a Direct Enquiry."
        )
        return {
            "matched": False,
            "category": "Unanswered",
            "matched_question": "None",
            "answer": msg,
            "confidence": score,
            "follow_ups": ["What undergraduate courses are offered?", "What is the tuition fee structure?", "How can I apply for admission?"],
            "status": "Unanswered"
        }
