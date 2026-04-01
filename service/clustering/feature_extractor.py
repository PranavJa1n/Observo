"""Feature extraction utilities for log messages."""

from __future__ import annotations

import re
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer

from .config import FeatureConfig


_DIGIT_RE = re.compile(r"\d+")
_WHITESPACE_RE = re.compile(r"\s+")


class LogFeatureExtractor:
    """Normalize log lines and convert them into TF-IDF vectors."""

    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config or FeatureConfig()
        self.vectorizer = TfidfVectorizer(
            max_features=self.config.max_features,
            ngram_range=self.config.ngram_range,
            analyzer=self.config.analyzer,
            lowercase=self.config.lowercase,
        )

    @staticmethod
    def _normalize(log: str) -> str:
        """Light-weight normalization to reduce variance in numeric ids."""

        scrubbed = _DIGIT_RE.sub(" <NUM> ", log)
        scrubbed = scrubbed.replace("-", " ").replace("/", " ")
        scrubbed = _WHITESPACE_RE.sub(" ", scrubbed)
        return scrubbed.strip().lower()

    def _prepare(self, logs: Iterable[str]) -> list[str]:
        return [self._normalize(log) for log in logs]

    def fit(self, logs: Iterable[str]) -> "LogFeatureExtractor":
        prepared = self._prepare(logs)
        self.vectorizer.fit(prepared)
        return self

    def transform(self, logs: Iterable[str]):
        prepared = self._prepare(logs)
        return self.vectorizer.transform(prepared)

    def fit_transform(self, logs: Iterable[str]):
        prepared = self._prepare(logs)
        return self.vectorizer.fit_transform(prepared)
