"""
Prompt templates for the Project Architect agent.

Contains all system prompts and instruction templates used by the LLM.
"""

UNDERSTAND_PROJECT_PROMPT = """You are an expert project analyst. Your task is to analyze a project idea and extract structured information.

Given the following project idea, extract:
1. A clear, concise project title (max 10 words)
2. 2-4 main objectives (what the project aims to achieve)
3. 2-4 key deliverables (tangible outputs)
4. 2-5 technical domains involved (e.g., AI/ML, Web Development, Cloud, IoT, Data Engineering, Mobile, DevOps, Security)

PROJECT IDEA:
{project_idea}

Respond in the following JSON format:
{{
    "project_title": "string",
    "objectives": ["objective1", "objective2", ...],
    "deliverables": ["deliverable1", "deliverable2", ...],
    "domains": ["domain1", "domain2", ...]
}}

Important:
- Be specific and actionable
- Focus on what makes this project unique
- Identify the most relevant technical domains
- Keep responses concise but comprehensive"""


OUTLINE_STEPS_PROMPT = """You are an expert project planner. Your task is to break down a project into actionable implementation steps.

PROJECT INFORMATION:
- Title: {project_title}
- Objectives: {objectives}
- Deliverables: {deliverables}
- Technical Domains: {domains}

Create 4-7 high-level steps that cover the complete project lifecycle. Each step should:
1. Be actionable and achievable
2. Build upon previous steps
3. Lead toward project completion
4. Be specific enough to research

Respond in the following JSON format:
{{
    "steps": [
        {{"name": "Step Name", "description": "Brief description of what this step involves"}},
        ...
    ]
}}

Common step patterns to consider:
- Requirements Definition / Planning
- Architecture / Design
- Data Collection / Preparation
- Core Implementation / Development
- Integration / Testing
- Deployment / Infrastructure
- Monitoring / Optimization

Adapt these patterns to the specific project needs."""


REFLECT_ON_STEP_PROMPT = """You are a research planning expert. Your task is to reflect on a project step and identify what information is needed.

PROJECT CONTEXT:
- Title: {project_title}
- Domains: {domains}

CURRENT STEP:
- Name: {step_name}
- Description: {step_description}

Analyze this step and determine:
1. What specific topics should be researched?
2. What technologies or tools are likely relevant?
3. What best practices should be found?
4. What are the key questions to answer?

Respond in the following JSON format:
{{
    "research_focus": "A concise description of what to research",
    "search_queries": ["query1", "query2"],
    "key_questions": ["question1", "question2", "question3"]
}}

Generate 2-3 focused search queries that will yield relevant, recent information about this step."""


SYNTHESIZE_RESEARCH_PROMPT = """You are a technical documentation expert. Your task is to synthesize research findings into structured documentation for a project step.

PROJECT CONTEXT:
- Title: {project_title}
- Domains: {domains}

STEP INFORMATION:
- Step Number: {step_number}
- Name: {step_name}
- Description: {step_description}

RESEARCH FINDINGS:
{research_content}

Based on the research findings, create comprehensive documentation for this step. Include:

1. **Step Objective**: A clear statement of what this step aims to achieve (2-3 sentences)

2. **Key Technologies**: List 3-5 specific technologies, frameworks, or tools relevant to this step

3. **Recommended Methods & Tools**: List 3-5 actionable recommendations for implementing this step

4. **Detailed Guidance**: Write 3-5 paragraphs explaining:
   - How to approach this step
   - Best practices to follow
   - Common pitfalls to avoid
   - Integration considerations with other steps

Respond in the following JSON format:
{{
    "objective": "string",
    "key_technologies": ["tech1", "tech2", ...],
    "methods_and_tools": ["method1", "method2", ...],
    "detailed_content": "Multi-paragraph detailed guidance..."
}}

Important:
- Focus on practical, actionable advice
- Reference specific tools and technologies by name
- Include 2026-relevant best practices
- Write in a professional, technical tone"""


# Dictionary of all prompts for easy access
PROMPTS = {
    "understand_project": UNDERSTAND_PROJECT_PROMPT,
    "outline_steps": OUTLINE_STEPS_PROMPT,
    "reflect_on_step": REFLECT_ON_STEP_PROMPT,
    "synthesize_research": SYNTHESIZE_RESEARCH_PROMPT,
}
