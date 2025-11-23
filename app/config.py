from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Секретний ключ для генерації токенів
    SECRET_KEY: str = "secret_key_for_lab_4_change_me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Налаштування пошти (для імітації або реальної відправки)
    MAIL_USERNAME: str = "supforgraduatebook@gmail.com"
    MAIL_PASSWORD: str = "xnwy tqkc kmar lgfd"
    MAIL_FROM: str = "Gradebook Admin"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"


settings = Settings()