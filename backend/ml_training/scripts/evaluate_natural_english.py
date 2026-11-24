"""Evaluate report descriptions against a publisher's service categories."""
import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from sklearn.metrics import classification_report

from backend.app.ml.predict import load_text, predict_text
from backend.app.ml.text_features import normalize
from backend.app.privacy import redact_contact

LABELS = {
    "Potholes":"Road", "Street Lamp":"Electricity", "Illegal Dumping":"Waste",
    "Missed Trash/Recycling":"Waste", "Yard Waste":"Waste",
}

def evaluate(snapshot):
    model = load_text()
    if not model:
        raise ValueError("Packaged trained model required")
    rows = json.loads(snapshot.read_text())["issues"]
    seen = set()
    truth, predictions, source_counts = [], [], Counter()
    for row in rows:
        if row.get("private_visibility") or not row.get("description"):
            continue
        title = (row.get("request_type") or {}).get("title")
        if title not in LABELS:
            continue
        description = redact_contact(row["description"]).strip()
        if len(re.findall(r"[A-Za-z]+",description)) < 5:
            continue
        key = normalize(description)
        if key in seen:
            continue
        seen.add(key)
        result = predict_text(model, description, "English")
        truth.append(LABELS[title])
        predictions.append(result["category"]["label"] if result else "Abstained")
        source_counts[title] += 1
    if not truth:
        raise ValueError("No eligible reports with a mapped category label")
    report = classification_report(truth,predictions,labels=sorted(set(truth)),zero_division=0,output_dict=True)
    return {
        "source":"https://seeclickfix.com/api/v2/issues?place_url=new-haven&per_page=100",
        "attribution":"SeeClickFix.com (CC BY-NC-SA 3.0 US)",
        "snapshot_sha256":hashlib.sha256(snapshot.read_bytes()).hexdigest(),
        "scope":"Naturally authored New Haven complaints; external category benchmark only. No severity labels.",
        "rows_read":len(rows), "count":len(truth), "category_counts":dict(Counter(truth)),
        "source_category_counts":dict(source_counts),
        "model_categories":list(model["tasks"]["category"]["classifier"].classes_),
        "accuracy":sum(a==b for a,b in zip(truth,predictions,strict=True))/len(truth),
        "macro_f1_over_supported_reference_categories":report["macro avg"]["f1-score"],
        "per_category":{key:report[key] for key in sorted(set(truth))},
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.dumps(evaluate(args.snapshot), indent=2) + "\n"
    args.output.write_text(report)
    print(report)
