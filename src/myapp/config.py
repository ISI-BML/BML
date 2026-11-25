import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_REGISTRATION_KEY = os.getenv("ADMIN_REGISTRATION_KEY", "")
    BOT_RESPONSE_DELAY_MINUTES = int(os.getenv("BOT_RESPONSE_DELAY_MINUTES", "30"))
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
