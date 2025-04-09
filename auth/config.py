from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str = "secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./sql_app.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()