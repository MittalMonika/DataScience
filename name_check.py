import re
from typing import List, Optional, Dict
from text_utils import normalize_text, fuzzy_token_set

# Your original patterns (kept so snippets still work)
EN_SENDER_KEYS = [
    r"\bSender\s*ID\b", r"\bSender\b", r"\bCustomer\s*ID\b", r"\bAccount\s*ID\b",
    r"\bFrom:\b", r"\bSender\s*Name\b", r"\bCustomer\s*Name\b"
]

# NEW: explicit "sender's name" style labels (colon optional)
SENDER_LABEL_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bSender(?:'s)?\s*Name\b\s*:?", re.IGNORECASE),
    re.compile(r"\bSender\b\s*:?", re.IGNORECASE),
    re.compile(r"\bFrom\b\s*:?", re.IGNORECASE),
    re.compile(r"\bOriginator\b\s*:?", re.IGNORECASE),
    re.compile(r"\bCustomer\s*Name\b\s*:?", re.IGNORECASE),
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

# ---------- helpers for robust extraction ----------

def _strip_label_same_line(line: str) -> str:
    """If a value is present on the SAME line after a sender label, return it."""
    for pat in SENDER_LABEL_PATTERNS:
        m = pat.search(line)
        if m:
            after = line[m.end():].strip(" :-\t")
            # Avoid returning empty/pure punctuation
            return after if normalize_text(after) else ""
    return ""

def _neighbor_window(lines: List[str], i: int, span: int = 3) -> List[str]:
    """Return a small window around index i (prev + next lines)."""
    start = max(0, i - 1)
    end = min(len(lines), i + span)
    return lines[start:end]

def _best_name_like_line(cands: List[str]) -> Optional[str]:
    """Prefer non-empty, alphabetic-heavy, longer lines; avoid pure labels."""
    cleaned = [c.strip() for c in cands if c and c.strip()]
    if not cleaned:
        return None
    label_words = {"sender","customer","account","id","name","from","originator"}
    best = ("", -1.0)
    for c in cleaned:
        n = normalize_text(c)
        alpha_tokens = sum(t.isalpha() for t in n.split())
        # downweight short label-only lines
        if any(w in n.split() for w in label_words) and len(n.split()) <= 3:
            score = 0
        else:
            score = alpha_tokens * 2 + len(c) * 0.02
        if score > best[1]:
            best = (c, score)
    return best[0] if best[1] > 0 else None

def _find_sender_hits(lines: List[str]) -> List[int]:
    """Line indices that contain sender-like labels."""
    hits = []
    for i, line in enumerate(lines):
        if any(p.search(line) for p in SENDER_LABEL_PATTERNS):
            hits.append(i)
    # fallback: loose 'sender'
    if not hits:
        for i, line in enumerate(lines):
            if re.search(r"\bsender(?:'s)?\b", line, flags=re.IGNORECASE):
                hits.append(i)
    return hits

# Your original block-based extractor (kept as fallback)
def extract_best_name_candidate(blocks: list[str]) -> Optional[str]:
    if not blocks:
        return None
    label_words = {"sender","customer","account","id","name","from"}
    candidates = []
    for b in blocks:
        for line in b.splitlines():
            n = normalize_text(line)
            if not n:
                continue
            if any(w in n.split() for w in label_words) and len(n.split()) <= 3:
                continue
            alpha_tokens = sum(t.isalpha() for t in n.split())
            if alpha_tokens >= 2:
                candidates.append(line.strip())
    return max(candidates, key=len) if candidates else None

def _extract_sender_name(page_text: str) -> Dict[str, str]:
    """
    Primary extractor:
      1) same line after label
      2) neighbor lines (next best)
      3) fallback: longest alpha-ish line on page
    Returns {'extracted': <str>, 'source': 'same_line'|'next_line'|'fallback'}.
    """
    lines = page_text.splitlines()
    hits = _find_sender_hits(lines)

    for i in hits:
        same = _strip_label_same_line(lines[i])
        if same:
            return {"extracted": same, "source": "same_line"}
        neigh = [l for l in _neighbor_window(lines, i, span=3) if l is not lines[i]]
        best = _best_name_like_line(neigh)
        if best:
            return {"extracted": best, "source": "next_line"}

    # final fallback if labels OCR poorly
    best_any = _best_name_like_line(lines)
    return {"extracted": best_any or "", "source": "fallback"}

# ---------- public API (unchanged) ----------

def verify_name_on_page(page_text: str, customer_name: str, pass_threshold=85):
    """
    Extracts the Sender's name value from the page text and
    fuzzy-compares it to `customer_name`.
    Returns:
      {
        "extracted_name": str,
        "match_score": int (0..100),
        "pass": bool,
        "snippet": str
      }
    """
    # Try robust extractor first
    ext = _extract_sender_name(page_text)
    extracted = ext.get("extracted", "").strip()

    # If that failed, fall back to your block-based pick so behavior stays compatible
    blocks = find_sender_blocks(page_text)
    if not extracted:
        extracted = extract_best_name_candidate(blocks) or ""

    score = fuzzy_token_set(extracted, customer_name) if extracted else 0
    return {
        "extracted_name": extracted,
        "match_score": score,
        "pass": bool(score >= pass_threshold),
        "snippet": "\n---\n".join(blocks)[:500] if blocks else ""
    }

from name_check import verify_name_on_page
page = "Sender's Name: Acme Corporation LLC\nAddress: 123 Main St"
print(verify_name_on_page(page, "Acme Corporation LLC"))
# -> extracted_name='Acme Corporation LLC', high match_score, pass=True


