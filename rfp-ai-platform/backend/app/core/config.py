import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate .env dynamically
_config_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(os.path.dirname(_config_dir))
_platform_dir = os.path.dirname(_backend_dir)
_candidate_envs = [
    os.path.join(_platform_dir, ".env"),
    os.path.join(_backend_dir, ".env"),
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "rfp-ai-platform", ".env"),
    "../.env",
    ".env",
]
for p in _candidate_envs:
    if os.path.isfile(p):
        load_dotenv(p)
        break

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered RFP Intelligence"
    API_V1_STR: str = "/api"
    
    # MySQL Database Configuration
    MYSQL_USER: str = os.getenv("MYSQL_USER", "rfp_user")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "rfp_password")
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT: str = os.getenv("MYSQL_PORT", "3306")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "rfp_db")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    # ChromaDB Configuration
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "localhost")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_jwt_key_here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # RAG Configuration
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "1000"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "200"))
    
    # AI Providers
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

    _base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(_base_dir, ".env"),
            os.path.join(_base_dir, "..", "rfp-ai-platform", ".env"),
            "../.env",
            ".env"
        ),
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
