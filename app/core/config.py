from pydantic_settings import BaseSettings
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Inventory QR SaaS"
    PROJECT_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    
    DATABASE_URL: str

    JWT_SECRET: str = "CAMBIAR_ESTO_EN_PRODUCCION_CLAVE_SUPER_SECRETA"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365 * 100  # 100 años

    INVITATION_TOKEN_EXPIRE_HOURS: int = 24 * 365 * 100  # 100 años
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24 * 365 * 100  # 100 años

    # Configuración de seguridad
    CORS_ORIGINS: list[str] = ["*"]

    # Configuración de entorno
    DEBUG: bool = False

    # Configuración SMTP (para email)
    SMTP_SERVER: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_SENDER_EMAIL: str

    # URL del frontend para enlaces en correos
    FRONTEND_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True

# Crear una instancia global de configuración
settings = Settings()
