from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Секретний ключ для генерації токенів
    SECRET_KEY: str = 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 

    # Налаштування пошти (для імітації або реальної відправки)
    MAIL_USERNAME: str = 
    MAIL_PASSWORD: str = 
    MAIL_FROM: str = 
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"


settings = Settings()
