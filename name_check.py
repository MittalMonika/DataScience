import re
from text_utils import normalize_text, fuzzy_token_set

EN_SENDER_KEYS = [
    r"\bSender\s*ID\b", r"\bSender\b", r"\bCustomer\s*ID\b", r"\bAccount\s*ID\b",
    r"\bFrom:\b", r"\bSender\s*Name\b", r"\bCustomer\s*Name\b"
]

def find_sender_blocks(page_text: str) -> list[str]:
    lines = [l.strip() for l in page_text.splitlines() if l.strip()]
    blocks = []
    for i, line in enumerate(lines):
        for pat in EN_SENDER_KEYS:
            if re.search(pat, line, flags=re.IGNORECASE):
                ctx = lines[max(0, i-1):min(len(lines), i+3)]
                blocks.append("\n".join(ctx))
                break
    return blocks

def extract_best_name_candidate(blocks: list[str]) -> str | None:
    if not blocks: return None
    label_words = {"sender","customer","account","id","name","from"}
    candidates = []
    for b in blocks:
        for line in b.splitlines():
            n = normalize_text(line)
            if not n: continue
            if any(w in n.split() for w in label_words) and len(n.split()) <= 3:
                continue
            alpha_tokens = sum(t.isalpha() for t in n.split())
            if alpha_tokens >= 2:
                candidates.append(line.strip())
    return max(candidates, key=len) if candidates else None

def verify_name_on_page(page_text: str, customer_name: str, pass_threshold=85):
    blocks = find_sender_blocks(page_text)
    extracted = extract_best_name_candidate(blocks) or ""
    score = fuzzy_token_set(extracted, customer_name) if extracted else 0
    return {
        "extracted_name": extracted,
        "match_score": score,
        "pass": bool(score >= pass_threshold),
        "snippet": "\n---\n".join(blocks)[:500]
    }
