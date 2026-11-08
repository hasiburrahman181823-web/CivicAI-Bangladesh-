"""
CivicAI Bangladesh - Dynamic Priority Ranking Engine
Calculates intelligent priority scores (0 - 100) combining AI predicted severity,
linguistic urgency, category sensitivity, citizen endorsements, and time elapsed.
"""

from typing import Dict, Any

CATEGORY_WEIGHTS = {
    "Public Safety & Law": 15,
    "Electricity & Power": 15,
    "Healthcare & Sanitation": 15,
    "Water & Drainage": 13,
    "Infrastructure": 12,
    "Environment & Pollution": 10,
    "Transport & Traffic": 10,
    "Corruption & Governance": 10,
    "Waste Management": 8,
    "Streetlight & Lighting": 7
}

SEVERITY_POINTS = {
    "Critical": 40,
    "High": 25,
    "Medium": 15,
    "Low": 5
}

def calculate_priority_score(
    severity: str,
    category: str,
    urgency_score: float,
    upvotes: int = 0,
    location_sensitive: bool = False,
    days_pending: int = 0
) -> Dict[str, Any]:
    """
    Computes transparent factor-weighted priority score (0 - 100).
    """
    # 1. Severity points (Max 40)
    sev_pts = SEVERITY_POINTS.get(severity, 15)

    # 2. Category sensitivity weight (Max 15)
    cat_pts = CATEGORY_WEIGHTS.get(category, 10)

    # 3. Urgency points (Max 20)
    urg_pts = round(float(urgency_score) * 20.0, 1)

    # 4. Citizen Endorsements / Upvotes (Max 15)
    endorsement_pts = min(15.0, round(float(upvotes) * 1.5, 1))

    # 5. Location Sensitivity (School/Hospital/Highway) (Max 5)
    loc_pts = 5.0 if location_sensitive else 0.0

    # 6. Aging Escalation (Max 5)
    aging_pts = min(5.0, float(days_pending) * 1.0)

    total_score = min(100.0, max(0.0, sev_pts + cat_pts + urg_pts + endorsement_pts + loc_pts + aging_pts))
    total_score = round(total_score, 1)

    # Priority Tier
    if total_score >= 80.0:
        priority_level = "Critical"
    elif total_score >= 60.0:
        priority_level = "High"
    elif total_score >= 40.0:
        priority_level = "Medium"
    else:
        priority_level = "Low"

    breakdown = {
        "severity_contribution": sev_pts,
        "category_contribution": cat_pts,
        "urgency_contribution": urg_pts,
        "endorsement_contribution": endorsement_pts,
        "location_sensitivity_contribution": loc_pts,
        "aging_contribution": aging_pts
    }

    return {
        "priority_score": total_score,
        "priority_level": priority_level,
        "breakdown": breakdown
    }
