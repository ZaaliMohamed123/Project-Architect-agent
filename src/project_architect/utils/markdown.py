"""
Markdown formatting utilities for Gradio output.

Provides helper functions to format agent progress and results as markdown.
"""

from typing import Optional


class MarkdownFormatter:
    """Helper class for formatting markdown output for the Gradio chatbot."""

    @staticmethod
    def header(text: str, level: int = 1) -> str:
        """Create a markdown header."""
        return f"{'#' * level} {text}\n\n"

    @staticmethod
    def bold(text: str) -> str:
        """Make text bold."""
        return f"**{text}**"

    @staticmethod
    def italic(text: str) -> str:
        """Make text italic."""
        return f"*{text}*"

    @staticmethod
    def code(text: str, language: str = "") -> str:
        """Create a code block."""
        return f"```{language}\n{text}\n```\n\n"

    @staticmethod
    def inline_code(text: str) -> str:
        """Create inline code."""
        return f"`{text}`"

    @staticmethod
    def bullet_list(items: list[str]) -> str:
        """Create a bullet list."""
        return "\n".join(f"- {item}" for item in items) + "\n\n"

    @staticmethod
    def numbered_list(items: list[str]) -> str:
        """Create a numbered list."""
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items)) + "\n\n"

    @staticmethod
    def link(text: str, url: str) -> str:
        """Create a markdown link."""
        return f"[{text}]({url})"

    @staticmethod
    def divider() -> str:
        """Create a horizontal divider."""
        return "\n---\n\n"

    @staticmethod
    def quote(text: str) -> str:
        """Create a blockquote."""
        lines = text.split("\n")
        return "\n".join(f"> {line}" for line in lines) + "\n\n"

    @staticmethod
    def status_badge(status: str, emoji: str = "") -> str:
        """Create a status badge."""
        status_emojis = {
            "pending": "⏳",
            "in_progress": "🔄",
            "researching": "🔍",
            "completed": "✅",
            "failed": "❌",
            "success": "✅",
            "error": "❌",
        }
        if not emoji:
            emoji = status_emojis.get(status.lower(), "📌")
        return f"{emoji} **{status}**"

    @classmethod
    def project_analysis_complete(
        cls,
        project_title: str,
        objectives: list[str],
        deliverables: list[str],
        domains: list[str],
    ) -> str:
        """Format the project analysis completion message."""
        output = cls.header("Project Analysis Complete", 2)
        output += f"{cls.bold('Project Title:')} {project_title}\n\n"

        output += f"{cls.bold('Objectives:')}\n"
        output += cls.bullet_list(objectives)

        output += f"{cls.bold('Deliverables:')}\n"
        output += cls.bullet_list(deliverables)

        output += f"{cls.bold('Technical Domains:')} {', '.join(domains)}\n\n"

        return output

    @classmethod
    def steps_outline(cls, steps: list[dict]) -> str:
        """Format the steps outline."""
        output = cls.header("Project Steps Outline", 2)

        for i, step in enumerate(steps, 1):
            output += f"{cls.bold(f'Step {i}:')} {step['name']}\n"
            output += f"   {step['description']}\n\n"

        return output

    @classmethod
    def step_research_start(cls, step_number: int, step_name: str, total_steps: int) -> str:
        """Format the start of step research."""
        output = cls.divider()
        output += cls.header(f"Step {step_number} of {total_steps}: {step_name}", 2)
        output += f"{cls.status_badge('researching')} Researching...\n\n"
        return output

    @classmethod
    def research_progress(
        cls,
        search_query: str,
        results_count: int,
        urls_reading: list[str],
    ) -> str:
        """Format research progress update."""
        output = f"{cls.bold('Research Progress:')}\n"
        output += f"- Searched for: {cls.inline_code(search_query)}\n"
        output += f"- Found {results_count} results\n"

        if urls_reading:
            output += f"- Reading:\n"
            for url in urls_reading:
                output += f"  - {url}\n"

        output += "\n"
        return output

    @classmethod
    def step_research_complete(
        cls,
        step_number: int,
        step_name: str,
        key_technologies: list[str],
        notion_url: Optional[str] = None,
    ) -> str:
        """Format step research completion."""
        output = f"{cls.status_badge('completed')} Step {step_number} research complete\n\n"

        output += f"{cls.bold('Key Technologies Found:')}\n"
        output += cls.bullet_list(key_technologies[:5])

        if notion_url:
            output += f"{cls.bold('Notion Page:')} {cls.link(f'Step {step_number}: {step_name}', notion_url)}\n\n"

        return output

    @classmethod
    def final_summary(
        cls,
        project_title: str,
        overview_url: str,
        step_pages: list[dict],
        total_time: Optional[float] = None,
    ) -> str:
        """Format the final completion summary."""
        output = cls.divider()
        output += cls.header("Documentation Complete!", 2)
        output += f"{cls.status_badge('success')} All steps have been researched and documented.\n\n"

        output += f"{cls.bold('Project:')} {project_title}\n\n"
        output += f"{cls.bold('Overview Page:')} {cls.link('View Project Overview', overview_url)}\n\n"

        output += f"{cls.bold('Step Documentation:')}\n"
        for page in step_pages:
            output += f"- {cls.link(page['title'], page['url'])}\n"

        output += "\n"

        if total_time:
            output += f"{cls.italic(f'Total time: {total_time:.1f} seconds')}\n"

        return output

    @classmethod
    def error_message(cls, error: str, context: str = "") -> str:
        """Format an error message."""
        output = f"{cls.status_badge('error')} An error occurred"
        if context:
            output += f" during {context}"
        output += f"\n\n{cls.quote(error)}"
        return output

    @classmethod
    def notion_page_created(cls, title: str, url: str) -> str:
        """Format Notion page creation notification."""
        return f"📝 Created Notion page: {cls.link(title, url)}\n\n"
