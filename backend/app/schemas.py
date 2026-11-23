import re
import unicodedata
from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

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

ADMIN_PASSWORD_MINIMUM = 15

class RecoveryCodeRequest(BaseModel):
    password: str = Field(min_length=10, max_length=128)

class PasswordReset(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    password: str = Field(min_length=10, max_length=128)

class AdminSetupProof(BaseModel):
    code: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")

class AdminSetup(AdminSetupProof):
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
