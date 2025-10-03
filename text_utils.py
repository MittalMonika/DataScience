import re, string, unicodedata
from rapidfuzz import fuzz

def strip_accents(s: str) -> str:
    if s is None:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

def normalize_text(s: str) -> str:
    s = (s or "")
    s = strip_accents(s).lower()
    allowed = set(string.ascii_lowercase + string.digits + " ")
    s = ''.join(ch if ch in allowed else " " for ch in s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fuzzy_token_set(a: str, b: str) -> int:
    return fuzz.token_set_ratio(normalize_text(a), normalize_text(b))
