"""Tests for the Notion client tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from project_architect.tools.notion_client import (
    NotionClient,
    NotionPage,
    NotionBlockBuilder,
)


class TestNotionPage:
    """Tests for NotionPage dataclass."""

    def test_creation(self):
        """Test creating a Notion page reference."""
        page = NotionPage(
            id="abc-123",
            url="https://notion.so/abc-123",
            title="Test Page",
        )
        assert page.id == "abc-123"
        assert page.title == "Test Page"

    def test_to_dict(self):
        """Test converting to dictionary."""
        page = NotionPage(
            id="abc-123",
            url="https://notion.so/abc-123",
            title="Test Page",
        )
        d = page.to_dict()
        assert d["id"] == "abc-123"
        assert d["url"] == "https://notion.so/abc-123"


class TestNotionBlockBuilder:
    """Tests for NotionBlockBuilder."""

    def test_heading_1(self):
        """Test creating heading 1 block."""
        block = NotionBlockBuilder.heading_1("Test Heading")
        assert block["type"] == "heading_1"
        assert block["heading_1"]["rich_text"][0]["text"]["content"] == "Test Heading"

    def test_heading_2(self):
        """Test creating heading 2 block."""
        block = NotionBlockBuilder.heading_2("Subheading")
        assert block["type"] == "heading_2"

    def test_paragraph(self):
        """Test creating paragraph block."""
        block = NotionBlockBuilder.paragraph("Test content")
        assert block["type"] == "paragraph"
        assert block["paragraph"]["rich_text"][0]["text"]["content"] == "Test content"

    def test_paragraph_bold(self):
        """Test creating bold paragraph."""
        block = NotionBlockBuilder.paragraph("Bold text", bold=True)
        assert block["paragraph"]["rich_text"][0]["annotations"]["bold"] is True

    def test_bulleted_list_item(self):
        """Test creating bulleted list item."""
        block = NotionBlockBuilder.bulleted_list_item("List item")
        assert block["type"] == "bulleted_list_item"

    def test_numbered_list_item(self):
        """Test creating numbered list item."""
        block = NotionBlockBuilder.numbered_list_item("Numbered item")
        assert block["type"] == "numbered_list_item"

    def test_divider(self):
        """Test creating divider."""
        block = NotionBlockBuilder.divider()
        assert block["type"] == "divider"

    def test_callout(self):
        """Test creating callout."""
        block = NotionBlockBuilder.callout("Important note", emoji="⚠️")
        assert block["type"] == "callout"
        assert block["callout"]["icon"]["emoji"] == "⚠️"

    def test_bookmark(self):
        """Test creating bookmark."""
        block = NotionBlockBuilder.bookmark("https://example.com", "Example")
        assert block["type"] == "bookmark"
        assert block["bookmark"]["url"] == "https://example.com"

    def test_link_to_page(self):
        """Test creating link to page."""
        block = NotionBlockBuilder.link_to_page("page-id-123")
        assert block["type"] == "link_to_page"
        assert block["link_to_page"]["page_id"] == "page-id-123"

    def test_code_block(self):
        """Test creating code block."""
        block = NotionBlockBuilder.code("print('hello')", language="python")
        assert block["type"] == "code"
        assert block["code"]["language"] == "python"


class TestNotionClient:
    """Tests for NotionClient."""

    @patch("project_architect.tools.notion_client.Client")
    def test_initialization(self, mock_client_class):
        """Test client initialization."""
        client = NotionClient(
            token="secret_test",
            parent_page_id="parent-id",
        )
        assert client.parent_page_id == "parent-id"
        mock_client_class.assert_called_once_with(auth="secret_test")

    @patch("project_architect.tools.notion_client.Client")
    def test_create_page(self, mock_client_class):
        """Test creating a page."""
        mock_client = MagicMock()
        mock_client.pages.create.return_value = {
            "id": "new-page-id",
            "url": "https://notion.so/new-page",
        }
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        page = client.create_page(title="Test Page")

        assert page.id == "new-page-id"
        assert page.title == "Test Page"
        mock_client.pages.create.assert_called_once()

    @patch("project_architect.tools.notion_client.Client")
    def test_create_page_with_children(self, mock_client_class):
        """Test creating a page with content blocks."""
        mock_client = MagicMock()
        mock_client.pages.create.return_value = {
            "id": "page-id",
            "url": "https://notion.so/page",
        }
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        children = [
            NotionBlockBuilder.heading_1("Title"),
            NotionBlockBuilder.paragraph("Content"),
        ]
        client.create_page(title="Test", children=children)

        call_kwargs = mock_client.pages.create.call_args[1]
        assert "children" in call_kwargs
        assert len(call_kwargs["children"]) == 2

    @patch("project_architect.tools.notion_client.Client")
    def test_append_blocks(self, mock_client_class):
        """Test appending blocks to a page."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        blocks = [NotionBlockBuilder.paragraph("New content")]
        client.append_blocks("page-id", blocks)

        mock_client.blocks.children.append.assert_called_once_with(
            block_id="page-id",
            children=blocks,
        )

    @patch("project_architect.tools.notion_client.Client")
    def test_create_project_overview(self, mock_client_class):
        """Test creating project overview page."""
        mock_client = MagicMock()
        mock_client.pages.create.return_value = {
            "id": "overview-id",
            "url": "https://notion.so/overview",
        }
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        page = client.create_project_overview(
            project_title="Test Project",
            objectives=["Objective 1", "Objective 2"],
            deliverables=["Deliverable 1"],
            domains=["AI", "Web"],
            steps=[
                {"name": "Step 1", "description": "First step"},
                {"name": "Step 2", "description": "Second step"},
            ],
        )

        assert page.id == "overview-id"
        call_kwargs = mock_client.pages.create.call_args[1]
        assert "children" in call_kwargs
        # Should have multiple blocks for sections
        assert len(call_kwargs["children"]) > 5

    @patch("project_architect.tools.notion_client.Client")
    def test_create_step_page(self, mock_client_class):
        """Test creating step documentation page."""
        mock_client = MagicMock()
        mock_client.pages.create.return_value = {
            "id": "step-id",
            "url": "https://notion.so/step",
        }
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        page = client.create_step_page(
            step_number=1,
            step_name="Requirements",
            step_description="Define requirements",
            objective="Gather all project requirements",
            key_technologies=["Python", "FastAPI"],
            methods_and_tools=["Use user interviews"],
            detailed_content="Detailed guidance here...",
            references=[{"title": "Guide", "url": "https://guide.com"}],
            parent_page_id="overview-id",
        )

        assert page.id == "step-id"
        call_kwargs = mock_client.pages.create.call_args[1]
        assert call_kwargs["parent"]["page_id"] == "overview-id"

    @patch("project_architect.tools.notion_client.Client")
    def test_update_overview_with_step_links(self, mock_client_class):
        """Test updating overview with step links."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        client = NotionClient(token="secret", parent_page_id="parent")
        step_pages = [
            NotionPage(id="step1-id", url="https://notion.so/step1", title="Step 1"),
            NotionPage(id="step2-id", url="https://notion.so/step2", title="Step 2"),
        ]
        client.update_overview_with_step_links("overview-id", step_pages)

        mock_client.blocks.children.append.assert_called_once()
        call_args = mock_client.blocks.children.append.call_args
        assert call_args[1]["block_id"] == "overview-id"
