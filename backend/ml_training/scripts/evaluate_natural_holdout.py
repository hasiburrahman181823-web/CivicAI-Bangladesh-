"""Evaluate independently labeled, naturally authored complaint texts."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from sklearn.metrics import classification_report

from backend.app.ml.predict import load_text, predict_text
from backend.app.privacy import redact_contact

LANGUAGES={"Bangla","English","Banglish"}

def evaluate(path):
    model=load_text()
    if model is None:
        raise ValueError("The frozen release text model is required")
    cohorts=defaultdict(list)
    seen=set()
    with path.open(encoding="utf-8-sig",newline="") as file:
        for row in csv.DictReader(file):
            if row["source_type"]!="natural" or row["language"] not in LANGUAGES:
                raise ValueError("Natural cohorts require independently authored, reviewed language labels")
            if not all(row[key].strip() for key in ("original_id","incident_id","review_ref","text","category")):
                raise ValueError("Original IDs, incident IDs and independent label references are required")
            key=row["original_id"]
            if key in seen:
                raise ValueError("Only one native observation per original is allowed")
            seen.add(key)
            prediction=predict_text(model,redact_contact(row["text"]),row["language"])
            cohorts[row["language"]].append((row,prediction))
    if not cohorts:
        raise ValueError("No independently labeled natural reports")
    report={}
    for lang, results in cohorts.items():
        item={"rows":len(results),"incident_groups":len({row["incident_id"] for row,_ in results})}
        for task in ("category","severity"):
            labeled=[(row,prediction) for row,prediction in results if row[task].strip()]
            if labeled:
                actual=[row[task] for row,_ in labeled]
                guesses=[pred[task]["label"] if pred else "Abstained" for _,pred in labeled]
                item[task]=classification_report(actual,guesses,labels=sorted(set(actual)),
                                                zero_division=0,output_dict=True)
        report[lang]=item
    return report

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.write_text(json.dumps(evaluate(args.csv),indent=2)+"\n")
