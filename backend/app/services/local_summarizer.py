import re
from collections import Counter


class LocalSummarizer:
    ACTION_WORDS = {
        "review",
        "send",
        "confirm",
        "schedule",
        "prepare",
        "share",
        "update",
        "reply",
        "approve",
        "deadline",
        "meeting",
        "today",
        "tomorrow",
        "friday",
        "monday",
        "important",
        "need",
        "please",
    }
    STOP_WORDS = {
        "the",
        "and",
        "or",
        "to",
        "of",
        "a",
        "an",
        "in",
        "for",
        "with",
        "on",
        "is",
        "are",
        "was",
        "were",
        "this",
        "that",
        "it",
        "you",
        "your",
        "we",
        "our",
        "i",
        "my",
    }

    def summarize(self, email_text: str) -> list[str]:
        sentences = self._sentences(email_text)
        if not sentences:
            return [
                "Review the email content for the sender's main request.",
                "Identify any deadlines, tasks, or meeting details.",
                "Respond with a clear next step.",
            ]

        keywords = self._keywords(email_text)
        scored = sorted(
            enumerate(sentences),
            key=lambda item: self._score_sentence(item[1], item[0], keywords),
            reverse=True,
        )
        selected = sorted(scored[:3], key=lambda item: item[0])
        bullets = [self._compress(sentence) for _, sentence in selected]

        while len(bullets) < 3:
            bullets.append("Respond with a clear next step.")
        return bullets[:3]

    def _sentences(self, email_text: str) -> list[str]:
        text = re.sub(r"https?://\S+", "", email_text)
        parts = re.split(r"(?<=[.?!])\s+|\n+", text)
        return [part.strip(" -\t") for part in parts if len(part.strip()) > 25]

    def _keywords(self, email_text: str) -> Counter[str]:
        words = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", email_text.lower())
        return Counter(word for word in words if word not in self.STOP_WORDS)

    def _score_sentence(self, sentence: str, index: int, keywords: Counter[str]) -> float:
        words = re.findall(r"[a-zA-Z][a-zA-Z'-]{2,}", sentence.lower())
        score = sum(keywords[word] for word in words)
        score += sum(4 for word in words if word in self.ACTION_WORDS)
        if index < 2:
            score += 6
        if 60 <= len(sentence) <= 220:
            score += 4
        return score / max(8, len(words))

    def _compress(self, sentence: str, max_words: int = 24) -> str:
        words = sentence.split()
        clipped = " ".join(words[:max_words]).strip(" ,;:-")
        if len(words) > max_words:
            clipped += "..."
        return clipped[0].upper() + clipped[1:] if clipped else "Review the email content."
