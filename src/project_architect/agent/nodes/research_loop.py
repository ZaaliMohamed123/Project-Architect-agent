"""
Research Loop Node

Performs iterative research for each project step.
This is STEP 4 in the workflow.
"""

import json
import logging
from typing import Any, Literal

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from project_architect.tools.search import SearchTool
from project_architect.tools.reader import URLReader
from project_architect.tools.notion_client import NotionClient
from project_architect.utils.prompts import PROMPTS
from project_architect.agent.state import StepStatus

logger = logging.getLogger(__name__)


def research_step(
    state: dict[str, Any], config: RunnableConfig
) -> Command[Literal["research_step", "finalize"]]:
    """
    Research and document a single project step.

    STEP 4: ITERATIVE RESEARCH & DOCUMENTATION LOOP
    For each step:
    1. REFLECT: Describe what this step needs
    2. SEARCH: Find top results about this step
    3. READ: Extract insights from relevant URLs (1-2 max)
    4. SYNTHESIZE: Combine into structured summary
    5. WRITE TO NOTION: Create step page immediately

    Args:
        state: Current agent state
        config: Configuration with tools and LLM

    Returns:
        Command to either continue loop or finalize
    """
    current_index = state["current_step_index"]
    steps = state["steps"]
    total_steps = len(steps)

    if current_index >= total_steps:
        logger.info("All steps researched, moving to finalize")
        return Command(goto="finalize")

    step = steps[current_index]
    step_number = current_index + 1

    logger.info(f"Researching step {step_number}/{total_steps}: {step['name']}")

    # Get tools from config
    llm = config["configurable"].get("llm")
    if not llm:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    search_tool: SearchTool = config["configurable"].get("search_tool")
    url_reader: URLReader = config["configurable"].get("url_reader")
    notion_client: NotionClient = config["configurable"].get("notion_client")

    progress_messages = []

    # Progress: Starting step research
    progress_messages.append(
        f"---\n\n"
        f"## Step {step_number} of {total_steps}: {step['name']}\n\n"
        f"**Status:** Researching...\n\n"
    )

    try:
        # 1. REFLECT: Generate search queries
        reflect_prompt = PROMPTS["reflect_on_step"].format(
            project_title=state["project_title"],
            domains=", ".join(state["domains"]),
            step_name=step["name"],
            step_description=step["description"],
        )

        reflect_response = llm.invoke([HumanMessage(content=reflect_prompt)])
        reflect_text = str(reflect_response.content)

        # Parse reflection
        if "```json" in reflect_text:
            reflect_text = reflect_text.split("```json")[1].split("```")[0]
        elif "```" in reflect_text:
            reflect_text = reflect_text.split("```")[1].split("```")[0]

        reflection = json.loads(reflect_text.strip())
        search_queries = reflection.get("search_queries", [f"{step['name']} best practices 2026"])

        logger.info(f"Generated {len(search_queries)} search queries")

        # 2. SEARCH: Execute searches
        all_search_results = []
        if search_tool:
            for query in search_queries[:2]:  # Limit to 2 queries
                results = search_tool.search(query, num_results=3, recent_only=True)
                all_search_results.extend(results)

                progress_messages.append(
                    f"**Research Progress:**\n"
                    f"- Searched for: `{query}`\n"
                    f"- Found {len(results)} results\n\n"
                )

        # 3. READ: Extract content from top URLs
        read_contents = []
        urls_to_read = []

        # Get unique URLs
        seen_urls = set()
        for result in all_search_results:
            if result.url not in seen_urls:
                urls_to_read.append(result.url)
                seen_urls.add(result.url)

        # Read top 1-2 URLs
        max_urls = config["configurable"].get("max_urls_per_step", 2)
        if url_reader and urls_to_read:
            urls_reading = urls_to_read[:max_urls]
            progress_messages.append(
                f"- Reading {len(urls_reading)} sources:\n"
                + "\n".join(f"  - {url}" for url in urls_reading)
                + "\n\n"
            )

            for url in urls_reading:
                read_result = url_reader.read(url)
                if read_result.success:
                    read_contents.append({
                        "url": read_result.url,
                        "title": read_result.title,
                        "content": read_result.content[:5000],  # Limit content
                    })
                    logger.info(f"Read {len(read_result.content)} chars from {url}")

        # 4. SYNTHESIZE: Combine research into structured content
        research_content = ""
        for i, search_result in enumerate(all_search_results[:5], 1):
            research_content += f"\n### Search Result {i}\n"
            research_content += f"Title: {search_result.title}\n"
            research_content += f"URL: {search_result.url}\n"
            research_content += f"Snippet: {search_result.snippet}\n"

        for i, read_content in enumerate(read_contents, 1):
            research_content += f"\n### Detailed Content {i}\n"
            research_content += f"Source: {read_content['url']}\n"
            research_content += f"Content:\n{read_content['content'][:3000]}\n"

        if not research_content:
            research_content = "No external research available. Please provide general best practices."

        synthesize_prompt = PROMPTS["synthesize_research"].format(
            project_title=state["project_title"],
            domains=", ".join(state["domains"]),
            step_number=step_number,
            step_name=step["name"],
            step_description=step["description"],
            research_content=research_content,
        )

        synth_response = llm.invoke([HumanMessage(content=synthesize_prompt)])
        synth_text = str(synth_response.content)

        # Parse synthesis
        if "```json" in synth_text:
            synth_text = synth_text.split("```json")[1].split("```")[0]
        elif "```" in synth_text:
            synth_text = synth_text.split("```")[1].split("```")[0]

        synthesis = json.loads(synth_text.strip())

        # Extract references from search results
        references = []
        for result in all_search_results[:3]:
            references.append({"title": result.title, "url": result.url})

        # 5. WRITE TO NOTION: Create step page
        step_page = None
        if notion_client:
            step_page = notion_client.create_step_page(
                step_number=step_number,
                step_name=step["name"],
                step_description=step["description"],
                objective=synthesis.get("objective", step["description"]),
                key_technologies=synthesis.get("key_technologies", []),
                methods_and_tools=synthesis.get("methods_and_tools", []),
                detailed_content=synthesis.get("detailed_content", ""),
                references=references,
                parent_page_id=state["overview_page_id"],
            )

            logger.info(f"Created step page: {step_page.title}")

        # Update step data
        updated_step = step.copy()
        updated_step["status"] = StepStatus.COMPLETED.value
        updated_step["search_results"] = [r.to_dict() for r in all_search_results[:5]]
        updated_step["read_contents"] = read_contents
        updated_step["objective"] = synthesis.get("objective", "")
        updated_step["key_technologies"] = synthesis.get("key_technologies", [])
        updated_step["methods_and_tools"] = synthesis.get("methods_and_tools", [])
        updated_step["detailed_content"] = synthesis.get("detailed_content", "")
        updated_step["references"] = references

        if step_page:
            updated_step["notion_page_id"] = step_page.id
            updated_step["notion_page_url"] = step_page.url

        # Update steps list
        updated_steps = steps.copy()
        updated_steps[current_index] = updated_step

        # Progress: Step complete
        tech_list = "\n".join(f"- {t}" for t in synthesis.get("key_technologies", [])[:5])
        progress_messages.append(
            f"**Step {step_number} Complete**\n\n"
            f"**Key Technologies:**\n{tech_list}\n\n"
        )

        if step_page:
            progress_messages.append(
                f"**Notion Page:** [{step_page.title}]({step_page.url})\n\n"
            )

        # Determine next action
        next_index = current_index + 1
        if next_index < total_steps:
            logger.info(f"Moving to step {next_index + 1}")
            return Command(
                update={
                    "steps": updated_steps,
                    "current_step_index": next_index,
                    "progress_log": progress_messages,
                },
                goto="research_step",  # Loop back
            )
        else:
            logger.info("All steps complete, moving to finalize")
            return Command(
                update={
                    "steps": updated_steps,
                    "current_step_index": next_index,
                    "progress_log": progress_messages,
                },
                goto="finalize",
            )

    except Exception as e:
        logger.error(f"Error researching step {step_number}: {e}")

        # Mark step as failed and continue
        updated_step = step.copy()
        updated_step["status"] = StepStatus.FAILED.value

        updated_steps = steps.copy()
        updated_steps[current_index] = updated_step

        progress_messages.append(
            f"**Error:** Failed to research step {step_number}: {str(e)}\n\n"
        )

        next_index = current_index + 1
        if next_index < total_steps:
            return Command(
                update={
                    "steps": updated_steps,
                    "current_step_index": next_index,
                    "progress_log": progress_messages,
                    "errors": [str(e)],
                },
                goto="research_step",
            )
        else:
            return Command(
                update={
                    "steps": updated_steps,
                    "current_step_index": next_index,
                    "progress_log": progress_messages,
                    "errors": [str(e)],
                },
                goto="finalize",
            )
