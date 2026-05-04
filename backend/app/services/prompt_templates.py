from langchain_core.prompts import PromptTemplate


SUMMARY_TEMPLATE = PromptTemplate.from_template(
    """<s>Summarize the following email only. Output bullet points..

Output format:
- **[Context]** content
- **[Tag]** content
- **[Tag]** content
- **[Tag]** content

First tag must be context and rest Tags to choose from: Action Required, Deadline, Decision Needed, Key Info, Next Step

[EMAIL START]
{email_text}
[EMAIL END]

Bullet points:"""
)

REPLY_TEMPLATE = PromptTemplate.from_template(
    """You are the person who received the email below. Write a {tone} reply FROM the recipient TO the sender.

RULES:
- You are REPLYING to this email, not continuing it or rewriting it.
- Reply directly to the sender's main point or request.
- Do not copy the sender's language or repeat their offer back to them.
- Do not invent names, links, dates, numbers, or facts not in the email.
- No subject line, no signature block.
- Length: 100 words.
- End with a clear next step or question.

TONE: {tone}
- formal: professional, complete sentences, no contractions.
- casual: warm, conversational, contractions allowed.
- concise: short sentences, direct, no filler.

[EMAIL RECEIVED]
{email_text}
[END EMAIL]

Your reply (start directly, no preamble):"""
)
