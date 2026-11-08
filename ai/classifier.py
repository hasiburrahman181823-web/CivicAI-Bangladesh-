"""
CivicAI Bangladesh - AI Classifier Engine
Loads trained models for Category Classification and Severity Prediction.
Provides prediction with calibrated confidence scores and alternative classes.
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, List
from ai.nlp_preprocessor import normalize_text

class ComplaintClassifier:
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
        self.models_dir = models_dir

        vec_path = os.path.join(models_dir, "vectorizer.joblib")
        cat_path = os.path.join(models_dir, "category_model.joblib")
        sev_path = os.path.join(models_dir, "severity_model.joblib")

        if not (os.path.exists(vec_path) and os.path.exists(cat_path) and os.path.exists(sev_path)):
            raise FileNotFoundError(
                f"Model artifacts missing in {models_dir}. Please run training/train_models.py first."
            )

        self.vectorizer = joblib.load(vec_path)
        self.cat_model = joblib.load(cat_path)
        self.sev_model = joblib.load(sev_path)

        self.cat_classes = list(self.cat_model.classes_)
        self.sev_classes = list(self.sev_model.classes_)

    def predict(self, title: str, description: str) -> Dict[str, Any]:
        combined_text = normalize_text(f"{title} {description}")
        vec = self.vectorizer.transform([combined_text])

        # Category prediction
        cat_probs = self.cat_model.predict_proba(vec)[0]
        cat_idx = int(np.argmax(cat_probs))
        predicted_category = self.cat_classes[cat_idx]
        cat_confidence = round(float(cat_probs[cat_idx]), 4)

        # Ranked categories
        top_cats = sorted(
            [{"category": cls, "confidence": round(float(prob), 4)} for cls, prob in zip(self.cat_classes, cat_probs)],
            key=lambda x: x["confidence"],
            reverse=True
        )[:3]

        # Severity prediction
        sev_probs = self.sev_model.predict_proba(vec)[0]
        sev_idx = int(np.argmax(sev_probs))
        predicted_severity = self.sev_classes[sev_idx]
        sev_confidence = round(float(sev_probs[sev_idx]), 4)

        # Ranked severities
        top_sevs = sorted(
            [{"severity": cls, "confidence": round(float(prob), 4)} for cls, prob in zip(self.sev_classes, sev_probs)],
            key=lambda x: x["confidence"],
            reverse=True
        )

        return {
            "category": predicted_category,
            "category_confidence": cat_confidence,
            "top_categories": top_cats,
            "severity": predicted_severity,
            "severity_confidence": sev_confidence,
            "top_severities": top_sevs
        }
