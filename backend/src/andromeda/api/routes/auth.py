from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, Request, Response, status

from andromeda.api.dependencies.auth_session import (
    delete_auth_cookie,
    get_auth_token_hash,
    get_optional_current_account,
    auth_token_hash,
    new_auth_token,
    require_trusted_origin,
    set_auth_cookie,
)
from andromeda.api.dependencies.profile_session import get_anonymous_profile_scope
from andromeda.api.dependencies.services import get_auth_service
from andromeda.api.schemas.auth import AuthSessionResponse, LoginRequest, RegisterRequest, account_response
from andromeda.infrastructure.config.settings import Settings
from andromeda.modules.auth.contracts.public import Account
from andromeda.modules.auth.services.authentication import AuthenticationService
from andromeda.modules.proftest.contracts.public import ProfileScope
from andromeda.shared.contracts.ids import SessionTokenHash


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthSessionResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    response: Response,
    http_request: Request,
    _csrf: object = Depends(require_trusted_origin),
    scope: ProfileScope = Depends(get_anonymous_profile_scope),
    service: AuthenticationService = Depends(get_auth_service),
) -> AuthSessionResponse:
    raw_token = new_auth_token()
    account = service.register(request.email, request.password.get_secret_value(), auth_token_hash(raw_token), scope)
    set_auth_cookie(response, _settings(http_request), raw_token)
    return account_response(account)


@router.post("/login", response_model=AuthSessionResponse)
def login(
    request: LoginRequest,
    response: Response,
    http_request: Request,
    _csrf: object = Depends(require_trusted_origin),
    scope: ProfileScope = Depends(get_anonymous_profile_scope),
    service: AuthenticationService = Depends(get_auth_service),
) -> AuthSessionResponse:
    raw_token = new_auth_token()
    account = service.login(request.email, request.password.get_secret_value(), auth_token_hash(raw_token), scope)
    set_auth_cookie(response, _settings(http_request), raw_token)
    return account_response(account)


@router.post("/logout", response_model=AuthSessionResponse)
def logout(
    response: Response,
    request: Request,
    token_hash: SessionTokenHash | None = Depends(get_auth_token_hash),
    service: AuthenticationService = Depends(get_auth_service),
    _csrf: object = Depends(require_trusted_origin),
) -> AuthSessionResponse:
    service.logout(token_hash)
    delete_auth_cookie(response, _settings(request))
    return AuthSessionResponse(authenticated=False, account=None)


@router.get("/session", response_model=AuthSessionResponse)
def current_session(account: Account | None = Depends(get_optional_current_account)) -> AuthSessionResponse:
    if account is None:
        return AuthSessionResponse(authenticated=False, account=None)
    return account_response(account)


def _settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


__all__ = ["router"]
