"""Evaluate the release triage policy against independently adjudicated priorities."""
import argparse
import csv
import json
from pathlib import Path

from scipy.stats import spearmanr
from sklearn.metrics import classification_report, cohen_kappa_score

from backend.app.ml.predict import load_text
from backend.app.services.analysis import analyze

LABELS=["Low","Medium","High","Critical"]

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    with args.csv.open(encoding="utf-8-sig",newline="") as handle:
        rows=list(csv.DictReader(handle))
    if not rows:
        raise SystemExit("Supply held-out, independently adjudicated priority labels first.")
    model=load_text()
    if model is None:
        raise SystemExit("Release text model is required.")
    report={}
    for cohort in ("natural","derived"):
        sample=[row for row in rows if row["source_type"]==cohort]
        if not sample:
            continue
        if any(row["reviewed_priority"] not in LABELS or not all(row[key].strip() for key in ["original_id","incident_id","review_ref","text"]) for row in sample):
            raise ValueError("Each label needs an original ID, incident ID and independent review reference")
        truth=[row["reviewed_priority"] for row in sample]
        hybrid=[analyze(row["text"],model,row["language"]) for row in sample]
        baseline=[analyze(row["text"],None,row["language"]) for row in sample]
        report[cohort]={}
        for name,suggestions in [("hybrid",hybrid),("rule_baseline",baseline)]:
            prediction=[value["priority"] for value in suggestions]
            correlation=spearmanr([LABELS.index(label) for label in truth],[value["score"] for value in suggestions]).statistic if len(set(truth))>1 and len({value["score"] for value in suggestions})>1 else None
            kappa=cohen_kappa_score(truth,prediction,labels=LABELS,weights="quadratic") if len(set(truth+prediction))>1 else None
            report[cohort][name]={"count": len(sample), "distinct_incidents":len({row["incident_id"] for row in sample}),
                                  "macro_f1":classification_report(truth,prediction,labels=LABELS,zero_division=0,output_dict=True)["macro avg"]["f1-score"],
                                  "ordinal_kappa":kappa,"rank_correlation":correlation}
    if not report:
        raise ValueError("Data must be marked natural or derived")
    args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
