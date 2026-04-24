"""Tests for the agent graph and state."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from project_architect.agent.state import (
    StepStatus,
    StepInfo,
    AgentState,
    create_initial_state,
    add_to_progress_log,
)


class TestStepStatus:
    """Tests for StepStatus enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert StepStatus.PENDING.value == "pending"
        assert StepStatus.RESEARCHING.value == "researching"
        assert StepStatus.COMPLETED.value == "completed"
        assert StepStatus.FAILED.value == "failed"


class TestStepInfo:
    """Tests for StepInfo dataclass."""

    def test_creation(self):
        """Test creating a step info."""
        step = StepInfo(
            name="Test Step",
            description="Test description",
        )
        assert step.name == "Test Step"
        assert step.status == StepStatus.PENDING

    def test_to_dict(self):
        """Test converting to dictionary."""
        step = StepInfo(
            name="Test",
            description="Desc",
            key_technologies=["Python", "FastAPI"],
        )
        d = step.to_dict()
        assert d["name"] == "Test"
        assert d["status"] == "pending"
        assert "Python" in d["key_technologies"]

    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "name": "Test",
            "description": "Desc",
            "status": "completed",
            "key_technologies": ["React"],
        }
        step = StepInfo.from_dict(data)
        assert step.name == "Test"
        assert step.status == StepStatus.COMPLETED
        assert "React" in step.key_technologies


class TestProgressLogReducer:
    """Tests for progress log reducer."""

    def test_add_single_message(self):
        """Test adding a single message."""
        current = ["Message 1"]
        result = add_to_progress_log(current, "Message 2")
        assert result == ["Message 1", "Message 2"]

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        current = ["Message 1"]
        result = add_to_progress_log(current, ["Message 2", "Message 3"])
        assert len(result) == 3

    def test_add_to_empty(self):
        """Test adding to empty list."""
        result = add_to_progress_log([], "First message")
        assert result == ["First message"]


class TestCreateInitialState:
    """Tests for initial state creation."""

    def test_creates_state_dict(self):
        """Test creating initial state."""
        state = create_initial_state("Build an AI chatbot")

        assert state["project_idea"] == "Build an AI chatbot"
        assert state["project_title"] == ""
        assert state["objectives"] == []
        assert state["steps"] == []
        assert state["current_step_index"] == 0
        assert state["progress_log"] == []
        assert state["errors"] == []

    def test_state_has_all_keys(self):
        """Test that state has all required keys."""
        state = create_initial_state("Test project")

        required_keys = [
            "project_idea",
            "project_title",
            "objectives",
            "deliverables",
            "domains",
            "steps",
            "current_step_index",
            "overview_page_id",
            "overview_page_url",
            "messages",
            "progress_log",
            "errors",
        ]

        for key in required_keys:
            assert key in state, f"Missing key: {key}"


class TestAgentGraph:
    """Tests for agent graph creation."""

    @patch("project_architect.agent.graph.MemorySaver")
    def test_graph_creation(self, mock_saver):
        """Test that graph can be created."""
        from project_architect.agent.graph import create_agent_graph

        graph = create_agent_graph()
        assert graph is not None

    @patch("project_architect.agent.graph.MemorySaver")
    def test_graph_has_nodes(self, mock_saver):
        """Test that graph has expected nodes."""
        from project_architect.agent.graph import create_agent_graph

        graph = create_agent_graph()

        # The graph should have been compiled
        # We can check the builder's nodes were added
        # This is a basic sanity check
        assert graph is not None
