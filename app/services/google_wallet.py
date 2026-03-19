import time
import uuid
from typing import Any

import google.auth.jwt
from google.oauth2 import service_account

_SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]
_SAVE_URL = "https://pay.google.com/gp/v/save/{}"


class GoogleWalletError(Exception):
    pass


def create_save_url(
    *,
    issuer_id: str,
    class_id: str,
    aztec_base64: str,
    service_account_file: str,
    object_id: str | None = None,
) -> str:
    if not issuer_id or not service_account_file:
        raise GoogleWalletError(
            "Brakuje konfiguracji Google Wallet (GOOGLE_WALLET_ISSUER_ID / GOOGLE_SERVICE_ACCOUNT_FILE)"
        )

    if object_id is None:
        object_id = str(uuid.uuid4())

    try:
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=_SCOPES,
        )
    except Exception as e:
        raise GoogleWalletError(f"Nie można wczytać service account: {e}") from e

    claims: dict[str, Any] = {
        "iss": credentials.service_account_email,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "payload": {
            "genericObjects": [
                {
                    "id": f"{issuer_id}.{object_id}",
                    "classId": f"{issuer_id}.{class_id}",
                    "barcode": {
                        "type": "AZTEC",
                        "value": aztec_base64,
                    },
                    "state": "ACTIVE",
                }
            ]
        },
    }

    token: bytes = google.auth.jwt.encode(credentials.signer, claims)
    return _SAVE_URL.format(token.decode("utf-8"))
