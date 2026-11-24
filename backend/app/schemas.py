import re
import unicodedata
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator
from .privacy import DIGITS

class AccountEmail(BaseModel):
    email: str = Field(min_length=5, max_length=254)

    @field_validator('email')
    @classmethod
    def email_valid(cls, value):
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Enter a valid email address')
        return value.lower().strip()

class Credentials(AccountEmail):
    password: str = Field(min_length=10, max_length=128)


def normalize_mobile(value):
    mobile = re.sub(r"[\s()-]", "", value.translate(DIGITS))
    if not re.fullmatch(r"(?:\+?88)?01[3-9][0-9]{8}", mobile):
        raise ValueError("Enter a valid Bangladesh mobile number")
    return "+88" + mobile[-11:]


class Registration(Credentials):
    name: str = Field(min_length=2, max_length=100)
    mobile: str = Field(max_length=32)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if len(value) < 2 or any(unicodedata.category(char) in {"Cc", "Cs"} for char in value):
            raise ValueError("Enter a valid name")
        return value

    @field_validator("mobile")
    @classmethod
    def clean_mobile(cls, value):
        return normalize_mobile(value)

ADMIN_PASSWORD_MINIMUM = 15

class RecoveryCodeRequest(BaseModel):
    password: str = Field(min_length=10, max_length=128)

class PasswordReset(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    password: str = Field(min_length=10, max_length=128)


class EmailCodePasswordReset(AccountEmail):
    code: str = Field(pattern=r"^[0-9]{6}$")
    password: str = Field(min_length=10, max_length=128)

class AdminSetupProof(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")

class AdminSetup(AdminSetupProof):
    password: str = Field(min_length=ADMIN_PASSWORD_MINIMUM, max_length=128)


class AdminPasswordReset(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_+/=-]{43,128}$")
    password: str = Field(min_length=ADMIN_PASSWORD_MINIMUM, max_length=128)

class TrackingInput(BaseModel):
    tracking_key: str = Field(min_length=1,max_length=128)

class ComplaintInput(BaseModel):
    title: str = Field(min_length=5, max_length=120)
    text: str = Field(min_length=10, max_length=1000)
    area: str = Field(min_length=2, max_length=120)
    language: Literal['Bangla', 'English', 'Banglish'] = 'English'
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    occurred_at: datetime

    @field_validator('title', 'text', 'area')
    @classmethod
    def clean(cls, value):
        value = ''.join(c for c in value if not unicodedata.category(c).startswith('C') or c in '\n\t').strip()
        if not value or re.search(r'(.)\1{9,}', value) or len(re.findall(r'https?://', value)) > 2:
            raise ValueError('Please provide a meaningful description without repeated text or excessive links')
        return value

    @model_validator(mode='after')
    def validate_context(self):
        if len(self.text) < 10 or len(self.title) < 5 or len(self.area) < 2:
            raise ValueError('Provide a meaningful title, description and area')
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError('Provide both latitude and longitude')
        if self.occurred_at.tzinfo is None:
            raise ValueError('Incident time must include timezone')
        if self.occurred_at > datetime.now(timezone.utc):
            raise ValueError('Incident time cannot be in the future')
        self.occurred_at = self.occurred_at.astimezone(timezone.utc)
        return self

class ReviewInput(BaseModel):
    status: Literal['Submitted', 'Under review', 'In progress', 'Resolved']
    priority: Literal['Low', 'Medium', 'High', 'Critical']
    note: str = Field(min_length=5, max_length=500)
    duplicate_of: str | None = None


class ComplaintSuggestion(BaseModel):
    text: str = Field(min_length=5, max_length=1000)
    language: Literal['Bangla', 'English', 'Banglish'] = 'English'

    @field_validator("text")
    @classmethod
    def clean(cls, value):
        value = ComplaintInput.clean(value)
        if len(value) < 5:
            raise ValueError("Enter at least five characters")
        return value


class ComplaintSubmission(ComplaintInput):
    mobile: str | None = Field(default=None, max_length=32)

    @field_validator("mobile")
    @classmethod
    def normalize_mobile(cls, value):
        return normalize_mobile(value) if value is not None else None


class FollowupInput(BaseModel):
    body: str = Field(min_length=2, max_length=1000)

    @field_validator("body")
    @classmethod
    def clean_body(cls, value):
        body = ComplaintInput.clean(value)
        if len(body) < 2:
            raise ValueError("Enter a message")
        return body


class ContactAccessInput(BaseModel):
    reason: str = Field(min_length=10, max_length=300)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value):
        reason = ComplaintInput.clean(value)
        if len(reason) < 10:
            raise ValueError("Enter a reason")
        return reason
