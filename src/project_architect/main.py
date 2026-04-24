"""
Project Architect - Gradio Chatbot Interface

Main entry point for the application.
"""

import logging
import time
import uuid
from typing import Generator

import gradio as gr
from langchain_openai import ChatOpenAI

from project_architect.config.settings import get_settings
from project_architect.tools.search import SearchTool
from project_architect.tools.reader import URLReader
from project_architect.tools.notion_client import NotionClient
from project_architect.agent.graph import create_agent_graph, create_initial_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_tools_config():
    """Create and return tool instances from settings."""
    settings = get_settings()

    # Create LLM with optional base_url for OpenAI-compatible APIs
    llm_kwargs = {
        "model": settings.openai_model,
        "temperature": settings.openai_temperature,
        "api_key": settings.openai_api_key,
    }
    
    # Add base_url if configured (for Ollama, vLLM, LM Studio, etc.)
    if settings.openai_base_url:
        llm_kwargs["base_url"] = settings.openai_base_url
        logger.info(f"Using custom LLM endpoint: {settings.openai_base_url}")
    
    llm = ChatOpenAI(**llm_kwargs)

    # Create search tool
    search_tool = SearchTool(
        google_api_key=settings.google_api_key,
        google_search_engine_id=settings.google_search_engine_id,
    )

    # Create URL reader
    url_reader = URLReader()

    # Create Notion client
    notion_client = NotionClient(
        token=settings.notion_token,
        parent_page_id=settings.notion_parent_page_id,
    )

    return {
        "llm": llm,
        "search_tool": search_tool,
        "url_reader": url_reader,
        "notion_client": notion_client,
        "max_urls_per_step": settings.max_urls_per_step,
    }


def process_project_idea(
    message: str,
    history: list[dict],
) -> Generator[str, None, None]:
    """
    Process a project idea and stream progress updates.

    Args:
        message: The project idea from the user
        history: Chat history (not used but required by Gradio)

    Yields:
        Markdown-formatted progress updates
    """
    if not message.strip():
        yield "Please enter a project idea to get started."
        return

    start_time = time.time()
    thread_id = str(uuid.uuid4())

    # Initial message
    yield (
        "# Project Architect\n\n"
        "Starting analysis of your project idea...\n\n"
        "---\n\n"
    )

    try:
        # Create tools config
        logger.info("Creating tools configuration")
        config = create_tools_config()

        # Create the graph
        graph = create_agent_graph()

        # Create initial state
        initial_state = create_initial_state(message)

        # Run configuration
        run_config = {
            "configurable": {
                **config,
                "thread_id": thread_id,
            }
        }

        # Accumulate output
        accumulated_output = (
            "# Project Architect\n\n"
            "Starting analysis of your project idea...\n\n"
            "---\n\n"
        )

        # Stream the graph execution
        logger.info(f"Starting graph execution for thread {thread_id}")

        for event in graph.stream(initial_state, config=run_config):
            for node_name, node_output in event.items():
                if isinstance(node_output, dict):
                    progress = node_output.get("progress_log", [])
                    if progress:
                        for msg in progress:
                            accumulated_output += msg
                            yield accumulated_output

        # Add completion time
        elapsed_time = time.time() - start_time
        accumulated_output += f"\n*Completed in {elapsed_time:.1f} seconds*\n"
        yield accumulated_output

        logger.info(f"Graph execution completed in {elapsed_time:.1f}s")

    except ValueError as e:
        error_msg = str(e)
        if "OPENAI_API_KEY" in error_msg or "NOTION_TOKEN" in error_msg:
            yield (
                "# Configuration Error\n\n"
                f"**Error:** {error_msg}\n\n"
                "Please ensure your `.env` file is configured with:\n"
                "- `OPENAI_API_KEY`\n"
                "- `NOTION_TOKEN`\n"
                "- `NOTION_PARENT_PAGE_ID`\n\n"
                "See `.env.example` for the required format."
            )
        else:
            yield f"# Error\n\n**Error:** {error_msg}"

    except Exception as e:
        logger.exception(f"Error processing project idea: {e}")
        yield (
            "# Error\n\n"
            f"An unexpected error occurred: {str(e)}\n\n"
            "Please check your configuration and try again."
        )


def create_gradio_interface():
    """Create and return the Gradio interface."""

    # Custom CSS for better markdown rendering
    css = """
    .chatbot-message {
        font-size: 14px;
        line-height: 1.6;
    }
    .chatbot-message h1 { font-size: 1.5em; margin-top: 0.5em; }
    .chatbot-message h2 { font-size: 1.3em; margin-top: 0.5em; }
    .chatbot-message h3 { font-size: 1.1em; margin-top: 0.5em; }
    .chatbot-message code {
        background-color: rgba(0,0,0,0.1);
        padding: 0.1em 0.3em;
        border-radius: 3px;
    }
    """

    # Example project ideas
    examples = [
        "Build an AI-powered personal finance tracker that analyzes spending patterns and provides savings recommendations",
        "Create a real-time collaborative whiteboard application with video conferencing integration",
        "Develop an IoT home automation system that learns user preferences and optimizes energy usage",
        "Build a machine learning pipeline for sentiment analysis of customer reviews",
        "Create a microservices-based e-commerce platform with event-driven architecture",
    ]

    with gr.Blocks(
        title="Project Architect",
    ) as demo:
        gr.Markdown(
            """
            # Project Architect

            Transform your project idea into a complete, structured Notion workspace with
            research-backed documentation for each implementation step.

            **How it works:**
            1. Enter your project idea below
            2. The agent analyzes your idea and identifies key components
            3. It breaks down the project into actionable steps
            4. For each step, it researches best practices and technologies
            5. Everything is documented in your Notion workspace

            **Note:** Make sure your `.env` file is configured with your API keys.
            """
        )

        chatbot = gr.Chatbot(
            label="Project Documentation Assistant",
            height=600,
            render_markdown=True,
            avatar_images=(None, "https://em-content.zobj.net/source/apple/354/robot_1f916.png"),
            layout="bubble",
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your Project Idea",
                placeholder="Describe your project idea in detail...",
                lines=3,
                scale=4,
            )
            submit_btn = gr.Button("Generate Documentation", variant="primary", scale=1)

        gr.Examples(
            examples=examples,
            inputs=msg,
            label="Example Project Ideas",
        )

        # Handle submission
        def respond(message, chat_history):
            """Handle user message and stream response."""
            chat_history = chat_history or []
            chat_history.append({"role": "user", "content": message})

            # Stream the response
            response_content = ""
            for chunk in process_project_idea(message, chat_history):
                response_content = chunk
                yield chat_history + [{"role": "assistant", "content": response_content}], ""

        # Connect events
        submit_btn.click(
            respond,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg],
        )

        msg.submit(
            respond,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg],
        )

        # Clear button
        clear_btn = gr.Button("Clear Chat")
        clear_btn.click(lambda: ([], ""), outputs=[chatbot, msg])

        gr.Markdown(
            """
            ---
            **Tips:**
            - Be specific about your project's goals and target users
            - Mention any specific technologies you want to use
            - Include constraints like timeline or budget if relevant
            """
        )

    return demo


def main():
    """Main entry point."""
    logger.info("Starting Project Architect")

    # Check for settings (will raise if not configured)
    try:
        settings = get_settings()
        warnings = settings.validate()
        for warning in warnings:
            logger.warning(warning)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\nConfiguration Error: {e}")
        print("\nPlease create a .env file with the required settings.")
        print("See .env.example for the required format.\n")
        return

    # Create and launch the interface
    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
