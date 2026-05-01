import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    label: str
    score: float
    model_version: str


@dataclass(frozen=True)
class Signal:
    label: str
    pattern: re.Pattern[str]
    weight: float


class HeuristicEmailClassifier:
    model_version = "heuristic-classifier-v3"

    def __init__(self) -> None:
        self.signals = [
            Signal("urgent", re.compile(r"\b(urgent|asap|immediately|eod|blocked|critical|important)\b", re.I), 0.36),
            Signal("follow-up", re.compile(r"\b(following up|follow up|checking in|reminder|gentle reminder|waiting)\b", re.I), 0.3),
            Signal("action-required", re.compile(r"\b(please|can you|could you|need you to|submit|confirm|send|review)\b", re.I), 0.28),
            Signal("opportunity", re.compile(r"\b(internship|placement|tnp|training and placement|career opportunity|hiring|apply|campus drive)\b", re.I), 0.42),
            Signal("work", re.compile(r"\b(project|meeting|deadline|review|proposal|invoice|client|report)\b", re.I), 0.26),
            Signal("finance", re.compile(r"\b(invoice|payment|receipt|billing|refund|paid|amount due)\b", re.I), 0.25),
            Signal("personal", re.compile(r"\b(family|dinner|birthday|weekend|trip|holiday)\b", re.I), 0.22),
            Signal("spam", re.compile(r"\b(winner|free money|claim now|limited offer|act now|prize)\b", re.I), 0.34),
            Signal("newsletter", re.compile(r"\b(newsletter|unsubscribe|weekly update|digest|read more)\b", re.I), 0.24),
        ]

    def classify(self, email_text: str) -> Classification:
        normalized = " ".join(email_text.split())
        scores: dict[str, float] = {}

        for signal in self.signals:
            if signal.pattern.search(normalized):
                scores[signal.label] = scores.get(signal.label, 0.18) + signal.weight

        if self._has_institutional_signal(normalized):
            scores["opportunity"] = scores.get("opportunity", 0.18) + 0.42
            scores["work"] = scores.get("work", 0.18) + 0.18
            if "newsletter" in scores:
                scores["newsletter"] *= 0.35

        if not scores:
            if len(normalized) > 900:
                return Classification("newsletter", 0.68, self.model_version)
            return Classification("low-priority", 0.62, self.model_version)

        label, score = sorted(scores.items(), key=lambda item: item[1], reverse=True)[0]
        return Classification(label, min(0.95, max(0.55, score)), self.model_version)

    def _has_institutional_signal(self, text: str) -> bool:
        return bool(
            re.search(
                r"\b(tnp|training and placement|placement cell|career development|iiit|iit|nit|university|college|"
                r"\.edu\b|\.ac\.in\b|@[^@\s]+\.ac\.in\b)\b",
                text,
                re.I,
            )
        )
