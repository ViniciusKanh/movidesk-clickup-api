import secrets

from fastapi import Header, HTTPException, Query, status

from app.config import get_settings


async def validate_webhook_secret(
    x_webhook_secret: str | None = Header(default=None),
    secret: str | None = Query(default=None),
) -> None:
    """Valida o segredo do webhook quando WEBHOOK_SECRET estiver configurado.

    Aceita o segredo de duas formas:
    - Header "X-Webhook-Secret" (uso normal, recomendado quando o sistema que
      chama o webhook permite customizar cabecalhos HTTP);
    - Query string "?secret=..." na propria URL do webhook (necessario porque
      a acao "Acionar Webhook" dos gatilhos do Movidesk so tem um campo de
      URL, sem suporte a cabecalhos customizados).

    Se ambos forem enviados, o header tem prioridade.
    """
    settings = get_settings()
    if not settings.webhook_secret:
        return

    provided = x_webhook_secret or secret or ""
    if not secrets.compare_digest(provided, settings.webhook_secret):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao autorizado.",
        )
