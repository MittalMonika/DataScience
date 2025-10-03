from text_utils import normalize_text
from ocr_utils import ocr_text

SIG_LABELS_EN = ["customer signature", "signature", "authorized signature", "sign here", "signed"]
SIG_LABELS_ES = ["firma", "firma del cliente", "firmado", "firmar aqui", "firma aqui"]

def ocr_with_boxes(reader, img_bgr):
    return ocr_text(reader, img_bgr, detail=1, paragraph=False)

def find_label_boxes(ocr_boxes, language_hint='en', min_partial_score=70):
    labels = SIG_LABELS_ES if language_hint == 'es' else SIG_LABELS_EN
    labs_norm = [normalize_text(x) for x in labels]
    hits = []
    for bbox, text, conf in ocr_boxes:
        t = normalize_text(text)
        score = max(sum(1 for tok in ln.split() if tok in t.split())/max(1,len(ln.split())) for ln in labs_norm)
        score *= 100
        if score >= min_partial_score:
            hits.append((bbox, text, conf, score))
    hits.sort(key=lambda x: x[-1], reverse=True)
    return hits
