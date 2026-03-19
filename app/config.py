from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_service_account_file: str = ""
    google_wallet_issuer_id: str = ""
    google_wallet_class_id: str = "aztec_ticket"

    model_config = {"env_file": ".env"}


settings = Settings()
