import json
import re
from collections import Counter
from functools import lru_cache
from math import exp, log, sqrt
from pathlib import Path


@lru_cache(maxsize=1)
def load_intake_model():
    model = json.loads(Path(__file__).with_name("intake_model.json").read_text(encoding="utf-8"))
    for head in model["heads"].values():
        head["index"] = {token: column for column, token in enumerate(head.pop("tokens"))}
    return model


def classify_text(text, target):
    head = load_intake_model()["heads"][target]
    text = re.sub(r"\s\s+", " ", text.lower())
    counts = Counter(text[start:start + size]
                     for size in (2, 3, 4) for start in range(len(text) - size + 1))
    features = {head["index"][token]: 1 + log(count) for token, count in counts.items()
                if token in head["index"]}
    for index in features:
        features[index] *= head["idf"][index]
    norm = sqrt(sum(value * value for value in features.values()))
    if len(features) < 8 or not norm:
        return "uncertain"
    logits = [
        bias + sum(weights[index] * value for index, value in features.items()) / norm
        for weights, bias in zip(head["weights"], head["bias"], strict=True)
    ]
    maximum = max(logits)
    confidence = 1 / sum(exp(score - maximum) for score in logits)
    return head["labels"][logits.index(maximum)] if confidence >= .61 else "uncertain"


DEPARTMENTS = {
    "Road": ("Roads and transport", "সড়ক ও পরিবহন", "Inspect the reported location and record the road hazard.",
             "অভিযোগের স্থানে সড়কের ঝুঁকি পরিদর্শন করে নথিভুক্ত করুন।"),
    "Water": ("Water services", "পানি সেবা", "Check for a reported outage, leak or contamination in the affected area.",
              "এলাকায় পানি সরবরাহ, লিক বা দূষণের সমস্যা যাচাই করুন।"),
    "Electricity": ("Power distribution", "বিদ্যুৎ বিতরণ", "Ask the power distribution team to inspect the location.",
                    "বিদ্যুৎ বিতরণ দলকে ঘটনাস্থল পরিদর্শনের অনুরোধ করুন।"),
    "Waste": ("Sanitation", "পরিচ্ছন্নতা", "Check the collection or drainage route and assign a field inspection.",
              "বর্জ্য সংগ্রহ বা ড্রেনেজের স্থান যাচাই করে পরিদর্শনের ব্যবস্থা করুন।"),
    "Gas": ("Gas distribution", "গ্যাস বিতরণ", "Notify the gas utility for inspection and safety triage.",
            "পরিদর্শন ও ঝুঁকি যাচাইয়ের জন্য গ্যাস বিতরণ সংস্থাকে জানান।"),
    "Health": ("Health services", "স্বাস্থ্য সেবা", "Contact the relevant health facility to verify service impact.",
               "সেবার প্রভাব যাচাই করতে সংশ্লিষ্ট স্বাস্থ্য প্রতিষ্ঠানে যোগাযোগ করুন।"),
    "Food": ("Food safety", "খাদ্য নিরাপত্তা", "Request a food safety officer to assess the report.",
             "অভিযোগ যাচাই করতে খাদ্য নিরাপত্তা কর্মকর্তাকে অনুরোধ করুন।"),
    "Safety": ("Public safety", "জননিরাপত্তা", "Review the reported risk promptly and route it to the appropriate authority.",
               "ঝুঁকিটি দ্রুত যাচাই করে উপযুক্ত কর্তৃপক্ষের কাছে পাঠান।"),
}
GENERAL = ("General services", "সাধারণ সেবা", "Confirm the location and assign the responsible service team.",
           "ঘটনাস্থল নিশ্চিত করে দায়িত্বপ্রাপ্ত সেবা দলকে অভিযোগটি দিন।")
LINK = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
PROMOTION = re.compile(r"\b(?:free lottery|referral code|guaranteed profit|win cash|lottery prize)\b|রেফারেল কোড|লটারি পুরস্কার",
                       re.IGNORECASE)
DIRECTED_ABUSE = re.compile(r"\byou (?:worthless bastard|disgusting scum)\b|তোকে মারব|\btoke marbo\b", re.IGNORECASE)


def summarize(text, title):
    if len(text) <= 260:
        return text
    sentences = [part.strip() for part in re.split(r"(?<=[.!?।])\s*|\n+", text) if part.strip()]
    words = set(title.casefold().split())
    ranked = sorted(enumerate(sentences),
                    key=lambda pair: (len(words.intersection(pair[1].casefold().split())), -pair[0]), reverse=True)
    selected = sorted(ranked[:2])
    summary = " ".join(sentence for _, sentence in selected)
    if len(summary) > 260:
        excerpt = summary[:258].rsplit(" ", 1)[0]
        return (excerpt if len(excerpt) >= 120 else summary[:258]).rstrip() + "…"
    return summary


def assess(title, text, category, priority):
    department_en, department_bn, action_en, action_bn = DEPARTMENTS.get(category, GENERAL)
    risk = classify_text(text, "risk")
    flags = []
    if risk == "promotion" or PROMOTION.search(text):
        flags.append("promotional_language")
    if risk == "abusive" or DIRECTED_ABUSE.search(text):
        flags.append("potential_abuse")
    words = text.lower().split()
    if len(LINK.findall(text)) >= 2 or (len(words) >= 12 and max(Counter(words).values()) / len(words) >= .35):
        flags.append("automated_pattern")
    return {
        "version": load_intake_model()["version"], "department": {"en": department_en, "bn": department_bn},
        "urgency": "High" if priority == "Critical" else priority,
        "sentiment": classify_text(text, "sentiment"), "flags": flags,
        "summary": summarize(text, title), "suggested_action": {"en": action_en, "bn": action_bn},
    }
