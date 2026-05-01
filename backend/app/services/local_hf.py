from functools import cached_property

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from backend.app.schemas.email import Tone
from backend.app.services.local_reply import LocalReplyGenerator
from backend.app.services.prompt_templates import REPLY_TEMPLATE, SUMMARY_TEMPLATE


class LocalHuggingFaceService:
    def __init__(self, summarizer_model: str, reply_model: str) -> None:
        self.summarizer_model = summarizer_model
        self.reply_model = reply_model
        self.fallback_reply = LocalReplyGenerator()

    @cached_property
    def _torch(self):
        import torch

        return torch

    @cached_property
    def _summary_components(self):
        return self._load_seq2seq(self.summarizer_model)

    @cached_property
    def _reply_components(self):
        return self._load_seq2seq(self.reply_model)

    @cached_property
    def _summary_chain(self):
        return (
            SUMMARY_TEMPLATE
            | RunnableLambda(lambda prompt: self._generate_seq2seq(self._summary_components, prompt.to_string(), 180))
            | StrOutputParser()
        )

    @cached_property
    def _reply_chain(self):
        return (
            REPLY_TEMPLATE
            | RunnableLambda(lambda prompt: self._generate_seq2seq(self._reply_components, prompt.to_string(), 180))
            | StrOutputParser()
        )

    def summarize(self, email_text: str) -> list[str]:
        source = self._truncate(email_text, max_words=700)
        generated = self._summary_chain.invoke({"email_text": source})
        return self._to_three_bullets(generated, source)

    def reply(self, email_text: str, tone: Tone) -> str:
        source = self._truncate(email_text, max_words=500)
        generated = self._reply_chain.invoke({"tone": tone, "email_text": source})
        return self._clean_reply(generated, source, tone)

    def _load_seq2seq(self, model_name: str):
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        model.eval()
        return tokenizer, model

    def _generate_seq2seq(self, components, prompt: str, max_new_tokens: int) -> str:
        tokenizer, model = components
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=min(getattr(tokenizer, "model_max_length", 1024), 1024),
        )
        with self._torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                num_beams=2,
                do_sample=False,
                no_repeat_ngram_size=3,
                repetition_penalty=1.4,
                early_stopping=True,
            )
        return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

    def _truncate(self, text: str, max_words: int) -> str:
        return " ".join(text.split()[:max_words])

    def _to_three_bullets(self, generated: str, source: str) -> list[str]:
        text = generated.replace("\r", "\n")
        banned = (
            "you are an email assistant",
            "you are an email summarization assistant",
            "extract the most actionable",
            "summarize this email",
            "summarize the following email",
            "return exactly",
            "output exactly",
            "each bullet",
            "use only",
            "email:",
            "email start",
            "email end",
            "bullets:",
            "bullet points",
            "three bullet summary",
        )
        raw_items = []
        for line in text.splitlines():
            cleaned = line.strip(" -*\t")
            if cleaned and not any(fragment in cleaned.lower() for fragment in banned):
                raw_items.append(cleaned)

        if len(raw_items) < 3:
            raw_items = [
                part.strip(" -*\t")
                for part in text.replace(";", ".").split(".")
                if part.strip(" -*\t") and not any(fragment in part.lower() for fragment in banned)
            ]

        if len(raw_items) < 2:
            raw_items = self._source_bullets(source)

        bullets = raw_items[:3]
        while len(bullets) < 3:
            bullets.append("Review the email and confirm the next action")
        return [bullet[0].upper() + bullet[1:] if bullet else bullet for bullet in bullets]

    def _source_bullets(self, source: str) -> list[str]:
        separators = source.replace("\n", ". ").replace(";", ".")
        sentences = [part.strip(" -*\t") for part in separators.split(".") if part.strip(" -*\t")]
        return sentences[:3] or ["Review the email and confirm the next action"]

    def _clean_reply(self, generated: str, source: str, tone: Tone) -> str:
        reply = generated.strip()
        for prefix in ("Reply:", "Email reply:", "Subject:"):
            if reply.lower().startswith(prefix.lower()):
                reply = reply[len(prefix):].strip()

        sentences = [part.strip() for part in reply.replace("\n", " ").split(".") if part.strip()]
        deduped = []
        seen = set()
        for sentence in sentences:
            key = sentence.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(sentence)
        reply = ". ".join(deduped[:4]).strip()
        if reply and not reply.endswith((".", "!", "?")):
            reply += "."

        lowered = reply.lower()
        repeated_apology = lowered.count("i'm sorry") > 1 or lowered.count("sorry") > 2
        prompt_echo = any(fragment in lowered for fragment in ("write a", "email:", "use only", "do not include"))
        too_short = len(reply.split()) < 5
        if repeated_apology or prompt_echo or too_short:
            return self.fallback_reply.reply(source, tone)

        return reply or self.fallback_reply.reply(source, tone)
