from pathlib import Path
import fitz
import numpy as np
import cv2
import easyocr

def make_reader(langs=('en','es'), gpu=False):
    return easyocr.Reader(list(langs), gpu=gpu)

def load_pdf_page_as_image(pdf_path, page_index_0: int, dpi: int = 350):
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        page = doc[page_index_0]
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        return img

def preprocess_page_for_text(img_bgr):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3,3), 0)
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 35, 11)
    return th

def ocr_text(reader, img_or_binary, detail=0, paragraph=True):
    return reader.readtext(img_or_binary, detail=detail, paragraph=paragraph)

def ocr_text_flat(reader, img_or_binary):
    lines = reader.readtext(img_or_binary, detail=0, paragraph=True)
    return "\n".join(lines)

def expand_bbox(bbox, pad=12):
    xs = [p[0] for p in bbox]
    ys = [p[1] for p in bbox]
    x0, y0 = max(int(min(xs))-pad, 0), max(int(min(ys))-pad, 0)
    x1, y1 = int(max(xs))+pad, int(max(ys))+pad
    return x0, y0, max(1, x1-x0), max(1, y1-y0)
