import os
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from scipy.special import softmax

ARTIFACTS = Path(os.getenv("CIVICAI_ARTIFACTS", Path(__file__).resolve().parents[2] / "ml_training/artifacts"))

def load_text():
    file = ARTIFACTS / "text.joblib"
    return joblib.load(file) if file.is_file() else None

def predict_text(bundle, text, language):
    vectorizer = bundle["vectorizer"]
    features = vectorizer.transform([text])
    if features.nnz < 5:
        return None
    cohort = {"Bangla":"natural_bangla", "English":"derived_english", "Banglish":"derived_banglish"}[language]
    result = {}
    for task, artifact in bundle["tasks"].items():
        model = artifact["classifier"]
        logits = np.asarray(model.decision_function(features)).reshape(-1)
        index = int(logits.argmax())
        probabilities = softmax(logits / artifact["temperature"].get(cohort, 1))
        coefficients = model.coef_[index]
        contribution = sorted(zip(features.indices, features.data * coefficients[features.indices]),
                              key=lambda pair: pair[1], reverse=True)
        tokens = [str(x).strip() for x in vectorizer.get_feature_names_out()[[f for f, score in contribution if score > 0][:5]]]
        measured_on = cohort if cohort in artifact["temperature"] else None
        result[task] = {
            "label": str(model.classes_[index]),
            "confidence": round(float(probabilities[index]), 4) if measured_on == "natural_bangla" else None,
            "derived_cohort_score": round(float(probabilities[index]), 4) if measured_on and measured_on.startswith("derived") else None,
            "calibration_cohort": measured_on,
            "features": list(dict.fromkeys(tokens)),
        }
    return result

def predict_forecast(category, occurred_at):
    if os.getenv("ENABLE_EXTERNAL_FORECAST", "").lower() != "true":
        return None
    path = ARTIFACTS / "forecast.joblib"
    if not path.exists():
        return None
    return _predict_forecast(_forecast_model(path), category, occurred_at)

@lru_cache(maxsize=2)
def _forecast_model(path):
    return joblib.load(path)

def benchmark_forecast(category, occurred_at):
    path = ARTIFACTS / "forecast.joblib"
    if not path.is_file():
        return None
    return _predict_forecast(_forecast_model(path), category, occurred_at)

def _predict_forecast(artifact, category, occurred_at):
    from datetime import timedelta
    if category not in artifact["categories"]:
        return None
    from pandas import DataFrame
    local = occurred_at + timedelta(hours=6)
    features = DataFrame([{"category":category,"hour":local.hour,"weekday":local.weekday()}])
    values = sorted(round(max(0, float(model.predict(features)[0])), 1) for model in artifact["models"])
    return {"lower_hours":values[0], "estimated_hours":values[1], "upper_hours":values[2],
            "source":"NYC 311 historical benchmark", "scope":"External city benchmark, not calibrated for Bangladesh",
            "target":"Time from request creation to closure"}
