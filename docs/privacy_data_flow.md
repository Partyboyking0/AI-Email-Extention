# Privacy Data Flow

Email text leaves the browser only when the user clicks an AI action that requires backend inference. The extension sends email body text, tone preference, and an internal thread identifier. Subjects, labels, sender metadata, and Gmail account metadata are not required for the Phase 1-3 flow.

The backend preprocesses text before logging or model calls: HTML is stripped, quoted blocks and signatures are removed, and email addresses and phone numbers are replaced with placeholders.

Server-side storage is limited to user preferences, usage counters, feedback examples, and anonymized hashes or embeddings. Raw email content should not be persisted.

All production API calls must use HTTPS. OAuth scopes should remain minimal: start with Gmail read-only, then add Google Tasks only when the task integration is implemented.
