from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import WebhookResponse
from app.services.integration_service import IntegrationService
from app.utils.security import validate_webhook_secret

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/movidesk/clickup",
    response_model=WebhookResponse,
    dependencies=[Depends(validate_webhook_secret)],
)
async def movidesk_to_clickup(
    payload: dict[str, Any],
    db: Session = Depends(get_db),
) -> WebhookResponse:
    service = IntegrationService(db)
    return await service.process_movidesk_webhook(payload)
