"""
Outline Steps Node

Breaks down the project into actionable implementation steps.
This is STEP 2 in the workflow.
"""

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from project_architect.utils.prompts import PROMPTS
from project_architect.agent.state import StepStatus

logger = logging.getLogger(__name__)


def outline_steps(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """
    Break down the project into 4-7 actionable steps.

    STEP 2: OUTLINE THE PROJECT STEPS
    - Break the idea into 4-7 high-level steps or milestones
    - Each step describes an actionable phase
    - Store steps in state for later processing

    Args:
        state: Current agent state with project information
        config: Configuration containing LLM settings

    Returns:
        Updated state with steps list
    """
    logger.info("Step 2: Outlining project steps")

    # Get LLM from config
    llm = config["configurable"].get("llm")
    if not llm:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    # Format the prompt
    prompt = PROMPTS["outline_steps"].format(
        project_title=state["project_title"],
        objectives=", ".join(state["objectives"]),
        deliverables=", ".join(state["deliverables"]),
        domains=", ".join(state["domains"]),
    )

    # Call LLM
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = str(response.content)

        # Parse JSON response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        raw_steps = result["steps"]

        # Convert to step info dictionaries
        steps = []
        for step_data in raw_steps:
            steps.append({
                "name": step_data["name"],
                "description": step_data["description"],
                "status": StepStatus.PENDING.value,
                "search_results": [],
                "read_contents": [],
                "objective": "",
                "key_technologies": [],
                "methods_and_tools": [],
                "detailed_content": "",
                "references": [],
                "notion_page_id": None,
                "notion_page_url": None,
            })

        logger.info(f"Generated {len(steps)} project steps")

        # Format progress log
        steps_text = "\n".join(
            f"{i+1}. **{s['name']}**: {s['description']}"
            for i, s in enumerate(steps)
        )
        progress_message = f"---\n\n## Project Steps\n\n{steps_text}\n"

        return {
            "steps": steps,
            "current_step_index": 0,
            "progress_log": [progress_message],
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Failed to parse steps outline: {e}")

    except Exception as e:
        logger.error(f"Error in outline_steps: {e}")
        raise
