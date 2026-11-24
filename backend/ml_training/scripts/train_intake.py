import argparse
import csv
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import make_pipeline


BACKEND = Path(__file__).resolve().parents[2]


def pipeline():
    return make_pipeline(
        TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=1000,
                        min_df=2, sublinear_tf=True),
        LogisticRegression(C=5, max_iter=600, class_weight="balanced"),
    )


def train(source):
    with source.open(encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle))
    examples = [row["text"] for row in records]
    result = {"version": "intake-nlp-1", "training_rows": len(records), "heads": {}}
    for target in ("sentiment", "risk"):
        answers = [row[target] for row in records]
        model = pipeline()
        folds = StratifiedKFold(n_splits=3, shuffle=True, random_state=19)
        scores = cross_val_score(model, examples, answers, cv=folds, scoring="f1_macro")
        model.fit(examples, answers)
        vectorizer, classifier = model.steps[0][1], model.steps[1][1]
        result["heads"][target] = {
            "labels": classifier.classes_.tolist(), "tokens": vectorizer.get_feature_names_out().tolist(),
            "idf": vectorizer.idf_.round(6).tolist(), "weights": classifier.coef_.round(6).tolist(),
            "bias": classifier.intercept_.round(6).tolist(), "synthetic_cv_macro_f1": round(scores.mean(), 3),
        }
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=BACKEND / "ml_training/data/intake_examples.csv")
    parser.add_argument("--output", type=Path, default=BACKEND / "app/ml/intake_model.json")
    args = parser.parse_args()
    args.output.write_text(json.dumps(train(args.data), ensure_ascii=False, separators=(",", ":")) + "\n",
                           encoding="utf-8")
