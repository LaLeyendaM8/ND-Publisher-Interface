import secrets

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    settings = get_settings()
    expected = settings.internal_api_token
    if not expected:
        return
    if not x_internal_token or not secrets.compare_digest(x_internal_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
