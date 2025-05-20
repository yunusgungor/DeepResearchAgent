from src.config import config
from src.logger import logger
from src.registry import REGISTED_MODELS
from src.tools.planning import PlanningTool
from src.tools.deep_researcher import DeepResearcherTool
from src.tools.python_interpreter import PythonInterpreterTool
from src.tools.deep_analyzer import DeepAnalyzerTool
from src.tools.auto_browser import AutoBrowserUseTool
from src.agent.browser_use_agent.browser_use_agent import BrowserUseAgent
from src.agent.deep_analyzer_agent.deep_analyzer_agent import DeepAnalyzerAgent
from src.agent.deep_researcher_agent.deep_researcher_agent import DeepResearcherAgent
from src.agent.planning_agent.planning_agent import PlanningAgent

AUTHORIZED_IMPORTS = [
    "pandas",
    "requests",
    "numpy"
]

def create_agent():
    # Initialize the deep analyzer agent
    deep_analyzer_agent_config = config.agent.deep_analyzer_agent_config
    deep_analyzer_agent = DeepAnalyzerAgent(
        config=deep_analyzer_agent_config,
        model=REGISTED_MODELS[deep_analyzer_agent_config.model_id],
        tools=[
            DeepAnalyzerTool(),
            PythonInterpreterTool(
                authorized_imports=AUTHORIZED_IMPORTS
            )
        ],
        max_steps=deep_analyzer_agent_config.max_steps,
        name=deep_analyzer_agent_config.name,
        description=deep_analyzer_agent_config.description,
        provide_run_summary=True,
    )

    deep_researcher_agent_config = config.agent.deep_researcher_agent_config
    deep_researcher_agent = DeepResearcherAgent(
        config=deep_researcher_agent_config,
        model=REGISTED_MODELS[deep_researcher_agent_config.model_id],
        tools=[
            DeepResearcherTool(
                REGISTED_MODELS[deep_researcher_agent_config.model_id]
            ),
            PythonInterpreterTool(
                authorized_imports=AUTHORIZED_IMPORTS
            )
        ],
        max_steps=deep_researcher_agent_config.max_steps,
        name=deep_researcher_agent_config.name,
        description=deep_researcher_agent_config.description,
        provide_run_summary=True,
    )

    browser_use_agent_config = config.agent.browser_use_agent_config
    browser_use_agent = BrowserUseAgent(
        config=browser_use_agent_config,
        model=REGISTED_MODELS[browser_use_agent_config.model_id],
        tools=[
            AutoBrowserUseTool(),
            PythonInterpreterTool(
                authorized_imports=AUTHORIZED_IMPORTS
            ),
        ],
        max_steps=browser_use_agent_config.max_steps,
        name=browser_use_agent_config.name,
        description=browser_use_agent_config.description,
        provide_run_summary=True,
    )

    # Initialize planning agent
    planning_agent_config = config.agent.planning_agent_config
    agent = PlanningAgent(
        config=planning_agent_config,
        model=REGISTED_MODELS[planning_agent_config.model_id],
        tools = [
            PlanningTool(),
        ],
        max_steps=planning_agent_config.max_steps,
        managed_agents=[
            browser_use_agent,
            deep_analyzer_agent,
            deep_researcher_agent,
        ],
        description=planning_agent_config.description,
        name=planning_agent_config.name,
        provide_run_summary=True,
    )

    logger.info("Agent initialized.")

    return agent