from __future__ import annotations

from datetime import datetime
from typing import Annotated

from pydantic import Field, SecretStr, StringConstraints

from andromeda.modules.auth.contracts.public import Account, AuthSessionResult

from .common import ApiModel


EmailInput = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=320)]


class RegisterRequest(ApiModel):
    email: EmailInput
    password: SecretStr = Field(min_length=12, max_length=128)


class LoginRequest(ApiModel):
    email: EmailInput
    password: SecretStr = Field(min_length=1, max_length=128)


class AccountResponse(ApiModel):
    account_id: str = Field(alias="accountId")
    email: str
    created_at: datetime = Field(alias="createdAt")


class AuthSessionResponse(ApiModel):
    authenticated: bool
    account: AccountResponse | None = None


def auth_response(session: AuthSessionResult) -> AuthSessionResponse:
    account = session.account
    return AuthSessionResponse(
        authenticated=session.authenticated,
        account=AccountResponse(
            accountId=account.account_id,
            email=account.email,
            createdAt=account.created_at,
        )
        if account is not None
        else None,
    )


def account_response(account: Account) -> AuthSessionResponse:
    return auth_response(AuthSessionResult(authenticated=True, account=account))


__all__ = ["AuthSessionResponse", "LoginRequest", "RegisterRequest", "account_response", "auth_response"]
