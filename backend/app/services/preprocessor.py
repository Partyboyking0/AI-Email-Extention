import re

from bs4 import BeautifulSoup


class EmailPreprocessor:
    def clean(self, raw_email: str) -> str:
        text = self.strip_html(raw_email)
        text = self.remove_quoted_blocks(text)
        text = self.remove_signature(text)
        text = self.scrub_pii(text)
        return self.truncate(text)

    def strip_html(self, value: str) -> str:
        soup = BeautifulSoup(value, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(" ", strip=True)

    def remove_quoted_blocks(self, value: str) -> str:
        lines = [line for line in value.splitlines() if not line.strip().startswith(">")]
        return "\n".join(lines)

    def remove_signature(self, value: str) -> str:
        markers = ("-- ", "Best regards", "Regards,", "Thanks,")
        positions = [value.find(marker) for marker in markers if value.find(marker) > 0]
        return value[: min(positions)] if positions else value

    def scrub_pii(self, value: str) -> str:
        value = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL]", value)
        value = re.sub(r"\+?\d[\d\s().-]{7,}\d", "[PHONE]", value)
        return value

    def truncate(self, value: str, max_words: int = 512) -> str:
        words = value.split()
        return " ".join(words[:max_words])
