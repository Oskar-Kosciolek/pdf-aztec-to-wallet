from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.config import settings
from app.services.google_wallet import GoogleWalletError, create_save_url
from app.services.pkpass import PKPassError, create_pkpass

router = APIRouter(prefix="/wallet", tags=["wallet"])


class GoogleWalletRequest(BaseModel):
    aztec_base64: str
    object_id: str | None = None


class PKPassRequest(BaseModel):
    aztec_base64: str
    serial_number: str | None = None


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


@router.post("/apple", response_class=Response)
def apple_wallet(body: PKPassRequest):
    """
    Przyjmuje base64 z /tickets/decode.
    Zwraca plik .pkpass gotowy do Apple Wallet.
    """
    try:
        pkpass_bytes = create_pkpass(
            aztec_base64=body.aztec_base64,
            pass_type_identifier=settings.pkpass_pass_type_identifier,
            team_identifier=settings.pkpass_team_identifier,
            certificate_path=settings.pkpass_certificate_file,
            key_path=settings.pkpass_key_file,
            wwdr_path=settings.pkpass_wwdr_file,
            serial_number=body.serial_number,
        )
    except PKPassError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=pkpass_bytes,
        media_type="application/vnd.apple.pkpass",
        headers={"Content-Disposition": "attachment; filename=ticket.pkpass"},
    )
