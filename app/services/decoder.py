import io
import base64
from typing import TypedDict

import zxingcpp
from PIL import Image
from pdf2image import convert_from_bytes


class AztecDecodeError(Exception):
    pass


class DecodeResult(TypedDict):
    data_base64: str
    size: int
    is_uic: bool


def _to_images(data: bytes) -> list[Image.Image]:
    if data[:4] == b"%PDF":
        try:
            pages: list[Image.Image] = convert_from_bytes(data, dpi=200)
            return pages
        except Exception as e:
            raise AztecDecodeError(
                f"Nie można wyrenderować PDF: {e}"
            ) from e
    try:
        return [Image.open(io.BytesIO(data))]
    except Exception as e:
        raise AztecDecodeError(f"Nie można otworzyć obrazu: {e}") from e


def decode_aztec(data: bytes) -> DecodeResult:
    images = _to_images(data)

    for img in images:
        for result in zxingcpp.read_barcodes(img):
            if result.format != zxingcpp.BarcodeFormat.Aztec:
                continue

            # Używamy .bytes, nie .text — dane UIC są binarne (zlib-compressed)
            raw = result.bytes
            return {
                "data_base64": base64.b64encode(raw).decode(),
                "size": len(raw),
                "is_uic": raw[:3] == b"#UT",
            }

    raise AztecDecodeError("Nie znaleziono kodu Aztec w pliku")
