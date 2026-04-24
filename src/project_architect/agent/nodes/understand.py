"""
Understand Project Node

Analyzes the project idea and extracts structured information.
This is STEP 1 in the workflow.
"""

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from project_architect.utils.prompts import PROMPTS

logger = logging.getLogger(__name__)


def understand_project(state: dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    """
    Analyze the project idea and extract structured information.

    STEP 1: UNDERSTAND THE PROJECT IDEA
    - Restate the idea clearly
    - Identify goals, deliverables, and end users
    - Infer main domains or technical areas

    Args:
        state: Current agent state containing project_idea
        config: Configuration containing LLM settings

    Returns:
        Updated state with extracted project information
    """
    logger.info("Step 1: Understanding project idea")

    project_idea = state["project_idea"]

    # Get LLM from config
    llm = config["configurable"].get("llm")
    if not llm:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    # Format the prompt
    prompt = PROMPTS["understand_project"].format(project_idea=project_idea)

    # Call LLM
    response_text = ""
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        response_text = str(response.content)

        # Parse JSON response
        # Handle potential markdown code blocks
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())

        logger.info(f"Extracted project title: {result['project_title']}")
        logger.info(f"Found {len(result['objectives'])} objectives")
        logger.info(f"Found {len(result['deliverables'])} deliverables")
        logger.info(f"Identified domains: {result['domains']}")

        return {
            "project_title": result["project_title"],
            "objectives": result["objectives"],
            "deliverables": result["deliverables"],
            "domains": result["domains"],
            "progress_log": [
                f"## Project Analysis Complete\n\n"
                f"**Project Title:** {result['project_title']}\n\n"
                f"**Objectives:**\n" + "\n".join(f"- {obj}" for obj in result["objectives"]) + "\n\n"
                f"**Deliverables:**\n" + "\n".join(f"- {d}" for d in result["deliverables"]) + "\n\n"
                f"**Technical Domains:** {', '.join(result['domains'])}\n"
            ],
            "messages": [
                HumanMessage(content=project_idea),
                AIMessage(content=f"I've analyzed your project idea: {result['project_title']}"),
            ],
        }

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        logger.error(f"Response was: {response_text}")
        raise ValueError(f"Failed to parse project analysis: {e}")

    except Exception as e:
        logger.error(f"Error in understand_project: {e}")
        raise
