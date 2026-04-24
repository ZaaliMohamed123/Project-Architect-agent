"""
Finalize Node

Updates the overview page with links and provides completion summary.
This is STEP 5 in the workflow.
"""

import logging
from typing import Any

from langchain_core.runnables import RunnableConfig

from project_architect.tools.notion_client import NotionClient, NotionPage

logger = logging.getLogger(__name__)


def finalize_documentation(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """
    Finalize the documentation by updating links and providing summary.

    STEP 5: FINALIZE
    - Update Overview page with proper Notion page links
    - Provide completion summary to the user

    Args:
        state: Current agent state with all step information
        config: Configuration containing Notion client

    Returns:
        Updated state with final progress log
    """
    logger.info("Step 5: Finalizing documentation")

    # Get Notion client from config
    notion_client: NotionClient = config["configurable"].get("notion_client")

    # Collect step pages
    step_pages = []
    for i, step in enumerate(state["steps"], 1):
        if step.get("notion_page_id") and step.get("notion_page_url"):
            step_pages.append(
                NotionPage(
                    id=step["notion_page_id"],
                    url=step["notion_page_url"],
                    title=f"Step {i}: {step['name']}",
                )
            )

    # Update overview page with links
    if notion_client and state.get("overview_page_id") and step_pages:
        try:
            notion_client.update_overview_with_step_links(
                overview_page_id=state["overview_page_id"],
                step_pages=step_pages,
            )
            logger.info(f"Updated overview page with {len(step_pages)} step links")
        except Exception as e:
            logger.error(f"Failed to update overview with links: {e}")

    # Count completed steps
    completed_count = sum(
        1 for step in state["steps"]
        if step.get("status") == "completed"
    )
    total_steps = len(state["steps"])

    # Build final summary
    step_links = "\n".join(
        f"- [{page.title}]({page.url})"
        for page in step_pages
    )

    # Handle case where no pages were created
    if not step_links:
        step_links = "*(No step pages were created)*"

    final_message = (
        f"---\n\n"
        f"## Documentation Complete!\n\n"
        f"**Project:** {state['project_title']}\n\n"
        f"**Status:** {completed_count}/{total_steps} steps completed\n\n"
        f"**Overview Page:** [{state['project_title']}]({state.get('overview_page_url', '#')})\n\n"
        f"**Step Documentation:**\n{step_links}\n\n"
    )

    # Add any errors
    if state.get("errors"):
        error_list = "\n".join(f"- {e}" for e in state["errors"])
        final_message += f"\n**Warnings:**\n{error_list}\n"

    final_message += (
        f"\n---\n\n"
        f"Your project documentation is ready! "
        f"Visit the Notion workspace to view and edit the detailed documentation.\n"
    )

    logger.info(f"Finalization complete: {completed_count}/{total_steps} steps documented")

    return {
        "progress_log": [final_message],
    }
