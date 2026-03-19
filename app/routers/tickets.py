from fastapi import APIRouter, HTTPException, UploadFile, File

from app.services.decoder import decode_aztec, AztecDecodeError

router = APIRouter(prefix="/tickets", tags=["tickets"])

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}


@router.post("/decode")
async def decode_ticket(file: UploadFile = File(...)):
    """
    Przyjmuje plik PDF lub obraz z kodem Aztec.
    Zwraca surowe bajty kodu jako base64 (gotowe do wrzucenia w PKPass / Google Wallet).
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Nieobsługiwany typ pliku: {file.content_type}",
        )

    data = await file.read()

    try:
        return decode_aztec(data)
    except AztecDecodeError as e:
        raise HTTPException(status_code=422, detail=str(e))
