"""
CivicAI Bangladesh - Duplicate Complaint Detection Engine
Combines multilingual TF-IDF vector cosine similarity with Haversine geospatial proximity.
Identifies duplicate/overlapping citizen complaints within local wards/upazilas.
"""

import math
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from ai.nlp_preprocessor import normalize_text

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two GPS coordinates in kilometers."""
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 9999.0

    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)

class DuplicateDetector:
    def __init__(self, vectorizer, default_radius_km: float = 3.0, default_sim_threshold: float = 0.58):
        self.vectorizer = vectorizer
        self.default_radius_km = default_radius_km
        self.default_sim_threshold = default_sim_threshold

    def find_duplicates(
        self,
        new_title: str,
        new_description: str,
        new_lat: Optional[float],
        new_lon: Optional[float],
        existing_complaints: List[Dict[str, Any]],
        max_candidates: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Scan existing complaints to find potential duplicates based on
        multilingual semantic similarity and geospatial proximity.
        """
        if not existing_complaints:
            return []

        new_text = normalize_text(f"{new_title} {new_description}")
        new_vec = self.vectorizer.transform([new_text])

        # Prepare corpus of existing texts
        corpus_texts = [
            normalize_text(f"{c.get('title', '')} {c.get('description', '')}")
            for c in existing_complaints
        ]
        corpus_vecs = self.vectorizer.transform(corpus_texts)

        # Compute cosine similarities
        sim_scores = cosine_similarity(new_vec, corpus_vecs)[0]

        candidates = []
        for idx, comp in enumerate(existing_complaints):
            semantic_sim = float(sim_scores[idx])
            comp_lat = comp.get("latitude")
            comp_lon = comp.get("longitude")

            geo_dist = haversine_distance_km(new_lat, new_lon, comp_lat, comp_lon)

            # Spatial weight: 1.0 at 0km distance, decaying to 0.0 at default_radius_km
            if geo_dist <= self.default_radius_km:
                spatial_factor = max(0.0, 1.0 - (geo_dist / self.default_radius_km))
            else:
                spatial_factor = 0.0

            # Combined match score (70% semantic + 30% spatial)
            combined_score = (0.70 * semantic_sim) + (0.30 * spatial_factor)

            # Check if this qualifies as a potential duplicate
            is_match = (semantic_sim >= self.default_sim_threshold and geo_dist <= self.default_radius_km) or (semantic_sim >= 0.85)

            if is_match or semantic_sim >= self.default_sim_threshold:
                candidates.append({
                    "complaint_id": comp.get("id"),
                    "tracking_id": comp.get("tracking_id"),
                    "title": comp.get("title"),
                    "status": comp.get("status"),
                    "category": comp.get("category"),
                    "severity": comp.get("severity"),
                    "semantic_similarity": round(semantic_sim, 4),
                    "distance_km": geo_dist if geo_dist < 9000 else None,
                    "match_score": round(combined_score, 4),
                    "is_likely_duplicate": is_match
                })

        # Sort by highest match score
        candidates.sort(key=lambda x: x["match_score"], reverse=True)
        return candidates[:max_candidates]
