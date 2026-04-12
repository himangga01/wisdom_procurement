from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SMART Procurement Calculator API"
    app_env: str = "local"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    sqlite_path: str = "./app.db"
    storage_root: str = "./storage"

    openai_api_key: str = ""
    openai_model_primary: str = "gpt-5.1"
    openai_model_secondary: str = "gpt-5-mini"

    ocr_languages: str = "kor+eng"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
