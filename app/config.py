from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Key settings for JWT
    SECRET_KEY: str = 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Settings for email service
    MAIL_USERNAME: str =
    MAIL_PASSWORD: str = 
    MAIL_FROM: str = "Gradebook Admin"
    MAIL_PORT: int = 587 # Secure port for TLS
    MAIL_SERVER: str = "smtp.gmail.com"


settings = Settings()