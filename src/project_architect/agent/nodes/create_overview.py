"""
Create Overview Node

Creates the main project overview page in Notion.
This is STEP 3 in the workflow.
"""

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from project_architect.tools.notion_client import NotionClient

logger = logging.getLogger(__name__)


def create_overview(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """
    Create the main project overview page in Notion.

    STEP 3: CREATE THE MAIN NOTION OVERVIEW PAGE
    - Title: Project Name
    - Sections: Objective, Step list with descriptions
    - Uses Notion API to create the page immediately

    Args:
        state: Current agent state with project and steps information
        config: Configuration containing Notion client settings

    Returns:
        Updated state with overview page ID and URL
    """
    logger.info("Step 3: Creating Notion overview page")

    # Get Notion client from config
    notion_client: NotionClient = config["configurable"].get("notion_client")
    if not notion_client:
        raise ValueError("Notion client not configured")

    try:
        # Create the overview page
        overview_page = notion_client.create_project_overview(
            project_title=state["project_title"],
            objectives=state["objectives"],
            deliverables=state["deliverables"],
            domains=state["domains"],
            steps=state["steps"],
        )

        logger.info(f"Created overview page: {overview_page.title} ({overview_page.id})")

        progress_message = (
            f"---\n\n"
            f"## Notion Workspace Created\n\n"
            f"Created project overview page: [{state['project_title']}]({overview_page.url})\n\n"
            f"Now beginning research for each step...\n"
        )

        return {
            "overview_page_id": overview_page.id,
            "overview_page_url": overview_page.url,
            "progress_log": [progress_message],
        }

    except Exception as e:
        logger.error(f"Failed to create overview page: {e}")
        raise
