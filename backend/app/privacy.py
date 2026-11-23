"""Minimize direct identifiers before saving or publishing complaint text."""
import re

DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯","0123456789")
EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
PHONE = re.compile(r"(?<!\d)(?:\+?88[ -]?)?01[3-9](?:[ -]?\d){8}(?!\d)")
NID = re.compile(r"(?<!\d)(?:\d{17}|\d{13}|\d{10})(?!\d)")

def redact_contact(text):
    for pattern in (EMAIL, PHONE, NID):
        for match in reversed(list(pattern.finditer(text.translate(DIGITS)))):
            text = text[:match.start()] + "[redacted]" + text[match.end():]
    return text

def redact_input(data):
    return data.model_copy(update={key:redact_contact(getattr(data,key)) for key in ("title","text","area")})
