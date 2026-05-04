from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path


LABELS = [
    "urgent",
    "follow-up",
    "action-required",
    "low-priority",
    "finance",
    "newsletter",
    "opportunity",
    "spam",
    "work",
    "personal",
]


SCENARIOS: dict[str, dict[str, list[str]]] = {
    "urgent": {
        "subjects": [
            "Immediate approval needed",
            "Production issue requires response",
            "Client escalation today",
            "Security alert needs action",
        ],
        "senders": ["ops lead", "support manager", "security team", "project owner"],
        "bodies": [
            "Please review this immediately. The customer is blocked and needs an answer before close of business today.",
            "We found a critical issue in the latest release. Confirm ownership and send the mitigation plan within the hour.",
            "This has been escalated by leadership. I need your decision and next action before the 3 PM call.",
            "The account is at risk unless we respond today. Please prioritize this over routine work.",
        ],
    },
    "follow-up": {
        "subjects": [
            "Following up on yesterday's note",
            "Checking in on pending review",
            "Reminder about open item",
            "Quick follow-up on the proposal",
        ],
        "senders": ["client success", "team coordinator", "vendor contact", "review owner"],
        "bodies": [
            "I wanted to follow up on the document I sent earlier. Can you share your feedback when you get a chance?",
            "Just checking whether there is any update on the pending approval from last week.",
            "Following up so this does not get missed. Please let me know if you need anything from my side.",
            "Can you confirm the status of the open item before our next sync?",
        ],
    },
    "action-required": {
        "subjects": [
            "Please complete the onboarding form",
            "Signature required for agreement",
            "Submit your details by Friday",
            "Action needed for account setup",
        ],
        "senders": ["hr operations", "admin desk", "platform team", "compliance office"],
        "bodies": [
            "Please fill out the attached form and submit it by Friday so we can complete the process.",
            "Your approval is required before we can move forward. Review the attachment and confirm once signed.",
            "Complete the requested details in the portal today. The setup cannot proceed until this is done.",
            "Please send the required documents and confirm your availability for the next step.",
        ],
    },
    "low-priority": {
        "subjects": [
            "Monthly system digest",
            "FYI office maintenance notice",
            "Weekly platform update",
            "General information for your records",
        ],
        "senders": ["admin notifications", "system updates", "facilities team", "internal portal"],
        "bodies": [
            "This is an informational update only. No action is required from your side at this time.",
            "Sharing the weekly digest for awareness. You can review it whenever convenient.",
            "The maintenance window is scheduled outside working hours. This message is for your records.",
            "Here is a routine update about internal tools and policy reminders.",
        ],
    },
    "finance": {
        "subjects": [
            "Invoice ready for payment",
            "Payment receipt attached",
            "Budget approval request",
            "Expense report needs review",
        ],
        "senders": ["accounts team", "finance desk", "billing office", "vendor billing"],
        "bodies": [
            "The invoice for this month is attached. Please review the amount and process payment by the due date.",
            "Your payment receipt has been generated. The transaction reference and tax details are included below.",
            "Please approve the revised budget so procurement can release the purchase order.",
            "The expense claim needs review because one receipt is missing from the submitted report.",
        ],
    },
    "newsletter": {
        "subjects": [
            "This week's product newsletter",
            "Career tips and industry insights",
            "Latest stories from our blog",
            "Monthly community roundup",
        ],
        "senders": ["newsletter team", "marketing updates", "community digest", "content desk"],
        "bodies": [
            "Welcome to this week's newsletter. Read the latest articles, product tips, and community highlights.",
            "Here are the most popular resources from our blog, plus upcoming webinars and guides.",
            "You are receiving this update because you subscribed to our mailing list. Unsubscribe link is below.",
            "Explore new tutorials, customer stories, and product announcements in this monthly roundup.",
        ],
    },
    "opportunity": {
        "subjects": [
            "Internship opportunity from placement cell",
            "Application open for campus hiring",
            "TNP update: company recruitment drive",
            "Job opportunity for final year students",
        ],
        "senders": ["tnp cell", "placement office", "career services", "recruitment team"],
        "bodies": [
            "Applications are open for the internship program. Interested students should submit resumes through the placement portal.",
            "The company is conducting a recruitment drive next week. Eligible candidates must register before the deadline.",
            "Please review the job description and apply if you meet the criteria shared by the placement cell.",
            "A new opportunity is available for students in software, data, and product roles. Complete the form to participate.",
        ],
    },
    "spam": {
        "subjects": [
            "You won a reward",
            "Limited time cash prize",
            "Claim your free gift now",
            "Urgent account bonus available",
        ],
        "senders": ["promo desk", "reward center", "unknown sender", "offer alerts"],
        "bodies": [
            "Congratulations, you have been selected for a special cash prize. Click the link now to claim your reward.",
            "Act fast to receive a free gift card. This offer expires soon and requires immediate confirmation.",
            "Your account has a bonus waiting. Open the link and enter your details to unlock the offer.",
            "Exclusive deal available only today. Reply with your personal details to complete verification.",
        ],
    },
    "work": {
        "subjects": [
            "Project update and next steps",
            "Meeting notes from sprint review",
            "Client feedback on deliverables",
            "Engineering plan for next milestone",
        ],
        "senders": ["project manager", "engineering lead", "client partner", "team lead"],
        "bodies": [
            "Here are the notes from today's project meeting. The backend tasks are on track and design review is pending.",
            "The client approved the first milestone. Please continue with the implementation plan discussed in the sync.",
            "Sharing the updated roadmap, owners, and timelines for the next sprint.",
            "We need to align on requirements, blockers, and delivery dates during tomorrow's team call.",
        ],
    },
    "personal": {
        "subjects": [
            "Dinner plans this weekend",
            "Family event reminder",
            "Quick personal update",
            "Photos from the trip",
        ],
        "senders": ["friend", "family member", "roommate", "college friend"],
        "bodies": [
            "Are you free this weekend for dinner? Let me know what time works for you.",
            "Just reminding you about the family event on Sunday. Everyone is planning to arrive by noon.",
            "I uploaded the photos from our trip. Check them when you get time.",
            "Hope your week is going well. Call me when you are free so we can catch up.",
        ],
    },
}


DETAILS = [
    "Please keep this thread updated.",
    "I have included the relevant details below.",
    "Let me know if anything is unclear.",
    "This should help with planning the next step.",
    "Thanks for checking this when possible.",
]


def make_email(label: str, index: int, rng: random.Random) -> dict[str, str]:
    scenario = SCENARIOS[label]
    subject = rng.choice(scenario["subjects"])
    sender = rng.choice(scenario["senders"])
    body = rng.choice(scenario["bodies"])
    detail = rng.choice(DETAILS)
    day = rng.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    reference = f"Reference ID: {label[:3].upper()}-{index:03d}"
    text = (
        f"From: {sender}\n"
        f"Subject: {subject}\n\n"
        f"Hi,\n\n"
        f"{body}\n\n"
        f"{detail} Target day: {day}.\n\n"
        f"{reference}"
    )
    return {"text": text, "label": label}


def generate_examples(per_label: int, seed: int) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    for label in LABELS:
        for index in range(1, per_label + 1):
            rows.append(make_email(label, index, rng))
    rng.shuffle(rows)
    return rows


def write_jsonl(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=True) + "\n")


def merge_jsonl(sources: list[Path], target: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as output:
        for source in sources:
            with source.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    counts[str(row["label"])] += 1
                    output.write(json.dumps(row, ensure_ascii=True) + "\n")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate balanced synthetic classifier emails and merge with Kaggle data.")
    parser.add_argument("--per-label", type=int, default=200)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--synthetic-file", default="ml/data/processed/classifier_synthetic_200_each.jsonl")
    parser.add_argument("--base-file", default="ml/data/processed/classifier_train_kaggle.jsonl")
    parser.add_argument("--combined-file", default="ml/data/processed/classifier_train_kaggle_synthetic.jsonl")
    args = parser.parse_args()

    synthetic_file = Path(args.synthetic_file)
    base_file = Path(args.base_file)
    combined_file = Path(args.combined_file)

    if not base_file.exists():
        raise SystemExit(f"Base training file not found: {base_file}")

    synthetic_rows = generate_examples(per_label=args.per_label, seed=args.seed)
    write_jsonl(synthetic_rows, synthetic_file)
    counts = merge_jsonl([base_file, synthetic_file], combined_file)

    print(f"Synthetic file: {synthetic_file}")
    print(f"Combined file: {combined_file}")
    print(f"Synthetic examples: {len(synthetic_rows)}")
    print(f"Combined examples: {sum(counts.values())}")
    print("Combined label counts:")
    for label in LABELS:
        print(f"- {label}: {counts[label]}")


if __name__ == "__main__":
    main()
