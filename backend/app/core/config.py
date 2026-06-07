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

    pdf_reader_engine: str = "auto"
    pdf_reader_odl_version: str = "2.4.7"
    pdf_reader_odl_table_method: str = "cluster"
    pdf_reader_odl_reading_order: str = "xycut"
    pdf_reader_odl_format: str = "markdown,json"
    pdf_reader_odl_timeout_seconds: int = 180
    pdf_reader_odl_threads: int = 1
    pdf_reader_odl_enable_hybrid: bool = False
    pdf_reader_allow_pymupdf_fallback: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
