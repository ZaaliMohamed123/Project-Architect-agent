"""Tests for the search tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from project_architect.tools.search import (
    SearchTool,
    SearchResult,
    GoogleSearchProvider,
    DuckDuckGoSearchProvider,
)


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            title="Test Title",
            url="https://example.com",
            snippet="Test snippet",
            source="google",
        )
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.snippet == "Test snippet"
        assert result.source == "google"

    def test_to_dict(self):
        """Test converting search result to dict."""
        result = SearchResult(
            title="Test",
            url="https://test.com",
            snippet="Snippet",
            source="duckduckgo",
        )
        d = result.to_dict()
        assert d["title"] == "Test"
        assert d["url"] == "https://test.com"
        assert d["source"] == "duckduckgo"


class TestDuckDuckGoSearchProvider:
    """Tests for DuckDuckGo search provider."""

    @patch("project_architect.tools.search.DDGS")
    def test_search_returns_results(self, mock_ddgs_class):
        """Test that DuckDuckGo search returns results."""
        # Setup mock
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=None)
        mock_ddgs.text.return_value = [
            {"title": "Result 1", "href": "https://example1.com", "body": "Snippet 1"},
            {"title": "Result 2", "href": "https://example2.com", "body": "Snippet 2"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        provider = DuckDuckGoSearchProvider()
        results = provider.search("test query", num_results=5)

        assert len(results) == 2
        assert results[0].title == "Result 1"
        assert results[0].source == "duckduckgo"
        assert results[1].url == "https://example2.com"

    @patch("project_architect.tools.search.DDGS")
    def test_search_with_time_filter(self, mock_ddgs_class):
        """Test search with time filter."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=None)
        mock_ddgs.text.return_value = []
        mock_ddgs_class.return_value = mock_ddgs

        provider = DuckDuckGoSearchProvider()
        provider.search("test", time_filter="m")

        mock_ddgs.text.assert_called_once()
        call_kwargs = mock_ddgs.text.call_args
        assert call_kwargs[1]["timelimit"] == "m"


class TestSearchTool:
    """Tests for the unified SearchTool."""

    def test_init_without_google(self):
        """Test initialization without Google credentials."""
        tool = SearchTool()
        assert tool.primary_provider == "duckduckgo"
        assert tool._google_provider is None

    def test_init_with_google(self):
        """Test initialization with Google credentials."""
        tool = SearchTool(
            google_api_key="test-key",
            google_search_engine_id="test-cx",
        )
        assert tool.primary_provider == "google"
        assert tool._google_provider is not None

    @patch("project_architect.tools.search.DDGS")
    def test_search_uses_duckduckgo_fallback(self, mock_ddgs_class):
        """Test that search falls back to DuckDuckGo."""
        mock_ddgs = MagicMock()
        mock_ddgs.__enter__ = Mock(return_value=mock_ddgs)
        mock_ddgs.__exit__ = Mock(return_value=None)
        mock_ddgs.text.return_value = [
            {"title": "DDG Result", "href": "https://ddg.com", "body": "DDG Snippet"},
        ]
        mock_ddgs_class.return_value = mock_ddgs

        tool = SearchTool()  # No Google config
        results = tool.search("test query")

        assert len(results) == 1
        assert results[0].source == "duckduckgo"

    def test_search_for_step(self):
        """Test search_for_step constructs appropriate query."""
        with patch.object(SearchTool, "search") as mock_search:
            mock_search.return_value = []

            tool = SearchTool()
            tool.search_for_step(
                step_name="Data Collection",
                step_description="Gather training data",
                project_context="ML Project",
            )

            # Check that search was called with appropriate query
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            query = call_args[1]["query"]
            assert "Data Collection" in query
            assert "best practices" in query
