"""
Notion API client for creating and managing documentation pages.

Provides high-level methods for creating structured documentation
in a Notion workspace.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


@dataclass
class NotionPage:
    """Represents a created Notion page."""

    id: str
    url: str
    title: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
        }


class NotionBlockBuilder:
    """Helper class for building Notion block structures."""

    @staticmethod
    def heading_1(text: str, color: str = "default") -> dict:
        """Create a heading 1 block."""
        return {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "color": color,
            },
        }

    @staticmethod
    def heading_2(text: str, color: str = "default") -> dict:
        """Create a heading 2 block."""
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "color": color,
            },
        }

    @staticmethod
    def heading_3(text: str, color: str = "default") -> dict:
        """Create a heading 3 block."""
        return {
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "color": color,
            },
        }

    @staticmethod
    def paragraph(text: str, bold: bool = False) -> dict:
        """Create a paragraph block."""
        annotations = {"bold": bold} if bold else {}
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": text},
                        "annotations": annotations,
                    }
                ],
            },
        }

    @staticmethod
    def paragraph_with_link(text: str, link_text: str, url: str) -> dict:
        """Create a paragraph with a link."""
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": text}},
                    {
                        "type": "text",
                        "text": {"content": link_text, "link": {"url": url}},
                        "annotations": {"color": "blue"},
                    },
                ],
            },
        }

    @staticmethod
    def bulleted_list_item(text: str) -> dict:
        """Create a bulleted list item."""
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            },
        }

    @staticmethod
    def numbered_list_item(text: str) -> dict:
        """Create a numbered list item."""
        return {
            "object": "block",
            "type": "numbered_list_item",
            "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            },
        }

    @staticmethod
    def divider() -> dict:
        """Create a divider block."""
        return {"object": "block", "type": "divider", "divider": {}}

    @staticmethod
    def callout(text: str, emoji: str = "💡", color: str = "gray_background") -> dict:
        """Create a callout block."""
        return {
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
                "icon": {"type": "emoji", "emoji": emoji},
                "color": color,
            },
        }

    @staticmethod
    def bookmark(url: str, caption: str = "") -> dict:
        """Create a bookmark block."""
        block = {
            "object": "block",
            "type": "bookmark",
            "bookmark": {"url": url},
        }
        if caption:
            block["bookmark"]["caption"] = [{"type": "text", "text": {"content": caption}}]
        return block

    @staticmethod
    def link_to_page(page_id: str) -> dict:
        """Create a link to another Notion page."""
        return {
            "object": "block",
            "type": "link_to_page",
            "link_to_page": {"type": "page_id", "page_id": page_id},
        }

    @staticmethod
    def page_mention(page_id: str, prefix_text: str = "") -> dict:
        """Create a paragraph with a page mention."""
        rich_text = []
        if prefix_text:
            rich_text.append({"type": "text", "text": {"content": prefix_text}})
        rich_text.append(
            {"type": "mention", "mention": {"type": "page", "page": {"id": page_id}}}
        )
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_text},
        }

    @staticmethod
    def toggle(text: str, children: list[dict] = None) -> dict:
        """Create a toggle block."""
        block = {
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": text}}],
            },
        }
        if children:
            block["toggle"]["children"] = children
        return block

    @staticmethod
    def code(code: str, language: str = "plain text") -> dict:
        """Create a code block."""
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code}}],
                "language": language,
            },
        }


class NotionClient:
    """
    High-level Notion client for project documentation.

    Provides methods for creating structured documentation pages
    with rich content blocks.
    """

    def __init__(self, token: str, parent_page_id: str):
        self.client = Client(auth=token)
        self.parent_page_id = parent_page_id
        self.block = NotionBlockBuilder()

        logger.info("NotionClient initialized")

    def create_page(
        self,
        title: str,
        children: list[dict] = None,
        icon_emoji: str = None,
        parent_page_id: str = None,
    ) -> NotionPage:
        """
        Create a new Notion page.

        Args:
            title: Page title
            children: List of block objects to add as content
            icon_emoji: Optional emoji icon for the page
            parent_page_id: Parent page ID (defaults to configured parent)

        Returns:
            NotionPage object with id, url, and title
        """
        parent_id = parent_page_id or self.parent_page_id

        page_data: dict[str, Any] = {
            "parent": {"page_id": parent_id},
            "properties": {
                "title": {"title": [{"text": {"content": title}}]},
            },
        }

        if icon_emoji:
            page_data["icon"] = {"type": "emoji", "emoji": icon_emoji}

        if children:
            page_data["children"] = children

        try:
            response = self.client.pages.create(**page_data)

            page = NotionPage(
                id=response["id"],
                url=response["url"],
                title=title,
            )

            logger.info(f"Created Notion page: {title} ({page.id})")
            return page

        except APIResponseError as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise

    def append_blocks(self, page_id: str, blocks: list[dict]) -> None:
        """
        Append blocks to an existing page.

        Args:
            page_id: The page ID to append to
            blocks: List of block objects to append
        """
        try:
            self.client.blocks.children.append(block_id=page_id, children=blocks)
            logger.info(f"Appended {len(blocks)} blocks to page {page_id}")

        except APIResponseError as e:
            logger.error(f"Failed to append blocks: {e}")
            raise

    def update_page_icon(self, page_id: str, emoji: str) -> None:
        """Update a page's icon emoji."""
        try:
            self.client.pages.update(page_id=page_id, icon={"type": "emoji", "emoji": emoji})
            logger.info(f"Updated icon for page {page_id}")

        except APIResponseError as e:
            logger.error(f"Failed to update page icon: {e}")
            raise

    def create_project_overview(
        self,
        project_title: str,
        objectives: list[str],
        deliverables: list[str],
        domains: list[str],
        steps: list[dict],
    ) -> NotionPage:
        """
        Create the main project overview page.

        Args:
            project_title: Title of the project
            objectives: List of project objectives
            deliverables: List of project deliverables
            domains: List of technical domains
            steps: List of step dictionaries with 'name' and 'description'

        Returns:
            NotionPage object for the overview page
        """
        children = []

        # Objective section
        children.append(self.block.heading_2("Objective"))
        for obj in objectives:
            children.append(self.block.bulleted_list_item(obj))

        children.append(self.block.divider())

        # Deliverables section
        children.append(self.block.heading_2("Deliverables"))
        for deliverable in deliverables:
            children.append(self.block.bulleted_list_item(deliverable))

        children.append(self.block.divider())

        # Technical domains
        children.append(self.block.heading_2("Technical Domains"))
        domains_text = ", ".join(domains)
        children.append(self.block.paragraph(domains_text))

        children.append(self.block.divider())

        # Steps section (placeholder - will be updated with links)
        children.append(self.block.heading_2("Project Steps"))
        children.append(
            self.block.callout(
                "Click on each step below to see detailed research and implementation guidance.",
                emoji="📋",
            )
        )

        for i, step in enumerate(steps, 1):
            step_text = f"Step {i}: {step['name']} - {step['description']}"
            children.append(self.block.numbered_list_item(step_text))

        return self.create_page(
            title=f"📚 {project_title}",
            children=children,
            icon_emoji="📚",
        )

    def create_step_page(
        self,
        step_number: int,
        step_name: str,
        step_description: str,
        objective: str,
        key_technologies: list[str],
        methods_and_tools: list[str],
        detailed_content: str,
        references: list[dict],
        parent_page_id: str,
    ) -> NotionPage:
        """
        Create a detailed page for a project step.

        Args:
            step_number: The step number (1-indexed)
            step_name: Name of the step
            step_description: Brief description
            objective: What this step aims to achieve
            key_technologies: List of relevant technologies
            methods_and_tools: List of recommended methods and tools
            detailed_content: Main content/explanation
            references: List of reference dicts with 'title' and 'url'
            parent_page_id: Parent page ID (typically the overview page)

        Returns:
            NotionPage object for the step page
        """
        children = []

        # Step objective
        children.append(self.block.heading_2("Step Objective"))
        children.append(self.block.paragraph(objective))

        children.append(self.block.divider())

        # Key technologies
        children.append(self.block.heading_2("Key Technologies"))
        for tech in key_technologies:
            children.append(self.block.bulleted_list_item(tech))

        children.append(self.block.divider())

        # Recommended methods & tools
        children.append(self.block.heading_2("Recommended Methods & Tools"))
        for method in methods_and_tools:
            children.append(self.block.bulleted_list_item(method))

        children.append(self.block.divider())

        # Detailed content
        children.append(self.block.heading_2("Detailed Guidance"))

        # Split content into paragraphs
        paragraphs = detailed_content.split("\n\n")
        for para in paragraphs:
            if para.strip():
                # Check if it's a subheading (starts with ##)
                if para.strip().startswith("## "):
                    children.append(self.block.heading_3(para.strip()[3:]))
                elif para.strip().startswith("- "):
                    # It's a list
                    for item in para.strip().split("\n"):
                        if item.strip().startswith("- "):
                            children.append(
                                self.block.bulleted_list_item(item.strip()[2:])
                            )
                else:
                    children.append(self.block.paragraph(para.strip()))

        children.append(self.block.divider())

        # References
        children.append(self.block.heading_2("References"))
        if references:
            for ref in references:
                children.append(self.block.bookmark(ref["url"], ref.get("title", "")))
        else:
            children.append(self.block.paragraph("No external references for this step."))

        # Step emoji based on number
        step_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        emoji = step_emojis[step_number - 1] if step_number <= 10 else "📝"

        return self.create_page(
            title=f"Step {step_number}: {step_name}",
            children=children,
            icon_emoji=emoji,
            parent_page_id=parent_page_id,
        )

    def update_overview_with_step_links(
        self,
        overview_page_id: str,
        step_pages: list[NotionPage],
    ) -> None:
        """
        Update the overview page with links to step pages.

        Appends a section with direct links to each step page.

        Args:
            overview_page_id: The overview page ID
            step_pages: List of NotionPage objects for each step
        """
        blocks = []

        blocks.append(self.block.divider())
        blocks.append(self.block.heading_2("Quick Navigation"))
        blocks.append(
            self.block.callout(
                "Click any step below to jump directly to its detailed documentation.",
                emoji="🔗",
            )
        )

        for page in step_pages:
            blocks.append(self.block.link_to_page(page.id))

        self.append_blocks(overview_page_id, blocks)
        logger.info(f"Updated overview page with {len(step_pages)} step links")
