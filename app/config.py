from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Key settings for JWT
    SECRET_KEY: str = "xirokyshin_lab4_secure_key_2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Settings for email service
    MAIL_USERNAME: str = "supforgraduatebook@gmail.com"
    MAIL_PASSWORD: str = "xnwy tqkc kmar lgfd"
    MAIL_FROM: str = "Gradebook Admin"
    MAIL_PORT: int = 587 # Secure port for TLS
    MAIL_SERVER: str = "smtp.gmail.com"


settings = Settings()