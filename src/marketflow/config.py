from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "local"
    database_url: str = "sqlite:///./marketflow.db"
    api_key: str = "local-dev-key-change-me"
    max_batch_size: int = 5000

settings = Settings()
