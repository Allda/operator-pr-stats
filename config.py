"""
Configuration module for GitHub PR Pipeline Parser
"""
import os
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip loading .env file
    pass


class Config:
    """Configuration settings for the application"""

    # GitHub settings
    GITHUB_TOKEN: Optional[str] = os.getenv('GITHUB_TOKEN')

    # Default settings
    DEFAULT_DATA_DIR: str = "data"
    DEFAULT_LIMIT: int = 50
    DEFAULT_DAYS_BACK: int = 30

    # Search terms for pipeline comments
    PIPELINE_SEARCH_TERMS = [
        'Pipeline Summary',
        'Tekton',
        'pipeline',
        'Task Status',
        'Pipeline Status',
        'CI/CD Summary'
    ]

    # Rate limiting
    MAX_REQUESTS_PER_HOUR: int = 5000
    REQUEST_TIMEOUT: int = 30

    @classmethod
    def get_github_token(cls) -> Optional[str]:
        """Get GitHub token from environment or config"""
        return cls.GITHUB_TOKEN

    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        if not cls.GITHUB_TOKEN:
            return False
        return True

    @classmethod
    def get_data_dir(cls, custom_dir: Optional[str] = None) -> Path:
        """Get data directory path"""
        data_dir = custom_dir or cls.DEFAULT_DATA_DIR
        return Path(data_dir)


# Create global config instance
config = Config()
