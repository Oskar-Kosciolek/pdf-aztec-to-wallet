import base64
import hashlib
import io
import json
import uuid
import zipfile
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7


class PKPassError(Exception):
    pass


def _sha1(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def _build_pass_json(
    pass_type_identifier: str,
    team_identifier: str,
    serial_number: str,
    message: str,
) -> bytes:
    pass_dict: dict[str, Any] = {
        "formatVersion": 1,
        "passTypeIdentifier": pass_type_identifier,
        "serialNumber": serial_number,
        "teamIdentifier": team_identifier,
        "organizationName": "Railway Ticket",
        "description": "Bilet kolejowy",
        "generic": {
            "primaryFields": [],
            "secondaryFields": [],
        },
        "barcodes": [
            {
                # Oryginalne bajty UIC zakodowane jako iso-8859-1 — jedyne kodowanie,
                # które przepuszcza bajty 0x00-0xFF bez zniekształceń.
                "message": message,
                "format": "PKBarcodeFormatAztec",
                "messageEncoding": "iso-8859-1",
            }
        ],
    }
    return json.dumps(pass_dict, ensure_ascii=False).encode("utf-8")


def create_pkpass(
    *,
    aztec_base64: str,
    pass_type_identifier: str,
    team_identifier: str,
    certificate_path: str,
    key_path: str,
    wwdr_path: str,
    serial_number: str | None = None,
) -> bytes:
    if not all([pass_type_identifier, team_identifier, certificate_path, key_path, wwdr_path]):
        raise PKPassError(
            "Brakuje konfiguracji PKPass (certyfikat, klucz, WWDR, Pass Type ID, Team ID)"
        )

    if serial_number is None:
        serial_number = str(uuid.uuid4())

    # Bajty Aztec → string iso-8859-1 (lossless dla danych binarnych)
    raw = base64.b64decode(aztec_base64)
    message = raw.decode("iso-8859-1")

    pass_json = _build_pass_json(pass_type_identifier, team_identifier, serial_number, message)

    manifest_bytes = json.dumps({"pass.json": _sha1(pass_json)}).encode("utf-8")

    try:
        with open(certificate_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        with open(key_path, "rb") as f:
            key = serialization.load_pem_private_key(f.read(), password=None)
        with open(wwdr_path, "rb") as f:
            wwdr = x509.load_pem_x509_certificate(f.read())
    except Exception as e:
        raise PKPassError(f"Nie można wczytać certyfikatów: {e}") from e

    try:
        signature = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest_bytes)
            .add_signer(cert, key, hashes.SHA256())
            .add_certificate(wwdr)
            .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.DetachedSignature])
        )
    except Exception as e:
        raise PKPassError(f"Błąd podpisywania PKCS7: {e}") from e

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("pass.json", pass_json)
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("signature", signature)

    return buf.getvalue()
