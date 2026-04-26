from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    use_mock: bool = True
    ner_backend: str = "llm"
    llm_backend: str = "openai"  # openai | lora

    openai_api_key: str = ""
    openai_ner_model: str = "gpt-4o-mini"
    openai_chat_model: str = "gpt-4o-mini"

    max_history_turns: int = 5
    sentiment_data_path: str = "./data/sentiment_summary.json"

    host: str = "0.0.0.0"
    port: int = 8000


settings = Settings()
