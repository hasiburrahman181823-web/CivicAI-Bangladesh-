"""
CivicAI Bangladesh - Multilingual NLP Preprocessor
Supports Bangla (বাংলা), English, and Banglish (Phonetic Roman Bangla).
Handles spelling variations, diacritics, character n-grams, and stopword filtering.
"""

import re
import unicodedata
from typing import List, Tuple

# Common Bangla stopwords
BANGLA_STOPWORDS = {
    "এবং", "ও", "কিন্তু", "বা", "যদি", "তবে", "তাহলে", "এই", "সেই", "একটি", "এক",
    "হয়", "হয়ে", "হলো", "ছিল", "আছে", "নেই", "না", "করা", "করে", "করতে", "হতে",
    "থেকে", "চেয়ে", "দ্বারা", "দিয়ে", "জন্য", "কারণে", "উপর", "নিচে", "ভেতর",
    "সাথে", "পর", "পূর্বে", "আগে", "কিছু", "অনেক", "সব", "কোন", "কি", "কী"
}

# Common English stopwords
ENGLISH_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "this", "that", "is",
    "are", "was", "were", "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "to", "at", "in", "on", "by", "for", "with", "about", "against",
    "between", "into", "through", "during", "before", "after", "above", "below", "of"
}

# Common Banglish filler words
BANGLISH_STOPWORDS = {
    "ar", "r", "ba", "kintu", "jodi", "tobe", "ei", "shei", "ekta", "ek",
    "hoy", "hoye", "hobe", "chilo", "ache", "nai", "na", "kora", "kore", "korte",
    "theke", "diye", "jonno", "karone", "upor", "niche", "vetor", "sathe", "por"
}

ALL_STOPWORDS = BANGLA_STOPWORDS | ENGLISH_STOPWORDS | BANGLISH_STOPWORDS

# High-urgency markers across 3 languages
URGENCY_KEYWORDS = {
    "bn": [
        "জরুরি", "তাৎক্ষণিক", "অবিলম্বে", "প্রাণহানি", "মৃত্যুঝুঁকি", "বিপজ্জনক", "বিদ্যুৎস্পৃষ্ট",
        "ধসে", "বিস্ফোরণ", "আগুন", "ডুবন্ত", "রক্তাক্ত", "মারাত্মক", "অসুস্থ", "ভয়াবহ", "এসিড",
        "ছিনতাই", "অস্ত্রধারী", "আক্রান্ত", "ডেঙ্গু", "মহামারী", "বিষাক্ত"
    ],
    "en": [
        "urgent", "emergency", "immediate", "fatal", "life-threatening", "hazard", "electrocution",
        "collapse", "explosion", "fire", "drowning", "critical", "severe", "toxic", "armed",
        "robbery", "epidemic", "outbreak", "peril", "casualty", "danger"
    ],
    "bn_en": [
        "urgent", "emergency", "druto", "immediate", "mrityu", "bipod", "accident", "shock",
        "blast", "aagun", "dube", "rokto", "marattok", "oshustho", "voyonkor", "acid",
        "chintai", "dengue", "bishakto", "spot dead"
    ]
}

def detect_language(text: str) -> str:
    """Detect whether text is predominantly Bangla script, English, or Banglish."""
    if not text:
        return "en"

    # Count Bangla Unicode characters (0980–09FF)
    bn_chars = sum(1 for c in text if '\u0980' <= c <= '\u09FF')
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return "en"

    bn_ratio = bn_chars / total_alpha
    if bn_ratio > 0.30:
        return "bn"

    # For Roman script, check for Banglish phonetics
    lower_text = text.lower()
    words = re.findall(r'[a-zA-Z]+', lower_text)
    banglish_markers = {"rasta", "pani", "bhenge", "moyla", "biddut", "chintai", "elaka", "kosto", "dorkar", "ghor", "dokhol"}
    banglish_hits = sum(1 for w in words if w in banglish_markers or w in BANGLISH_STOPWORDS)

    if banglish_hits >= 2:
        return "bn-en"

    return "en"

def normalize_text(text: str) -> str:
    """Normalize text across Bangla unicode and Roman scripts."""
    if not text:
        return ""

    # Unicode normalization (NFC ensures consistent Bangla vowel signs and hasant)
    text = unicodedata.normalize('NFC', text)

    # Standardize whitespace
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)

    # Remove harmful control characters while preserving Bangla punctuation
    text = re.sub(r'[^\w\s\u0980-\u09FF\.\,\-\?\!\'\"\/]', '', text)

    return text.strip()

def tokenize(text: str, remove_stopwords: bool = False) -> List[str]:
    """Tokenize text into lowercase / normalized tokens."""
    norm = normalize_text(text).lower()
    # Match Bangla and English word tokens
    tokens = re.findall(r'[\u0980-\u09FF\w]+', norm)
    if remove_stopwords:
        tokens = [t for t in tokens if t not in ALL_STOPWORDS and len(t) > 1]
    return tokens

def extract_urgency_signals(text: str) -> Tuple[float, List[str]]:
    """Scan text for urgency signals and return an urgency score (0.0 - 1.0) and matched keywords."""
    norm = normalize_text(text).lower()
    matched = []

    for lang, keywords in URGENCY_KEYWORDS.items():
        for kw in keywords:
            if kw in norm:
                matched.append(kw)

    matched = list(set(matched))
    hit_count = len(matched)

    if hit_count == 0:
        urgency_score = 0.20
    elif hit_count == 1:
        urgency_score = 0.55
    elif hit_count == 2:
        urgency_score = 0.78
    else:
        urgency_score = min(0.98, 0.78 + (hit_count - 2) * 0.08)

    # Exclamation mark multiplier
    exclamations = text.count("!")
    if exclamations > 2:
        urgency_score = min(1.0, urgency_score + 0.05)

    return round(urgency_score, 3), matched
