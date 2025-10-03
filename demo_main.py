import argparse
import pandas as pd
from pathlib import Path

from ocr_utils import make_reader
from pipeline import process_document

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV with columns: customer_name, document_id")
    ap.add_argument("--pdf-dir", required=True, help="folder containing <document_id>.pdf")
    ap.add_argument("--out", default="results.csv", help="output CSV path")
    ap.add_argument("--gpu", action="store_true", help="use GPU for EasyOCR")
    args = ap.parse_args()

    reader = make_reader(gpu=args.gpu)

    df = pd.read_csv(args.csv)
    rows = []
    for _, row in df.iterrows():
        cust = str(row.get("customer_name","")).strip()
        docid = str(row.get("document_id","")).strip()
        pdf_path = Path(args.pdf_dir) / f"{docid}.pdf"
        if not pdf_path.exists():
            rows.append({"document_id": docid, "customer_name": cust, "status": "PDF_NOT_FOUND"})
            continue
        try:
            res = process_document(reader, str(pdf_path), cust)
            rows.append({"document_id": docid, "customer_name": cust, "status": "OK", **res})
        except Exception as e:
            rows.append({"document_id": docid, "customer_name": cust, "status": f"ERROR: {e}"})
    out = pd.DataFrame(rows)
    out.to_csv(args.out, index=False)
    print(f"Wrote {args.out} with {len(rows)} rows.")

if __name__ == "__main__":
    main()
