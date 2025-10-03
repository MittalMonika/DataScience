import cv2, numpy as np
from ocr_utils import expand_bbox
from label_detect import ocr_with_boxes, find_label_boxes

def inkiness_score(binary_roi):
    if binary_roi.dtype != np.uint8:
        binary_roi = binary_roi.astype(np.uint8)
    if binary_roi.max() <= 1:
        binary_roi = (binary_roi * 255).astype(np.uint8)
    inv = cv2.bitwise_not(binary_roi)
    contours, _ = cv2.findContours(inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    h, w = binary_roi.shape[:2]
    area_img = h*w if h*w>0 else 1
    good = 0; irregular = 0; total_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 40 or area > 0.12*area_img: 
            continue
        x,y,cw,ch = cv2.boundingRect(cnt)
        aspect = max(cw,ch)/(min(cw,ch)+1e-3)
        if aspect > 25: 
            continue
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)+1e-3
        solidity = area/hull_area
        perim = cv2.arcLength(cnt, True)
        complexity = perim/(np.sqrt(hull_area)+1e-3)
        total_area += area
        good += 1
        if solidity < 0.75 or complexity > 6.0:
            irregular += 1
    density = good/(np.sqrt(area_img)/25 + 1e-3)
    coverage = total_area/(area_img + 1e-3)
    irr_frac = irregular/(good + 1e-3)
    score = 0.7*density + 0.6*irr_frac + 0.4*coverage
    return float(score)

def detect_signature_in_roi(img_bgr, roi_rect):
    x,y,w,h = roi_rect
    H,W = img_bgr.shape[:2]
    x = max(0, min(x, W-1)); y = max(0, min(y, H-1))
    w = max(1, min(w, W-x)); h = max(1, min(h, H-y))
    roi = img_bgr[y:y+h, x:x+w]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    _, th_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    th_adap = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY, 35, 11)
    score = max(inkiness_score(th_otsu), inkiness_score(th_adap))
    return (score >= 0.8, score, (x,y,w,h))

def detect_signature_on_page(reader, img_bgr, language_hint='en'):
    boxes = ocr_with_boxes(reader, img_bgr)
    hits = find_label_boxes(boxes, language_hint=language_hint, min_partial_score=70)
    for bbox, text, conf, score in hits[:3]:
        x,y,w,h = expand_bbox(bbox, pad=8)
        roi_below = (x, y + int(1.1*h), w, int(2.2*h))
        found_b, score_b, rb = detect_signature_in_roi(img_bgr, roi_below)
        if found_b:
            return {"signature_found": True, "method": "label_roi_below", "score": score_b}
    H,W = img_bgr.shape[:2]
    bottom_h = max(80, int(0.30*H))
    roi_bottom = (int(0.08*W), H - bottom_h, int(0.84*W), bottom_h)
    found, s, rb = detect_signature_in_roi(img_bgr, roi_bottom)
    if found:
        return {"signature_found": True, "method": "bottom_zone", "score": s}
    return {"signature_found": False, "method": "none", "score": 0.0}
