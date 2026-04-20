"""Feature extraction utilities for log messages — format-agnostic.

Normalization strips timestamps, IPs, UUIDs, hex hashes, file paths, and URLs
from any log format (HDFS, nginx, syslog, Python, Java, Docker, Go) before
TF-IDF vectorization, so the vocabulary captures meaningful semantic words
rather than variable runtime data.
"""

from __future__ import annotations

import re
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer

from .config import FeatureConfig


# --------------------------------------------------------------------------- #
# Ordered noise-stripping regex patterns                                       #
# Apply in this order: URLs → timestamps → IPs → UUIDs → hex → paths → nums  #
# --------------------------------------------------------------------------- #

# URLs (before IP/path patterns consume parts of them)
_URL_RE = re.compile(r"https?://\S+|ftp://\S+", re.IGNORECASE)

# ISO 8601 and common timestamp variants
#   2026-04-20T23:45:01Z  /  2026-04-20 23:45:01.123  /  2026-04-20 23:45:01+05:30
_ISO_TS_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?",
    re.IGNORECASE,
)

# Apache / HDFS bracket timestamp: [20/Apr/2026:23:45:01 +0000]
_APACHE_TS_RE = re.compile(
    r"\[?\d{1,2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}(?:\s[+-]\d{4})?\]?",
    re.IGNORECASE,
)

# Syslog: Apr 20 23:45:01
_SYSLOG_TS_RE = re.compile(
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b",
    re.IGNORECASE,
)

# Unix epoch — 10 or 13 digits standalone
_EPOCH_RE = re.compile(r"\b\d{10,13}\b")

# IP address with optional port: 192.168.1.100  or  10.0.0.1:8080
_IP_RE = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}(?::\d{2,5})?\b")

# UUID (must come before hex to catch the full token as one unit)
_UUID_RE = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    re.IGNORECASE,
)

# Hex blobs: 0x1a2b3c  or  standalone 6+ hex-char tokens like deadbeef
_HEX_RE = re.compile(r"0x[0-9a-f]+|\b[0-9a-f]{6,}\b", re.IGNORECASE)

# File / directory paths: /var/log/app.log  or  C:\Windows\System32\foo.dll
_PATH_RE = re.compile(r"(?:[A-Za-z]:)?(?:[/\\][\w.\-]+){2,}")

# Java fully-qualified class names: org.apache.hadoop.hdfs.DataNode
# → keep only the last segment (the actual class name)
_JAVA_CLASS_RE = re.compile(r"\b(?:[a-z][\w]*\.){2,}([A-Z][\w]*)\b")

# Remaining standalone numbers (after all specific patterns handled above)
_NUM_RE = re.compile(r"\b\d+(?:[.,]\d+)?\b")

# Collapse whitespace
_WS_RE = re.compile(r"\s+")


class LogFeatureExtractor:
    """Normalize log lines and convert them into TF-IDF vectors.

    The normalization pipeline is format-agnostic: it strips known noise
    patterns (timestamps, IPs, UUIDs, paths, hex, numbers) so that the TF-IDF
    vocabulary captures meaningful action words and log levels, not runtime
    variable data.
    """

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
        """Format-agnostic normalization pipeline.

        Strips noise patterns in a deterministic order so that meaningful
        words (log levels, action verbs, system nouns) survive into the
        TF-IDF vocabulary.
        """
        s = log

        # 1. URLs — before IP/path patterns consume their parts
        s = _URL_RE.sub(" <URL> ", s)

        # 2. Timestamps — most specific format first
        s = _ISO_TS_RE.sub(" <TIMESTAMP> ", s)
        s = _APACHE_TS_RE.sub(" <TIMESTAMP> ", s)
        s = _SYSLOG_TS_RE.sub(" <TIMESTAMP> ", s)
        s = _EPOCH_RE.sub(" <TIMESTAMP> ", s)

        # 3. IP addresses
        s = _IP_RE.sub(" <IP> ", s)

        # 4. UUIDs (before hex, so full UUID is one token not mangled)
        s = _UUID_RE.sub(" <UUID> ", s)

        # 5. Hex blobs
        s = _HEX_RE.sub(" <HEX> ", s)

        # 6. File / directory paths
        s = _PATH_RE.sub(" <PATH> ", s)

        # 7. Java class names → keep only the final class-name segment
        s = _JAVA_CLASS_RE.sub(r"\1", s)

        # 8. Remaining numbers
        s = _NUM_RE.sub(" <NUM> ", s)

        # 9. Lowercase + collapse whitespace
        return _WS_RE.sub(" ", s).strip().lower()

    def _prepare(self, logs: Iterable[str]) -> list[str]:
        return [self._normalize(log) for log in logs]

    def fit(self, logs: Iterable[str]) -> "LogFeatureExtractor":
        self.vectorizer.fit(self._prepare(logs))
        return self

    def transform(self, logs: Iterable[str]):
        return self.vectorizer.transform(self._prepare(logs))

    def fit_transform(self, logs: Iterable[str]):
        return self.vectorizer.fit_transform(self._prepare(logs))
