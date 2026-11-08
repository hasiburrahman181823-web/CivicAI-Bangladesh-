"""
CivicAI Bangladesh - AI Explanation & Decision Support Engine
Provides interpretable, factor-by-factor transparency for citizen complaints.
Explains priority scores, extracted signals, and departmental routing recommendations.
"""

from typing import Dict, Any, List

DEPARTMENT_ROUTING = {
    "Infrastructure": "Roads & Highways Department (RHD) / City Corporation Engineering",
    "Water & Drainage": "WASA (Water Supply & Sewerage Authority) / Municipal Drainage Cell",
    "Waste Management": "City Corporation Waste Management Division (Conservancy)",
    "Electricity & Power": "BPDB / DPDC / DESCO / REB Rapid Response Wing",
    "Streetlight & Lighting": "Municipal Electrical Maintenance Division",
    "Public Safety & Law": "Bangladesh Police / Local Thana / Highway Police",
    "Environment & Pollution": "Department of Environment (DoE) & Forest Directorate",
    "Healthcare & Sanitation": "Directorate General of Health Services (DGHS) / Upazila Health Complex",
    "Corruption & Governance": "Anti-Corruption Commission (ACC) & District Commissioner Office",
    "Transport & Traffic": "BRTA & Traffic Police Division"
}

DEPARTMENT_ROUTING_BN = {
    "Infrastructure": "সড়ক ও জনপথ বিভাগ (সওজ) / সিটি কর্পোরেশন প্রকৌশল শাখা",
    "Water & Drainage": "ওয়াসা / পৌরসভা পয়ঃনিষ্কাশন সেল",
    "Waste Management": "সিটি কর্পোরেশন বর্জ্য ব্যবস্থাপনা শাখা (কনজারভেন্সি)",
    "Electricity & Power": "পিডিবি / ডিপিডিসি / ডেসকো / পল্লী বিদ্যুৎ জরুরি দল",
    "Streetlight & Lighting": "পৌর বিদ্যুৎ ও সড়কবাতি রক্ষণাবেক্ষণ শাখা",
    "Public Safety & Law": "বাংলাদেশ পুলিশ / সংশ্লিষ্ট থানা / হাইওয়ে পুলিশ",
    "Environment & Pollution": "পরিবেশ অধিদপ্তর (DoE) ও জেলা প্রশাসন",
    "Healthcare & Sanitation": "স্বাস্থ্য অধিদপ্তর (DGHS) / উপজেলা স্বাস্থ্য কমপ্লেক্স",
    "Corruption & Governance": "দুদক (ACC) ও জেলা প্রশাসক কার্যালয়",
    "Transport & Traffic": "বিআরটিএ (BRTA) ও ট্রাফিক পুলিশ বিভাগ"
}

def generate_ai_explanation(
    category: str,
    category_confidence: float,
    severity: str,
    severity_confidence: float,
    priority_score: float,
    priority_level: str,
    urgency_keywords: List[str],
    breakdown: Dict[str, Any],
    upvotes: int = 0
) -> Dict[str, Any]:
    """Generate comprehensive dual-language explanation and routing guidance."""
    target_dept = DEPARTMENT_ROUTING.get(category, "Concerned Municipal Authority")
    target_dept_bn = DEPARTMENT_ROUTING_BN.get(category, "সংশ্লিষ্ট পৌর কর্তৃপক্ষ")

    # Construct narrative explanation in English
    reasons_en = [
        f"Classified as '{category}' with {int(category_confidence * 100)}% model confidence.",
        f"Assessed as '{severity}' severity ({breakdown.get('severity_contribution', 0)} pts) based on risk factors."
    ]

    if urgency_keywords:
        reasons_en.append(
            f"Detected high-urgency language markers: [{', '.join(urgency_keywords[:4])}] adding {breakdown.get('urgency_contribution', 0)} pts."
        )

    if upvotes > 0:
        reasons_en.append(
            f"Endorsed by {upvotes} verified citizens (+{breakdown.get('endorsement_contribution', 0)} community priority pts)."
        )

    explanation_en = (
        f"This complaint received an intelligent priority index of {priority_score}/100 ({priority_level} priority). "
        + " ".join(reasons_en)
        + f" Recommended routing: Forward to {target_dept} for rapid inspection and resolution."
    )

    # Construct narrative explanation in Bangla
    reasons_bn = [
        f"অভিযোগটি '{category}' ক্যাটাগরিতে {int(category_confidence * 100)}% নিশ্চিততার সাথে চিহ্নিত হয়েছে।",
        f"ঝুঁকির মাত্রার ভিত্তিতে এটি '{severity}' তীব্রতা ({breakdown.get('severity_contribution', 0)} পয়েন্ট) পেয়েছে।"
    ]

    if urgency_keywords:
        reasons_bn.append(
            f"জরুরি শব্দ সনাক্ত হয়েছে: [{', '.join(urgency_keywords[:4])}], যা জরুরি স্কেলে {breakdown.get('urgency_contribution', 0)} পয়েন্ট যোগ করেছে।"
        )

    if upvotes > 0:
        reasons_bn.append(
            f"{upvotes} জন নাগরিকের সমর্থন রয়েছে (+{breakdown.get('endorsement_contribution', 0)} পয়েন্ট)।"
        )

    explanation_bn = (
        f"অভিযোগটি কৃত্রিম বুদ্ধিমত্তার বিশ্লেষণে {priority_score}/100 স্কোর পেয়েছে ({priority_level} অগ্রাধিকার)। "
        + " ".join(reasons_bn)
        + f" সুপারিশ: দ্রুত ব্যবস্থা গ্রহণের জন্য {target_dept_bn}-এ প্রেরণ করা হোক।"
    )

    # SLA Recommended turnaround
    sla_hours = 12 if priority_level == "Critical" else (24 if priority_level == "High" else (48 if priority_level == "Medium" else 72))

    return {
        "summary_en": explanation_en,
        "summary_bn": explanation_bn,
        "recommended_department": target_dept,
        "recommended_department_bn": target_dept_bn,
        "recommended_sla_hours": sla_hours,
        "action_required": "Emergency Immediate Dispatch" if priority_level == "Critical" else ("Priority Field Inspection" if priority_level == "High" else "Scheduled Resolution Queue")
    }
