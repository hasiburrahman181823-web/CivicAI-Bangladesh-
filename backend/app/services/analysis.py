import math
from datetime import timezone

from ..ml.predict import predict_text, predict_forecast
import re

CATEGORIES = {
    'Water': ['water', 'পানি', 'pani', 'pipe', 'পাইপ', 'পানির'],
    'Electricity': ['electric', 'বিদ্যুৎ', 'bidyut', 'current', 'কারেন্ট', 'wire'],
    'Road': ['road', 'রাস্তা', 'rasta', 'pothole', 'সড়ক', 'গর্ত'],
    'Waste': ['waste', 'garbage', 'বর্জ্য', 'ময়লা', 'moyla', 'drain', 'নর্দমা'],
    'Health': ['health', 'hospital', 'হাসপাতাল', 'স্বাস্থ্য', 'clinic', 'ambulance'],
    'Gas': ['gas', 'গ্যাস'],
    'Safety': ['crime', 'আগুন', 'fire', 'বিপদ', 'চুরি', 'danger', 'accident'],
}

def analyze(text, category_model=None, language="English", occurred_at=None):
    normalized = text.lower()
    matches = {category: [word for word in words if word in normalized] for category, words in CATEGORIES.items()}
    category = max(matches, key=lambda key: len(matches[key]))
    if not matches[category]:
        category = 'Other'
    prediction = predict_text(category_model, text, language) if category_model else None
    if prediction:
        category_label = prediction["category"]["label"]
        # Preserve categories outside the training label set when explicit cues exist.
        if category not in {"Gas", "Safety"}:
            category = category_label
        else:
            prediction["category"]["policy_override"] = category
    severity = prediction["severity"]["label"] if prediction else None
    base = {"Low": 20, "Medium": 35, "High": 55}.get(severity, 20)
    evidence = []
    score = base
    for name, words, points in [
        ('Immediate safety cue', ['fire', 'আগুন', 'exposed wire', 'gas leak', 'গ্যাস লিক', 'injured'], 45),
        ('Essential service disruption', ['no water', 'পানি নেই', 'pani nai', 'power outage', 'বিদ্যুৎ নেই'], 20),
        ('Sensitive facility mentioned', ['school', 'hospital', 'স্কুল', 'হাসপাতাল'], 10),
        ('Extended disruption mentioned', ['days', 'দিন', 'din dhore', 'week'], 10),
    ]:
        found = [word for word in words if word in normalized]
        if found:
            score += points
            evidence.append({'label': name, 'points': points, 'keywords': found})
    score = min(score, 100)
    forecast = predict_forecast(category, occurred_at) if occurred_at else None
    category_confidence = prediction["category"]["confidence"] if prediction and not prediction["category"].get("policy_override") else None
    low_confidence = category_confidence is None or category_confidence < .70
    if prediction:
        severity_confidence = prediction["severity"]["confidence"]
        low_confidence = low_confidence or severity_confidence is None or severity_confidence < .70
    priority = 'Critical' if score >= 75 else 'High' if score >= 55 else 'Medium' if score >= 35 else 'Low'
    return {
        "category": category, "severity": severity, "priority": priority, "score": score,
        "confidence": category_confidence, "low_confidence": low_confidence,
        "method": "Trained severity plus policy adjustments" if prediction else "Transparent keyword and policy rules",
        "requires_review": True, "keywords": matches.get(category, []),
        "breakdown": [{"label": f"Trained severity: {severity}" if severity else "Base review score",
                       "points": base, "keywords": prediction["severity"]["features"] if prediction else []}] + evidence,
        "models": prediction, "forecast": forecast,
        "limitations": "Suggested priority requires human confirmation. Confidence describes text classification, not priority or incident verification.",
    }


def haversine(a, b):
    lat1, lat2 = math.radians(a.latitude), math.radians(b.latitude)
    dlat = lat2 - lat1
    dlon = math.radians(b.longitude - a.longitude)
    return 6371000 * 2 * math.asin(min(1, math.sqrt(math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)))

def _utc(value):
    return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)

def candidate_context(item, other):
    hours = abs((_utc(item.occurred_at) - _utc(other.occurred_at)).total_seconds()) / 3600
    if hours > 72:
        return None
    has_geo = all(getattr(x, key, None) is not None for x in (item, other) for key in ("latitude", "longitude"))
    distance = haversine(item, other) if has_geo else None
    if distance is not None and distance > 350:
        return None
    if not has_geo and item.area.casefold().strip() != other.area.casefold().strip():
        return None
    return hours, distance

def duplicate_candidates(item, others, encoder=None):
    ready = []
    for other in others:
        if other.id == getattr(item, "id", None) or other.status == "Resolved":
            continue
        context = candidate_context(item, other)
        if context is not None:
            ready.append((other, *context))
    if not ready:
        return []
    if encoder is not None:
        limited = ready[:100]
        vectors = encoder.encode([item.text, *[x[0].text for x in limited]], normalize_embeddings=True)
        scores = vectors[1:] @ vectors[0]
        scored = zip(limited, scores, strict=True)
        threshold, method = .65, "Multilingual MiniLM similarity"
    else:
        def lexical(other):
            a, b = set(re.findall(r"\w+", item.text.lower())), set(re.findall(r"\w+", other.text.lower()))
            return len(a & b) / max(1, len(a | b))
        scored = ((context, lexical(context[0])) for context in ready)
        threshold, method = .20, "Lexical overlap"
    results = []
    for (other, hours, distance), score in scored:
        if score >= threshold:
            results.append({"id": other.id, "title": other.title, "similarity": round(float(score), 3),
                            "distance_m": round(distance) if distance is not None else None,
                            "hours_apart": round(hours, 1), "method": method, "requires_review": True})
    return sorted(results, key=lambda x: x["similarity"], reverse=True)[:5]
