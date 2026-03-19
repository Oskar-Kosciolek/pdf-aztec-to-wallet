from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.google_wallet import GoogleWalletError, create_save_url

router = APIRouter(prefix="/wallet", tags=["wallet"])


class GoogleWalletRequest(BaseModel):
    aztec_base64: str
    object_id: str | None = None


@router.post("/google")
def google_wallet(body: GoogleWalletRequest):
    """
    Przyjmuje base64 z /tickets/decode.
    Zwraca link 'Dodaj do Google Wallet'.
    """
    try:
        url = create_save_url(
            issuer_id=settings.google_wallet_issuer_id,
            class_id=settings.google_wallet_class_id,
            aztec_base64=body.aztec_base64,
            service_account_file=settings.google_service_account_file,
            object_id=body.object_id,
        )
    except GoogleWalletError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"save_url": url}
