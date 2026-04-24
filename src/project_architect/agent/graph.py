"""
LangGraph State Graph Definition

Assembles the agent nodes into a complete workflow graph.
"""

import logging
from typing import Any

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from project_architect.agent.state import AgentState, create_initial_state
from project_architect.agent.nodes.understand import understand_project
from project_architect.agent.nodes.outline import outline_steps
from project_architect.agent.nodes.create_overview import create_overview
from project_architect.agent.nodes.research_loop import research_step
from project_architect.agent.nodes.finalize import finalize_documentation

logger = logging.getLogger(__name__)


def create_agent_graph():
    """
    Create the LangGraph state graph for the Project Architect agent.

    The graph follows this flow:
    START -> understand_project -> outline_steps -> create_overview ->
    research_step (loop) -> finalize -> END

    Returns:
        Compiled LangGraph graph ready for execution
    """
    logger.info("Creating agent graph")

    # Create the state graph
    builder = StateGraph(AgentState)

    # Add nodes
    builder.add_node("understand_project", understand_project)
    builder.add_node("outline_steps", outline_steps)
    builder.add_node("create_overview", create_overview)
    builder.add_node("research_step", research_step)
    builder.add_node("finalize", finalize_documentation)

    # Define the flow
    # START -> understand_project
    builder.add_edge(START, "understand_project")

    # understand_project -> outline_steps
    builder.add_edge("understand_project", "outline_steps")

    # outline_steps -> create_overview
    builder.add_edge("outline_steps", "create_overview")

    # create_overview -> research_step
    builder.add_edge("create_overview", "research_step")

    # research_step loops back to itself or goes to finalize
    # This is handled by the Command return in research_step node

    # finalize -> END
    builder.add_edge("finalize", END)

    # Compile the graph with memory checkpoint
    checkpointer = MemorySaver()
    graph = builder.compile(checkpointer=checkpointer)

    logger.info("Agent graph created successfully")
    return graph


def run_agent(
    project_idea: str,
    config: dict[str, Any],
    thread_id: str = "default",
):
    """
    Run the agent to process a project idea.

    Args:
        project_idea: The project idea to process
        config: Configuration dict with LLM and tool instances
        thread_id: Thread ID for checkpointing

    Yields:
        Progress updates as the agent runs
    """
    graph = create_agent_graph()

    # Create initial state
    initial_state = create_initial_state(project_idea)

    # Run the graph with streaming
    run_config = {
        "configurable": {
            **config,
            "thread_id": thread_id,
        }
    }

    logger.info(f"Starting agent run for: {project_idea[:50]}...")

    # Stream events from the graph
    for event in graph.stream(initial_state, config=run_config):
        # Extract progress log updates
        for node_name, node_output in event.items():
            if isinstance(node_output, dict):
                progress = node_output.get("progress_log", [])
                if progress:
                    for message in progress:
                        yield message

    logger.info("Agent run completed")


async def run_agent_async(
    project_idea: str,
    config: dict[str, Any],
    thread_id: str = "default",
):
    """
    Run the agent asynchronously.

    Args:
        project_idea: The project idea to process
        config: Configuration dict with LLM and tool instances
        thread_id: Thread ID for checkpointing

    Yields:
        Progress updates as the agent runs
    """
    graph = create_agent_graph()

    # Create initial state
    initial_state = create_initial_state(project_idea)

    # Run the graph with streaming
    run_config = {
        "configurable": {
            **config,
            "thread_id": thread_id,
        }
    }

    logger.info(f"Starting async agent run for: {project_idea[:50]}...")

    # Stream events from the graph
    async for event in graph.astream(initial_state, config=run_config):
        # Extract progress log updates
        for node_name, node_output in event.items():
            if isinstance(node_output, dict):
                progress = node_output.get("progress_log", [])
                if progress:
                    for message in progress:
                        yield message

    logger.info("Async agent run completed")
