"""
CivicAI Bangladesh - Unified Complaint Intelligence Pipeline
Coordinates NLP preprocessing, category classification, severity prediction,
duplicate detection, priority scoring, urgency extraction, and explainability.
"""

import os
from typing import Dict, Any, List, Optional

from ai.nlp_preprocessor import (
    normalize_text,
    detect_language,
    extract_urgency_signals
)
from ai.classifier import ComplaintClassifier
from ai.duplicate_detector import DuplicateDetector
from ai.priority_scorer import calculate_priority_score
from ai.explainer import generate_ai_explanation

class ComplaintIntelligenceEngine:
    _instance = None

    @classmethod
    def get_instance(cls, models_dir: Optional[str] = None):
        if cls._instance is None:
            cls._instance = cls(models_dir)
        return cls._instance

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
        self.models_dir = models_dir

        # Initialize core components
        self.classifier = ComplaintClassifier(models_dir)
        self.duplicate_detector = DuplicateDetector(
            vectorizer=self.classifier.vectorizer,
            default_radius_km=3.0,
            default_sim_threshold=0.55
        )

    def analyze_complaint(
        self,
        title: str,
        description: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        upvotes: int = 0,
        days_pending: int = 0,
        existing_complaints: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete multi-model intelligence pipeline on a complaint.
        """
        combined_text = f"{title} {description}".strip()

        # 1. Multilingual NLP Language Detection
        detected_lang = detect_language(combined_text)

        # 2. Sentiment and Urgency Extraction
        urgency_score, urgency_keywords = extract_urgency_signals(combined_text)

        # 3. Model 1 & 2: Category and Severity Prediction
        classification_result = self.classifier.predict(title, description)
        category = classification_result["category"]
        cat_conf = classification_result["category_confidence"]
        severity = classification_result["severity"]
        sev_conf = classification_result["severity_confidence"]

        # 4. Model 4: Duplicate Detection
        potential_duplicates = []
        if existing_complaints:
            potential_duplicates = self.duplicate_detector.find_duplicates(
                new_title=title,
                new_description=description,
                new_lat=latitude,
                new_lon=longitude,
                existing_complaints=existing_complaints,
                max_candidates=5
            )

        # 5. Model 3: Priority Ranking Calculation
        priority_data = calculate_priority_score(
            severity=severity,
            category=category,
            urgency_score=urgency_score,
            upvotes=upvotes,
            location_sensitive=False,
            days_pending=days_pending
        )
        priority_score = priority_data["priority_score"]
        priority_level = priority_data["priority_level"]
        breakdown = priority_data["breakdown"]

        # 6. Model 7: AI Explainability Engine
        explanation = generate_ai_explanation(
            category=category,
            category_confidence=cat_conf,
            severity=severity,
            severity_confidence=sev_conf,
            priority_score=priority_score,
            priority_level=priority_level,
            urgency_keywords=urgency_keywords,
            breakdown=breakdown,
            upvotes=upvotes
        )

        return {
            "language": detected_lang,
            "category": category,
            "category_confidence": cat_conf,
            "top_categories": classification_result["top_categories"],
            "severity": severity,
            "severity_confidence": sev_conf,
            "top_severities": classification_result["top_severities"],
            "urgency_score": urgency_score,
            "urgency_keywords": urgency_keywords,
            "priority_score": priority_score,
            "priority_level": priority_level,
            "priority_breakdown": breakdown,
            "duplicates": potential_duplicates,
            "is_duplicate_flagged": any(d.get("is_likely_duplicate") for d in potential_duplicates),
            "explanation": explanation
        }
