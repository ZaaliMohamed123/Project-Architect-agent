"""
State schema for the Project Architect agent.

Defines the typed state that flows through the LangGraph workflow.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Annotated, Any, Optional

from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class StepStatus(str, Enum):
    """Status of a project step."""

    PENDING = "pending"
    RESEARCHING = "researching"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StepInfo:
    """Information about a project step."""

    name: str
    description: str
    status: StepStatus = StepStatus.PENDING

    # Research results
    search_results: list[dict] = field(default_factory=list)
    read_contents: list[dict] = field(default_factory=list)

    # Synthesized content
    objective: str = ""
    key_technologies: list[str] = field(default_factory=list)
    methods_and_tools: list[str] = field(default_factory=list)
    detailed_content: str = ""
    references: list[dict] = field(default_factory=list)

    # Notion page reference
    notion_page_id: Optional[str] = None
    notion_page_url: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "search_results": self.search_results,
            "read_contents": self.read_contents,
            "objective": self.objective,
            "key_technologies": self.key_technologies,
            "methods_and_tools": self.methods_and_tools,
            "detailed_content": self.detailed_content,
            "references": self.references,
            "notion_page_id": self.notion_page_id,
            "notion_page_url": self.notion_page_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StepInfo":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            status=StepStatus(data.get("status", "pending")),
            search_results=data.get("search_results", []),
            read_contents=data.get("read_contents", []),
            objective=data.get("objective", ""),
            key_technologies=data.get("key_technologies", []),
            methods_and_tools=data.get("methods_and_tools", []),
            detailed_content=data.get("detailed_content", ""),
            references=data.get("references", []),
            notion_page_id=data.get("notion_page_id"),
            notion_page_url=data.get("notion_page_url"),
        )


def add_to_progress_log(
    current: list[str], new: list[str] | str
) -> list[str]:
    """Reducer for progress log - appends new entries."""
    if isinstance(new, str):
        new = [new]
    return current + new


class ProjectArchitectState:
    """
    State schema for the Project Architect agent.

    This is implemented as a TypedDict-compatible class for LangGraph.
    """

    # Input
    project_idea: str

    # Extracted project information
    project_title: str
    objectives: list[str]
    deliverables: list[str]
    domains: list[str]

    # Steps (4-7 items)
    steps: list[dict]  # List of StepInfo as dicts
    current_step_index: int

    # Notion tracking
    overview_page_id: Optional[str]
    overview_page_url: Optional[str]

    # Progress tracking for UI
    messages: Annotated[list[BaseMessage], add_messages]
    progress_log: Annotated[list[str], add_to_progress_log]

    # Error tracking
    errors: list[str]


# TypedDict version for LangGraph compatibility
from typing import TypedDict


class AgentState(TypedDict):
    """TypedDict state for LangGraph compatibility."""

    # Input
    project_idea: str

    # Extracted project information
    project_title: str
    objectives: list[str]
    deliverables: list[str]
    domains: list[str]

    # Steps
    steps: list[dict]
    current_step_index: int

    # Notion tracking
    overview_page_id: str
    overview_page_url: str

    # Progress tracking
    messages: Annotated[list[BaseMessage], add_messages]
    progress_log: Annotated[list[str], add_to_progress_log]

    # Error tracking
    errors: list[str]


def create_initial_state(project_idea: str) -> dict[str, Any]:
    """Create the initial state for a new project."""
    return {
        "project_idea": project_idea,
        "project_title": "",
        "objectives": [],
        "deliverables": [],
        "domains": [],
        "steps": [],
        "current_step_index": 0,
        "overview_page_id": "",
        "overview_page_url": "",
        "messages": [],
        "progress_log": [],
        "errors": [],
    }
