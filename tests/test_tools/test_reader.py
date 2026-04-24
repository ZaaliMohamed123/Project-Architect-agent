"""Tests for the URL reader tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock

import httpx

from project_architect.tools.reader import URLReader, ReadResult


class TestReadResult:
    """Tests for ReadResult dataclass."""

    def test_successful_result(self):
        """Test creating a successful read result."""
        result = ReadResult(
            url="https://example.com",
            title="Example Title",
            content="Example content here",
            success=True,
        )
        assert result.success is True
        assert result.error is None
        assert "Example content" in result.summary

    def test_failed_result(self):
        """Test creating a failed read result."""
        result = ReadResult(
            url="https://example.com",
            title="",
            content="",
            success=False,
            error="Connection refused",
        )
        assert result.success is False
        assert "Connection refused" in result.summary

    def test_summary_truncation(self):
        """Test that summary truncates long content."""
        long_content = "x" * 1000
        result = ReadResult(
            url="https://example.com",
            title="Test",
            content=long_content,
            success=True,
        )
        assert len(result.summary) < len(long_content)
        assert result.summary.endswith("...")

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ReadResult(
            url="https://example.com",
            title="Test",
            content="Content",
            success=True,
        )
        d = result.to_dict()
        assert d["url"] == "https://example.com"
        assert d["success"] is True


class TestURLReader:
    """Tests for URLReader."""

    def test_invalid_url(self):
        """Test handling of invalid URLs."""
        reader = URLReader()
        result = reader.read("not-a-valid-url")

        assert result.success is False
        assert "Invalid URL" in result.error

    @patch("httpx.Client.get")
    def test_successful_read(self, mock_get):
        """Test successful URL read."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <main>
                    <p>Main content here</p>
                </main>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        reader = URLReader()
        result = reader.read("https://example.com/test")

        assert result.success is True
        assert result.title == "Test Page"
        assert "Main content" in result.content

    @patch("httpx.Client.get")
    def test_http_error(self, mock_get):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason_phrase = "Not Found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found",
            request=Mock(),
            response=mock_response,
        )
        mock_get.return_value = mock_response

        reader = URLReader()
        result = reader.read("https://example.com/missing")

        assert result.success is False
        assert "404" in result.error

    def test_read_multiple(self):
        """Test reading multiple URLs."""
        with patch.object(URLReader, "read") as mock_read:
            mock_read.return_value = ReadResult(
                url="https://example.com",
                title="Test",
                content="Content",
                success=True,
            )

            reader = URLReader()
            results = reader.read_multiple([
                "https://example1.com",
                "https://example2.com",
            ])

            assert len(results) == 2
            assert mock_read.call_count == 2

    def test_context_manager(self):
        """Test context manager functionality."""
        with URLReader() as reader:
            assert reader._client is None  # Lazy loaded

        # Client should be closed after context
        assert reader._client is None


class TestURLReaderContentExtraction:
    """Tests for content extraction logic."""

    @patch("httpx.Client.get")
    def test_extracts_article_content(self, mock_get):
        """Test that article content is preferred."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <nav>Navigation</nav>
                <article>
                    <p>Article content should be extracted</p>
                </article>
                <footer>Footer</footer>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        reader = URLReader()
        result = reader.read("https://example.com")

        assert "Article content" in result.content
        assert "Navigation" not in result.content
        assert "Footer" not in result.content

    @patch("httpx.Client.get")
    def test_removes_script_tags(self, mock_get):
        """Test that script tags are removed."""
        mock_response = Mock()
        mock_response.text = """
        <html>
            <body>
                <p>Real content</p>
                <script>alert('should not appear');</script>
            </body>
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        reader = URLReader()
        result = reader.read("https://example.com")

        assert "Real content" in result.content
        assert "alert" not in result.content

    @patch("httpx.Client.get")
    def test_content_truncation(self, mock_get):
        """Test that very long content is truncated."""
        long_content = "x" * 100000
        mock_response = Mock()
        mock_response.text = f"<html><body><p>{long_content}</p></body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        reader = URLReader(max_content_length=1000)
        result = reader.read("https://example.com")

        assert len(result.content) < 100000
        assert "truncated" in result.content.lower()
