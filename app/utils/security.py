import secrets

from fastapi import Header, HTTPException, status

from app.config import get_settings


async def validate_webhook_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    """Valida o segredo do webhook quando WEBHOOK_SECRET estiver configurado."""
    settings = get_settings()
    if not settings.webhook_secret:
        return

    provided = x_webhook_secret or ""
    if not secrets.compare_digest(provided, settings.webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autorizado.",
        )
