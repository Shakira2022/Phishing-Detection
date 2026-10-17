"""Context-aware feature construction for the phishing classifier."""

import re

import numpy as np
from scipy.sparse import csr_matrix, hstack

STRUCTURAL_FEATURE_NAMES = [
    "email_length_log", "word_count_log", "url_count", "exclamation_count",
    "question_count", "digit_ratio", "uppercase_ratio", "urgency_terms",
    "credential_terms", "call_to_action_terms", "money_terms", "html_markers",
]

URGENCY = re.compile(r"\b(urgent|immediately|now|asap|24 hours|limited|expire|suspend|warning)\b", re.I)
CREDENTIALS = re.compile(r"\b(password|account|login|verify|verification|credential|security code|bank)\b", re.I)
CALL_TO_ACTION = re.compile(r"\b(click|open|download|confirm|activate|update|login|visit|reply|call)\b", re.I)
MONEY = re.compile(r"(?:\$|£|€|\b(?:money|cash|prize|winner|refund|invoice|payment)\b)", re.I)
URL = re.compile(r"(?:https?://|www\.|\b\w+\.\w{2,}/)", re.I)


def structural_features(texts):
    rows = []
    for value in texts:
        text = str(value)
        words = re.findall(r"\b\w+\b", text)
        letters = [c for c in text if c.isalpha()]
        rows.append([
            np.log1p(len(text)) / 10.0, np.log1p(len(words)) / 8.0, len(URL.findall(text)) / 5.0, text.count("!") / 10.0,
            text.count("?") / 10.0, sum(c.isdigit() for c in text) / max(len(text), 1),
            sum(c.isupper() for c in letters) / max(len(letters), 1), len(URGENCY.findall(text)),
            len(CREDENTIALS.findall(text)) / 5.0, len(CALL_TO_ACTION.findall(text)) / 5.0, len(MONEY.findall(text)) / 5.0,
            len(re.findall(r"<[^>]+>", text)) / 10.0,
        ])
    return csr_matrix(np.asarray(rows, dtype=np.float32))


def build_features(vectorizer, texts, fit=False):
    text_features = vectorizer.fit_transform(texts) if fit else vectorizer.transform(texts)
    return hstack([text_features, structural_features(texts)], format="csr")
