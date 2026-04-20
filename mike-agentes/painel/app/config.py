from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str

    ADMIN_EMAIL: str = "rafaelmacario1991@gmail.com"
    SECRET_KEY: str = "dev-secret-change-in-production"  # sobrescrever em .env em produção
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
