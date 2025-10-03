from ocr_utils import load_pdf_page_as_image, preprocess_page_for_text, ocr_text_flat
from text_utils import normalize_text

SPANISH_CUES = [
    "remitente", "identificacion del remitente", "emisor", "firma", "firmado",
    "ciudad", "pais", "direccion", "estado", "telefono"
]

def detect_bilingual(reader, pdf_path) -> bool:
    """Return True if English+Spanish, else False. 
    Heuristic: scan Page 2 (index 1) for Spanish cues.
    """
    try:
        img2 = load_pdf_page_as_image(pdf_path, 1)
    except Exception:
        return False
    th2 = preprocess_page_for_text(img2)
    text2 = ocr_text_flat(reader, th2)
    t = normalize_text(text2)
    return any(cue in t for cue in SPANISH_CUES)
