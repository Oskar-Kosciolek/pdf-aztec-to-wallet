from fastapi import APIRouter, HTTPException, UploadFile, File

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("/decode")
async def decode_ticket(file: UploadFile = File(...)):
    """
    Accepts a PDF or image file containing a UIC 918.3 Aztec barcode.
    Returns the raw decoded bytes (base64-encoded) from the Aztec code.
    """
    raise HTTPException(status_code=501, detail="Not implemented yet")
