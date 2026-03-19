from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Google Wallet
    google_service_account_file: str = ""
    google_wallet_issuer_id: str = ""
    google_wallet_class_id: str = "aztec_ticket"

    # Apple Wallet (PKPass)
    pkpass_certificate_file: str = ""
    pkpass_key_file: str = ""
    pkpass_wwdr_file: str = ""
    pkpass_pass_type_identifier: str = ""
    pkpass_team_identifier: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
