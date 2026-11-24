import json
import os

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from ..config import PRODUCTION
from ..models import ComplaintIntake
from ..security import client_address


configured_key = os.getenv("INTAKE_ENCRYPTION_KEY", "")
contact_reviewers = frozenset(
    entry.strip().lower() for entry in os.getenv("CONTACT_REVIEWER_EMAILS", "").split(",") if entry.strip()
)
if PRODUCTION and not configured_key:
    raise RuntimeError("Set INTAKE_ENCRYPTION_KEY before enabling production intake.")
vault = Fernet(configured_key or Fernet.generate_key())


def masked_contact(intake):
    if intake is None:
        return None
    return {
        "mobile": "•••• " + intake.mobile_last4 if intake.mobile_last4 else None,
        "verified": intake.mobile_verified_at is not None,
    }


def seal_intake(item, mobile, request):
    address = client_address(request)
    agent = request.headers.get("user-agent", "")[:256].lower()
    device = "tablet" if "ipad" in agent or "tablet" in agent else (
        "mobile" if "mobile" in agent else "desktop_or_other"
    )
    value = {"complaint_id": item.id, "mobile": mobile, "source_ip": address, "device": device}
    return ComplaintIntake(complaint_id=item.id, sealed_data=vault.encrypt(json.dumps(value).encode()),
                           mobile_last4=mobile[-4:] if mobile else None)


def open_intake(intake):
    try:
        value = json.loads(vault.decrypt(intake.sealed_data))
    except (InvalidToken, ValueError) as error:
        raise HTTPException(503, "Contact information is temporarily unavailable") from error
    if value.pop("complaint_id") != intake.complaint_id:
        raise HTTPException(503, "Contact information is temporarily unavailable")
    return value
