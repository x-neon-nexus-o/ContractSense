from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=10, max_length=200)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.rsplit("@", 1)[-1]:
            raise ValueError("Enter a valid email address.")
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class UserView(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserView


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ContractMetadataUpdate(BaseModel):
    jurisdiction_state: str | None = Field(default=None, max_length=100)
    governing_law: str | None = Field(default=None, max_length=200)
    msme_supplier: bool | None = None


class ApiMessage(BaseModel):
    message: str


class AnalysisEnvelope(BaseModel):
    analysis_id: str
    contract_id: str
    result: dict[str, Any]
    created_at: str
