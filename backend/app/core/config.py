"""
Core configuration management using Pydantic Settings
Loads configuration from environment variables
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # API Configuration
    APP_NAME: str = "B2B Textile Procurement API"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    

    WORKERS: int = 1
    
    # Database Configuration
    SQLITE_CHECKPOINT_DB: str = "B2B-textile-assistant.db"
    SQLITE_SUPPLIERS_DB: str = "suppliers.db"
    
    # LangGraph Configuration
    GRAPH_DEBUG: bool = False
    DEFAULT_THREAD_ID_PREFIX: str = "thread"
    
    # AI/LLM Configuration
    GOOGLE_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Composio Configuration (Email)
    COMPOSIO_API_KEY: Optional[str] = None
    COMPOSIO_USER_ID: str = "0000-0000"
    
    # CORS Configuration
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "app.log"
    
    # Background Task Configuration
    TASK_TIMEOUT: int = 300  # 5 minutes
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def checkpoint_db_path(self) -> Path:
        """Get full path to checkpoint database"""
        return Path(self.SQLITE_CHECKPOINT_DB)
    
    @property
    def suppliers_db_path(self) -> Path:
        """Get full path to suppliers database"""
        return Path(self.SQLITE_SUPPLIERS_DB)


# Global settings instance
settings = Settings()