"""
CivicAI Bangladesh - Model Training & Evaluation Engine
Trains Category Classification and Severity Prediction models using
multilingual word and sub-word character n-gram feature representations.
Evaluates across Bangla, English, and Banglish test sets.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    classification_report,
    confusion_matrix
)

from ai.nlp_preprocessor import normalize_text

def train_and_evaluate():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(base_dir, "datasets")
    models_dir = os.path.join(base_dir, "ai", "models")
    os.makedirs(models_dir, exist_ok=True)

    print("Loading datasets...")
    train_df = pd.read_csv(os.path.join(datasets_dir, "train.csv"))
    val_df = pd.read_csv(os.path.join(datasets_dir, "val.csv"))
    test_df = pd.read_csv(os.path.join(datasets_dir, "test.csv"))

    # Prepare composite text (title + description)
    def prepare_text(df):
        return (df["title"].fillna("") + " " + df["description"].fillna("")).apply(normalize_text)

    X_train_raw = prepare_text(train_df)
    X_val_raw = prepare_text(val_df)
    X_test_raw = prepare_text(test_df)

    y_cat_train = train_df["category"]
    y_cat_val = val_df["category"]
    y_cat_test = test_df["category"]

    y_sev_train = train_df["severity"]
    y_sev_val = val_df["severity"]
    y_sev_test = test_df["severity"]

    print(f"Training samples: {len(X_train_raw)}")
    print(f"Validation samples: {len(X_val_raw)}")
    print(f"Test samples: {len(X_test_raw)}")

    # Dual feature union: Word n-grams (1, 2) + Character n-grams (3, 5)
    # This guarantees robust representation for Bangla morphological forms and Banglish phonetic variations
    print("\nExtracting Multilingual Word + Subword Character N-Gram Features...")
    word_vec = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=8000,
        sublinear_tf=True
    )
    char_vec = TfidfVectorizer(
        analyzer='char_wb',
        ngram_range=(3, 5),
        max_features=12000,
        sublinear_tf=True
    )
    vectorizer = FeatureUnion([
        ('word', word_vec),
        ('char', char_vec)
    ])

    X_train_vec = vectorizer.fit_transform(X_train_raw)
    X_val_vec = vectorizer.transform(X_val_raw)
    X_test_vec = vectorizer.transform(X_test_raw)

    print(f"Feature dimension: {X_train_vec.shape[1]}")

    # ==========================================
    # 1. Train Category Classifier
    # ==========================================
    print("\n--- Training Model 1: Civic Category Classifier ---")
    cat_base = LogisticRegression(
        C=2.5,
        max_iter=1000,
        class_weight='balanced',
        random_state=42
    )
    cat_model = CalibratedClassifierCV(estimator=cat_base, cv=3)
    cat_model.fit(X_train_vec, y_cat_train)

    # Evaluate on Validation and Test
    val_cat_preds = cat_model.predict(X_val_vec)
    test_cat_preds = cat_model.predict(X_test_vec)

    cat_acc = accuracy_score(y_cat_test, test_cat_preds)
    cat_p, cat_r, cat_f1, _ = precision_recall_fscore_support(
        y_cat_test, test_cat_preds, average='macro', zero_division=0
    )

    print(f"Category Classifier Overall Test Results:")
    print(f"Accuracy:  {cat_acc:.4f}")
    print(f"Precision: {cat_p:.4f}")
    print(f"Recall:    {cat_r:.4f}")
    print(f"Macro F1:  {cat_f1:.4f}")

    cat_classes = list(cat_model.classes_)
    cat_cm = confusion_matrix(y_cat_test, test_cat_preds, labels=cat_classes)

    # ==========================================
    # 2. Train Severity Classifier
    # ==========================================
    print("\n--- Training Model 2: Severity Predictor ---")
    sev_base = LogisticRegression(
        C=2.0,
        max_iter=1000,
        class_weight='balanced',
        random_state=42
    )
    sev_model = CalibratedClassifierCV(estimator=sev_base, cv=3)
    sev_model.fit(X_train_vec, y_sev_train)

    val_sev_preds = sev_model.predict(X_val_vec)
    test_sev_preds = sev_model.predict(X_test_vec)

    sev_acc = accuracy_score(y_sev_test, test_sev_preds)
    sev_p, sev_r, sev_f1, _ = precision_recall_fscore_support(
        y_sev_test, test_sev_preds, average='macro', zero_division=0
    )

    print(f"Severity Predictor Overall Test Results:")
    print(f"Accuracy:  {sev_acc:.4f}")
    print(f"Precision: {sev_p:.4f}")
    print(f"Recall:    {sev_r:.4f}")
    print(f"Macro F1:  {sev_f1:.4f}")

    sev_classes = list(sev_model.classes_)
    sev_cm = confusion_matrix(y_sev_test, test_sev_preds, labels=sev_classes)

    # ==========================================
    # 3. Per-Language Evaluation (Bangla, English, Banglish)
    # ==========================================
    print("\n--- Evaluating Models across Bangla, English, and Banglish ---")
    per_language_metrics = {}

    for lang_code, lang_name in [("bn", "Bangla"), ("en", "English"), ("bn-en", "Banglish")]:
        mask = (test_df["language"] == lang_code).values
        if np.sum(mask) == 0:
            continue

        X_lang_vec = vectorizer.transform(X_test_raw[mask])
        y_cat_lang = y_cat_test[mask]
        y_sev_lang = y_sev_test[mask]

        preds_cat = cat_model.predict(X_lang_vec)
        preds_sev = sev_model.predict(X_lang_vec)

        l_cat_acc = accuracy_score(y_cat_lang, preds_cat)
        _, _, l_cat_f1, _ = precision_recall_fscore_support(
            y_cat_lang, preds_cat, average='macro', zero_division=0
        )

        l_sev_acc = accuracy_score(y_sev_lang, preds_sev)
        _, _, l_sev_f1, _ = precision_recall_fscore_support(
            y_sev_lang, preds_sev, average='macro', zero_division=0
        )

        per_language_metrics[lang_name] = {
            "samples": int(np.sum(mask)),
            "category_accuracy": round(float(l_cat_acc), 4),
            "category_macro_f1": round(float(l_cat_f1), 4),
            "severity_accuracy": round(float(l_sev_acc), 4),
            "severity_macro_f1": round(float(l_sev_f1), 4),
        }

        print(f"[{lang_name}] N={np.sum(mask)} | Cat Acc: {l_cat_acc:.4f}, Cat F1: {l_cat_f1:.4f} | Sev Acc: {l_sev_acc:.4f}, Sev F1: {l_sev_f1:.4f}")

    # ==========================================
    # 4. Save Model Artifacts
    # ==========================================
    print("\nSaving trained models and evaluation artifacts...")
    joblib.dump(vectorizer, os.path.join(models_dir, "vectorizer.joblib"))
    joblib.dump(cat_model, os.path.join(models_dir, "category_model.joblib"))
    joblib.dump(sev_model, os.path.join(models_dir, "severity_model.joblib"))

    evaluation_report = {
        "model_version": "v1.2.0-BanglaPSG",
        "training_timestamp": "2026-11-08T10:00:00Z",
        "total_train_samples": len(X_train_raw),
        "total_test_samples": len(X_test_raw),
        "feature_count": X_train_vec.shape[1],
        "category_metrics": {
            "accuracy": round(float(cat_acc), 4),
            "precision_macro": round(float(cat_p), 4),
            "recall_macro": round(float(cat_r), 4),
            "macro_f1": round(float(cat_f1), 4),
            "classes": cat_classes
        },
        "severity_metrics": {
            "accuracy": round(float(sev_acc), 4),
            "precision_macro": round(float(sev_p), 4),
            "recall_macro": round(float(sev_r), 4),
            "macro_f1": round(float(sev_f1), 4),
            "classes": sev_classes
        },
        "per_language_performance": per_language_metrics
    }

    with open(os.path.join(models_dir, "evaluation_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(evaluation_report, f, indent=2)

    confusion_matrices = {
        "category": {
            "labels": cat_classes,
            "matrix": cat_cm.tolist()
        },
        "severity": {
            "labels": sev_classes,
            "matrix": sev_cm.tolist()
        }
    }

    with open(os.path.join(models_dir, "confusion_matrices.json"), "w", encoding="utf-8") as f:
        json.dump(confusion_matrices, f, indent=2)

    print("All models and metrics successfully saved to ai/models/.")
    return evaluation_report

if __name__ == "__main__":
    train_and_evaluate()
