"""
Configuration settings for Project Architect.

Loads environment variables and provides typed access to configuration.
"""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    # Required fields (no defaults) must come first
    openai_api_key: str
    notion_token: str
    notion_parent_page_id: str

    # LLM Configuration
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7

    # Google Custom Search (Optional)
    google_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None

    # Research Configuration
    max_urls_per_step: int = 2
    max_search_results: int = 5

    # Computed properties
    @property
    def use_google_search(self) -> bool:
        """Check if Google Custom Search is configured."""
        return bool(self.google_api_key and self.google_search_engine_id)

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        # Load .env file if it exists
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path)

        # Required fields
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        notion_token = os.getenv("NOTION_TOKEN")
        if not notion_token:
            raise ValueError("NOTION_TOKEN environment variable is required")

        notion_parent_page_id = os.getenv("NOTION_PARENT_PAGE_ID")
        if not notion_parent_page_id:
            raise ValueError("NOTION_PARENT_PAGE_ID environment variable is required")

        # Get base URL (optional, for OpenAI-compatible APIs)
        openai_base_url = os.getenv("OPENAI_BASE_URL") or None

        # Optional fields with defaults
        return cls(
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            notion_token=notion_token,
            notion_parent_page_id=notion_parent_page_id,
            google_api_key=os.getenv("GOOGLE_API_KEY") or None,
            google_search_engine_id=os.getenv("GOOGLE_SEARCH_ENGINE_ID") or None,
            max_urls_per_step=int(os.getenv("MAX_URLS_PER_STEP", "2")),
            max_search_results=int(os.getenv("MAX_SEARCH_RESULTS", "5")),
        )

    def validate(self) -> list[str]:
        """Validate settings and return list of warnings."""
        warnings = []

        if self.openai_base_url:
            warnings.append(
                f"Using custom OpenAI-compatible API at: {self.openai_base_url}"
            )

        if not self.use_google_search:
            warnings.append(
                "Google Custom Search not configured. Using DuckDuckGo as fallback."
            )

        if self.max_urls_per_step > 5:
            warnings.append(
                f"max_urls_per_step={self.max_urls_per_step} may slow down research. "
                "Consider using 2-5 for optimal performance."
            )

        return warnings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings.from_env()
