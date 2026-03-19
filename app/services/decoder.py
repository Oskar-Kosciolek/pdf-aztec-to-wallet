import io
import base64

import zxingcpp
from PIL import Image
from pdf2image import convert_from_bytes


class AztecDecodeError(Exception):
    pass


def _to_images(data: bytes) -> list[Image.Image]:
    if data[:4] == b"%PDF":
        return convert_from_bytes(data, dpi=200)
    return [Image.open(io.BytesIO(data))]


def decode_aztec(data: bytes) -> dict:
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
