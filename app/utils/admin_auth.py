from __future__ import annotations

import secrets

from fastapi import Cookie, HTTPException, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings

SESSION_COOKIE_NAME = "movidesk_clickup_admin_session"
SESSION_SALT = "movidesk-clickup-admin"


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    secret = settings.admin_session_secret or settings.webhook_secret or settings.clickup_token or "dev-insecure-secret"
    return URLSafeTimedSerializer(secret_key=secret, salt=SESSION_SALT)


def verify_admin_credentials(username: str, password: str) -> bool:
    """Compara usuario/senha informados com ADMIN_USERNAME/ADMIN_PASSWORD, em tempo constante."""
    settings = get_settings()
    if not settings.admin_username or not settings.admin_password:
        # Painel administrativo desabilitado ate que usuario/senha sejam configurados.
        return False

    username_ok = secrets.compare_digest(username or "", settings.admin_username)
    password_ok = secrets.compare_digest(password or "", settings.admin_password)
    return username_ok and password_ok


def create_session_cookie(response: Response, username: str) -> None:
    token = _serializer().dumps({"u": username})
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.admin_session_ttl_minutes * 60,
        path="/admin",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/admin")


async def require_admin_session(
    admin_session: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> str:
    settings = get_settings()
    if not settings.admin_username or not settings.admin_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Painel administrativo nao configurado (defina ADMIN_USERNAME e ADMIN_PASSWORD).",
        )

    if not admin_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao invalida. Faca login novamente.")

    max_age_seconds = settings.admin_session_ttl_minutes * 60
    try:
        data = _serializer().loads(admin_session, max_age=max_age_seconds)
    except SignatureExpired:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao expirada. Faca login novamente.")
    except BadSignature:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao invalida. Faca login novamente.")

    username = data.get("u") if isinstance(data, dict) else None
    if not username or not secrets.compare_digest(str(username), settings.admin_username):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessao invalida. Faca login novamente.")

    return str(username)
