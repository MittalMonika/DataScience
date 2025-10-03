from pathlib import Path
from ocr_utils import make_reader, load_pdf_page_as_image, preprocess_page_for_text, ocr_text_flat
from lang_detect import detect_bilingual
from signature_detect import detect_signature_on_page
from name_check import verify_name_on_page

def process_document(reader, pdf_path: str, customer_name: str, name_pass_threshold=85):
    pdf_path = Path(pdf_path)
    bilingual = detect_bilingual(reader, pdf_path)

    sig_pages = [0,1] if bilingual else [0]
    signature_checks = []
    for pidx in sig_pages:
        img = load_pdf_page_as_image(pdf_path, pidx)
        lang_hint = 'es' if (bilingual and pidx==1) else 'en'
        sig = detect_signature_on_page(reader, img, language_hint=lang_hint)
        signature_checks.append({"page": pidx+1, **sig})
    signature_present = any(r.get("signature_found") for r in signature_checks)

    sender_pidx = 2 if bilingual else 1
    img_sender = load_pdf_page_as_image(pdf_path, sender_pidx)
    txt_sender = ocr_text_flat(reader, preprocess_page_for_text(img_sender))
    name_res = verify_name_on_page(txt_sender, customer_name, pass_threshold=name_pass_threshold)

    return {
        "bilingual": bilingual,
        "signature_pages_checked": [p+1 for p in sig_pages],
        "signature_present": signature_present,
        "signature_checks": signature_checks,
        "name_check_page": sender_pidx+1,
        **name_res
    }
