import base64
import zlib
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.decoder import decode_aztec, AztecDecodeError
from app.services.uic_parser import decode_pkp_text, parse_fields

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


class InspectRequest(BaseModel):
    data_base64: str


@router.post("/inspect")
def inspect_ticket(body: InspectRequest):
    """
    Podgląd zawartości zdekodowanego kodu Aztec (np. z /decode).
    Rozpakowuje payload zlib i zwraca czytelny podgląd ASCII.
    """
    try:
        raw = base64.b64decode(body.data_base64)
    except Exception:
        raise HTTPException(status_code=422, detail="Nieprawidłowy base64")

    header = raw[:16].decode("iso-8859-1")
    is_uic = header.startswith("#UT")

    result: dict[str, Any] = {
        "size_bytes": len(raw),
        "header": header,
        "standard": "UIC_918_3" if is_uic else None,
    }

    if is_uic:
        zlib_magic = b"\x78\x9c"
        zlib_offset = raw.find(zlib_magic)
        if zlib_offset == -1:
            result["decompressed_error"] = "Nie znaleziono nagłówka zlib w danych"
        else:
            result["zlib_offset"] = zlib_offset
            try:
                decompressed = zlib.decompressobj().decompress(raw[zlib_offset:])
                result["decompressed_size_bytes"] = len(decompressed)
                result["readable_preview"] = decode_pkp_text(decompressed)
                result["parsed_fields"] = parse_fields(decompressed)
            except zlib.error:
                result["decompressed_error"] = "Błąd dekompresji — dane mogą być zaszyfrowane"

    return result
