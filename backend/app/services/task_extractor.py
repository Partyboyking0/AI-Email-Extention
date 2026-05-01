import re
from dataclasses import dataclass

from backend.app.schemas.email import TaskItem


@dataclass(frozen=True)
class TaskCandidate:
    text: str
    deadline: str | None = None


class HeuristicTaskExtractor:
    ACTION_PATTERNS = (
        r"\bplease\s+(?P<task>[^.?!\n]+)",
        r"\bcan you\s+(?P<task>[^.?!\n]+)",
        r"\bcould you\s+(?P<task>[^.?!\n]+)",
        r"\bneed you to\s+(?P<task>[^.?!\n]+)",
        r"\baction item:?\s+(?P<task>[^.?!\n]+)",
    )
    INVITATION_PATTERNS = (
        r"\b(?P<task>apply(?:\s+for|\s+to)?[^.?!\n]*)",
        r"\b(?P<task>fill out[^.?!\n]*)",
        r"\b(?P<task>submit[^.?!\n]*)",
        r"\b(?P<task>register[^.?!\n]*)",
        r"\b(?P<task>visit[^.?!\n]*link[^.?!\n]*)",
        r"\b(?P<task>click[^.?!\n]*)",
        r"\b(?P<task>attach[^.?!\n]*)",
        r"\b(?P<task>send[^.?!\n]*resume[^.?!\n]*)",
        r"\b(?P<task>complete[^.?!\n]*form[^.?!\n]*)",
        r"\b(?P<task>interested[^.?!\n]*contact[^.?!\n]*)",
    )
    DEADLINE_PATTERN = re.compile(
        r"\b(?P<deadline>today|tomorrow|by eod|eod|by friday|by monday|this week|next week|"
        r"\d{1,2}/\d{1,2}(?:/\d{2,4})?|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2})\b",
        re.IGNORECASE,
    )

    def extract(self, email_text: str, limit: int = 5) -> list[TaskItem]:
        candidates: list[TaskCandidate] = []
        for sentence in self._sentences(email_text):
            deadline = self._deadline(sentence)
            for pattern in self.ACTION_PATTERNS:
                match = re.search(pattern, sentence, flags=re.IGNORECASE)
                if match:
                    candidates.append(TaskCandidate(text=self._normalize_task(match.group("task")), deadline=deadline))
                    break
            else:
                for pattern in self.INVITATION_PATTERNS:
                    match = re.search(pattern, sentence, flags=re.IGNORECASE)
                    if match:
                        candidates.append(TaskCandidate(text=self._normalize_task(match.group("task")), deadline=deadline))
                        break

            if not candidates and deadline and self._looks_actionable(sentence):
                candidates.append(TaskCandidate(text=self._normalize_task(sentence), deadline=deadline))

        deduped = self._dedupe(candidates)[:limit]
        if not deduped:
            deduped = [TaskCandidate(text=self._fallback_task(email_text))]

        return [
            TaskItem(id=f"task-{index + 1}", text=candidate.text, deadline=candidate.deadline)
            for index, candidate in enumerate(deduped)
        ]

    def _sentences(self, email_text: str) -> list[str]:
        return [part.strip() for part in re.split(r"(?<=[.?!])\s+|\n+", email_text) if part.strip()]

    def _deadline(self, sentence: str) -> str | None:
        match = self.DEADLINE_PATTERN.search(sentence)
        return match.group("deadline") if match else None

    def _looks_actionable(self, sentence: str) -> bool:
        return bool(
            re.search(
                r"\b(send|review|confirm|schedule|share|update|prepare|approve|fix|apply|submit|register|contact|form)\b",
                sentence,
                re.IGNORECASE,
            )
        )

    def _normalize_task(self, task: str) -> str:
        task = re.sub(self.DEADLINE_PATTERN, "", task).strip(" ,.-")
        if not task:
            return "Review email and decide the next action"
        return task[0].upper() + task[1:]

    def _fallback_task(self, email_text: str) -> str:
        if re.search(r"\b(internship|placement|tnp|training and placement|opportunity)\b", email_text, re.IGNORECASE):
            org = self._detect_org(email_text)
            return f"Respond to internship opportunity from {org}" if org else "Respond to internship opportunity"
        return "Review email and decide the next action"

    def _detect_org(self, email_text: str) -> str | None:
        branded = re.search(r"\b([A-Z][A-Za-z0-9&.-]+(?:\s+[A-Z][A-Za-z0-9&.-]+){0,3})\b", email_text)
        if branded:
            candidate = branded.group(1).strip()
            if candidate.lower() not in {"dear student", "hello", "regards"}:
                return candidate
        return None

    def _dedupe(self, candidates: list[TaskCandidate]) -> list[TaskCandidate]:
        seen: set[str] = set()
        result: list[TaskCandidate] = []
        for candidate in candidates:
            key = candidate.text.lower()
            if key not in seen:
                seen.add(key)
                result.append(candidate)
        return result
