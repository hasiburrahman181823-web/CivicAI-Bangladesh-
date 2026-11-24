"""Train and temperature-calibrate separate category and severity classifiers."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from openpyxl import load_workbook
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, log_loss
from sklearn.model_selection import StratifiedGroupKFold

from backend.app.ml.text_features import normalize, romanize

CATEGORY = {"Healthcare": "Health", "Road & Transport": "Road"}
SOURCE = "https://doi.org/10.17632/w6c4zx5t2s.1"

def read_data(workbook):
    with workbook.open("rb") as source:
        book = load_workbook(source, read_only=True, data_only=True)
        rows = book.active.values
        headers = [str(x).strip() for x in next(rows)]
        fields = [headers.index(name) for name in ("Grievance Text", "Category", "Severity")]
        data = []
        for index, row in enumerate(rows, start=2):
            values = [row[i] for i in fields]
            if all(value is not None and str(value).strip() for value in values):
                sentence, category, severity = (str(value).strip() for value in values)
                data.append((index, sentence, CATEGORY.get(category, category), severity))
        book.close()
    return data

def expected_calibration_error(probs, truth, classes):
    confidence = probs.max(axis=1)
    correct = classes[probs.argmax(axis=1)] == truth
    return float(sum(mask.mean() * abs(correct[mask].mean() - confidence[mask].mean())
                     for low, high in zip(np.arange(10)/10, np.arange(1, 11)/10)
                     if (mask := (confidence >= low) & ((confidence < high) | ((high == 1) & (confidence == 1)))).any()))

def stats(logits, temperature, truth, classes):
    p = softmax(logits / temperature, axis=1)
    pred = classes[p.argmax(axis=1)]
    hot = np.equal.outer(truth, classes)
    return {"count": len(truth), "accuracy": float(accuracy_score(truth, pred)),
            "macro_f1": classification_report(truth, pred, labels=classes, output_dict=True, zero_division=0)["macro avg"]["f1-score"],
            "log_loss": float(log_loss(truth, p, labels=classes)),
            "brier_multiclass": float(np.mean(np.sum((p-hot)**2, axis=1))),
            "ece_top_label_10_bins": expected_calibration_error(p, truth, classes)}

def train(args):
    data = read_data(args.workbook)
    ids, natural, cat, sev = map(list, zip(*data, strict=True))
    cat, sev = np.asarray(cat), np.asarray(sev)
    group = np.asarray([hashlib.sha256(normalize(value).encode()).hexdigest() for value in natural])
    assert len(set(group)) >= 10
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42).split(natural, cat, group))
    valid, test = folds[0][1], folds[1][1]
    training = np.setdiff1d(np.arange(len(data)), np.r_[valid, test])
    assert not set(group[training]) & set(group[valid])
    assert not set(group[training]) & set(group[test])
    assert not set(group[valid]) & set(group[test])
    views = {"natural_bangla": natural, "derived_banglish": [romanize(x) for x in natural]}
    if args.english:
        with args.english.open(encoding="utf-8-sig", newline="") as f:
            table = {int(row["row_id"]): row["english"].strip() for row in csv.DictReader(f)}
        views["derived_english"] = [table.get(i, "") for i in ids]
    samples, indices = [], []
    for corpus in views.values():
        for i in training:
            if corpus[i]:
                samples.append(corpus[i])
                indices.append(i)
    vectorizer = TfidfVectorizer(preprocessor=normalize, analyzer="char", ngram_range=(2, 5),
                                 min_df=2, max_features=65000, sublinear_tf=True, dtype=np.float32)
    matrix = vectorizer.fit_transform(samples)
    args.output.mkdir(parents=True, exist_ok=True)
    bundle = {"vectorizer": vectorizer, "tasks": {}, "source": SOURCE}
    report = {"source": SOURCE, "workbook_sha256": hashlib.sha256(args.workbook.read_bytes()).hexdigest(),
              "rows": len(data), "normalized_groups": len(set(group)),
              "split": {"train": len(training), "calibration": len(valid), "test": len(test)},
              "grouping": "Exact normalized source text; every derived variant inherits its original row split. Incident IDs unavailable.",
              "augmented_training_rows": len(samples), "tasks": {}}
    for task, labels in (("category", cat), ("severity", sev)):
        model = LogisticRegression(max_iter=350, C=5, random_state=42).fit(matrix, labels[indices])
        bundle["tasks"][task] = {"classifier": model, "temperature": {}}
        report["tasks"][task] = {}
        for cohort, corpus in views.items():
            cal_ids = [i for i in valid if corpus[i]]
            test_ids = [i for i in test if corpus[i]]
            if not cal_ids or not test_ids:
                continue
            cal = model.decision_function(vectorizer.transform([corpus[i] for i in cal_ids]))
            temp = float(minimize_scalar(lambda t: log_loss(labels[cal_ids], softmax(cal/t, axis=1), labels=model.classes_), bounds=(0.15, 6), method="bounded").x)
            logits = model.decision_function(vectorizer.transform([corpus[i] for i in test_ids]))
            report["tasks"][task][cohort] = {
                "temperature": temp, "raw": stats(logits, 1, labels[test_ids], model.classes_),
                "calibrated": stats(logits, temp, labels[test_ids], model.classes_)}
            bundle["tasks"][task]["temperature"][cohort] = temp
    joblib.dump(bundle, args.output / "text.joblib", compress=3)
    (args.output / "text_metrics.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--english", type=Path, help="Optional derived English CSV with row_id and english columns")
    parser.add_argument("--output", type=Path, required=True)
    train(parser.parse_args())
