"""
Search tool with Google Custom Search and DuckDuckGo fallback.

Provides a unified interface for web search with automatic fallback
when Google API is not configured or quota is exceeded.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    title: str
    url: str
    snippet: str
    source: str  # "google" or "duckduckgo"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }


class GoogleSearchProvider:
    """Google Custom Search API provider."""

    def __init__(self, api_key: str, search_engine_id: str):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self._service = None

    @property
    def service(self):
        """Lazy-load the Google API service."""
        if self._service is None:
            self._service = build("customsearch", "v1", developerKey=self.api_key)
        return self._service

    def search(
        self,
        query: str,
        num_results: int = 5,
        date_restrict: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search using Google Custom Search API.

        Args:
            query: Search query string
            num_results: Number of results to return (max 10)
            date_restrict: Date restriction (e.g., "d7" for last 7 days, "m1" for last month)

        Returns:
            List of SearchResult objects
        """
        try:
            params = {
                "q": query,
                "cx": self.search_engine_id,
                "num": min(num_results, 10),
            }

            if date_restrict:
                params["dateRestrict"] = date_restrict

            result = self.service.cse().list(**params).execute()

            results = []
            for item in result.get("items", []):
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source="google",
                    )
                )

            logger.info(f"Google search returned {len(results)} results for: {query}")
            return results

        except HttpError as e:
            logger.warning(f"Google search failed: {e}")
            raise


class DuckDuckGoSearchProvider:
    """DuckDuckGo search provider (free, no API key required)."""

    def search(
        self,
        query: str,
        num_results: int = 5,
        time_filter: Optional[str] = None,
    ) -> list[SearchResult]:
        """
        Search using DuckDuckGo.

        Args:
            query: Search query string
            num_results: Number of results to return
            time_filter: Time filter ("d" for day, "w" for week, "m" for month, "y" for year)

        Returns:
            List of SearchResult objects
        """
        try:
            with DDGS() as ddgs:
                ddg_results = list(
                    ddgs.text(
                        query,
                        max_results=num_results,
                        timelimit=time_filter,
                    )
                )

            results = []
            for item in ddg_results:
                results.append(
                    SearchResult(
                        title=item.get("title", ""),
                        url=item.get("href", ""),
                        snippet=item.get("body", ""),
                        source="duckduckgo",
                    )
                )

            logger.info(f"DuckDuckGo search returned {len(results)} results for: {query}")
            return results

        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
            raise


class SearchTool:
    """
    Unified search tool with automatic fallback.

    Uses Google Custom Search if configured, otherwise falls back to DuckDuckGo.
    Also falls back automatically if Google quota is exceeded.
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        google_search_engine_id: Optional[str] = None,
    ):
        self._google_provider = None
        self._ddg_provider = DuckDuckGoSearchProvider()

        if google_api_key and google_search_engine_id:
            self._google_provider = GoogleSearchProvider(
                api_key=google_api_key,
                search_engine_id=google_search_engine_id,
            )
            logger.info("SearchTool initialized with Google Custom Search")
        else:
            logger.info("SearchTool initialized with DuckDuckGo (Google not configured)")

    @property
    def primary_provider(self) -> str:
        """Return the name of the primary search provider."""
        return "google" if self._google_provider else "duckduckgo"

    def search(
        self,
        query: str,
        num_results: int = 5,
        recent_only: bool = True,
    ) -> list[SearchResult]:
        """
        Search the web for information.

        Args:
            query: Search query string
            num_results: Number of results to return
            recent_only: If True, prefer recent content (last 30 days)

        Returns:
            List of SearchResult objects
        """
        results = []

        # Try Google first if available
        if self._google_provider:
            try:
                date_restrict = "m1" if recent_only else None  # Last month
                results = self._google_provider.search(
                    query=query,
                    num_results=num_results,
                    date_restrict=date_restrict,
                )
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Google search failed, falling back to DuckDuckGo: {e}")

        # Fall back to DuckDuckGo
        try:
            time_filter = "m" if recent_only else None  # Last month
            results = self._ddg_provider.search(
                query=query,
                num_results=num_results,
                time_filter=time_filter,
            )
        except Exception as e:
            logger.error(f"All search providers failed: {e}")
            results = []

        return results

    def search_for_step(
        self,
        step_name: str,
        step_description: str,
        project_context: str,
        num_results: int = 5,
    ) -> list[SearchResult]:
        """
        Search for information relevant to a specific project step.

        Constructs an optimized search query based on the step context.

        Args:
            step_name: Name of the step
            step_description: Description of what the step involves
            project_context: Brief context about the overall project
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        # Construct a focused search query
        query = f"{step_name} {step_description} best practices 2026"

        logger.info(f"Searching for step: {step_name}")
        return self.search(query=query, num_results=num_results, recent_only=True)
