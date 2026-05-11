from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str    
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_SECRET_KEY: str
    ALGORITHM: str
    GROQ_API_TOKEN: str | None = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"

    R2_ACCOUNT_ID: str | None = None
    R2_ACCESS_KEY_ID: str | None = None
    R2_SECRET_ACCESS_KEY: str | None = None
    R2_BUCKET_NAME: str | None = None
    R2_PRESIGNED_EXPIRES_SECONDS: int = 3600

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def R2_ENDPOINT_URL(self) -> str | None:
        if not self.R2_ACCOUNT_ID:
            return None
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    @property
    def GROQ_ENABLED(self) -> bool:
        return bool(self.GROQ_API_TOKEN)

    @property
    def R2_ENABLED(self) -> bool:
        return all(
            [
                self.R2_ACCOUNT_ID,
                self.R2_ACCESS_KEY_ID,
                self.R2_SECRET_ACCESS_KEY,
                self.R2_BUCKET_NAME,
            ]
        )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
