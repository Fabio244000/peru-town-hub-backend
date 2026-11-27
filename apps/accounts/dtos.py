from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class NewAccount:
    first_names: str
    last_names: str
    username: str
    password: str
    phone_country_code: str
    phone_number: str


@dataclass(frozen=True)
class SessionTokens:
    access: str
    refresh: str
    expires_in: int


@dataclass(frozen=True)
class RegisteredAccount:
    username: str
    first_names: str
    last_names: str
    phone: str
    phone_status: str
    created_at: datetime
    tokens: SessionTokens
