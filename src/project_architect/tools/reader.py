"""
URL Reader tool using LangChain's WebBaseLoader.

Extracts and cleans content from web pages for research purposes.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class ReadResult:
    """Result of reading a URL."""

    url: str
    title: str
    content: str
    success: bool
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "success": self.success,
            "error": self.error,
        }

    @property
    def summary(self) -> str:
        """Get a truncated summary of the content."""
        if not self.success:
            return f"Failed to read: {self.error}"
        max_len = 500
        if len(self.content) > max_len:
            return self.content[:max_len] + "..."
        return self.content


class URLReader:
    """
    URL content reader with fallback strategies.

    Uses httpx for HTTP requests and BeautifulSoup for parsing.
    Includes error handling and content cleaning.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        max_content_length: int = 50000,
    ):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self._client = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-load HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
            )
        return self._client

    def read(self, url: str) -> ReadResult:
        """
        Read and extract content from a URL.

        Args:
            url: The URL to read

        Returns:
            ReadResult with extracted content or error information
        """
        logger.info(f"Reading URL: {url}")

        try:
            # Validate URL
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return ReadResult(
                    url=url,
                    title="",
                    content="",
                    success=False,
                    error="Invalid URL format",
                )

            # Fetch the page
            response = self.client.get(url)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")

            # Extract title
            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Remove unwanted elements
            for element in soup.find_all(
                ["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]
            ):
                element.decompose()

            # Extract main content
            content = self._extract_main_content(soup)

            # Clean and truncate content
            content = self._clean_content(content)
            if len(content) > self.max_content_length:
                content = content[: self.max_content_length] + "\n\n[Content truncated...]"

            logger.info(f"Successfully read {len(content)} characters from: {url}")

            return ReadResult(
                url=url,
                title=title,
                content=content,
                success=True,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code}: {e.response.reason_phrase}"
            logger.warning(f"Failed to read {url}: {error_msg}")
            return ReadResult(
                url=url,
                title="",
                content="",
                success=False,
                error=error_msg,
            )

        except httpx.RequestError as e:
            error_msg = f"Request failed: {str(e)}"
            logger.warning(f"Failed to read {url}: {error_msg}")
            return ReadResult(
                url=url,
                title="",
                content="",
                success=False,
                error=error_msg,
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to read {url}: {error_msg}")
            return ReadResult(
                url=url,
                title="",
                content="",
                success=False,
                error=error_msg,
            )

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Extract the main content from the page.

        Tries to find article/main content, falls back to body.
        """
        # Try to find main content containers
        main_selectors = [
            "article",
            "main",
            '[role="main"]',
            ".post-content",
            ".article-content",
            ".entry-content",
            ".content",
            "#content",
        ]

        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                return main_content.get_text(separator="\n", strip=True)

        # Fall back to body
        body = soup.find("body")
        if body:
            return body.get_text(separator="\n", strip=True)

        return soup.get_text(separator="\n", strip=True)

    def _clean_content(self, content: str) -> str:
        """Clean extracted content."""
        # Remove excessive whitespace
        lines = content.split("\n")
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            line = line.strip()
            if not line:
                if not prev_empty:
                    cleaned_lines.append("")
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False

        return "\n".join(cleaned_lines).strip()

    def read_multiple(self, urls: list[str]) -> list[ReadResult]:
        """
        Read multiple URLs.

        Args:
            urls: List of URLs to read

        Returns:
            List of ReadResult objects
        """
        results = []
        for url in urls:
            result = self.read(url)
            results.append(result)
        return results

    def close(self):
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
