# agent_with_ofs.py
from ofs import (
    list_projects_json,
    list_bidders_json,
    get_paths_json,
    find_bidder_in_project,
)
import os
from smolagents import CodeAgent, OpenAIServerModel, tool
from credgoo import get_api_key

# ------------------------------------------------------------------
# 1. Load credentials (unchanged)
# ------------------------------------------------------------------
BASE_URL = "https://aqueduct.ai.datalab.tuwien.ac.at/v1"
API_KEY = get_api_key('tu')
MODEL = 'deepseek-r1'

model = OpenAIServerModel(
    model_id=MODEL,
    api_base=BASE_URL,
    api_key=API_KEY,
)

# ------------------------------------------------------------------
# 2. Import OFS helpers and wrap each one as a tool
# ------------------------------------------------------------------


@tool
def ofs_list_projects_json() -> dict:
    """Return structured JSON with projects and count."""
    return list_projects_json()


@tool
def ofs_list_bidders_json(project: str) -> dict:
    """Return structured JSON with bidders and files for the given project.

    Args:
        project: The name of the OFS project to get bidders data for
    """
    return list_bidders_json(project)


@tool
def ofs_get_paths_json(name: str) -> dict:
    """Return structured JSON with all paths for the given name.

    Args:
        name: The name (project or bidder) to get path information for
    """
    return get_paths_json(name)


@tool
def ofs_find_bidder_in_project(project: str, bidder: str) -> dict:
    """Return info about a specific bidder inside a project.

    Args:
        project: The name of the OFS project
        bidder: The name of the bidder to find within the project
    """
    return find_bidder_in_project(project, bidder)


# ------------------------------------------------------------------
# 3. Build the agent with both WebSearchTool and all OFS tools
# ------------------------------------------------------------------
agent = CodeAgent(
    tools=[
        ofs_list_projects_json,
        ofs_list_bidders_json,
        ofs_get_paths_json,
        ofs_find_bidder_in_project,
    ],
    model=model,
    stream_outputs=True,
)

# ------------------------------------------------------------------
# 4. Example prompt (switch to whatever you need)
# ------------------------------------------------------------------
agent.run(
    "gibt es projekte für gartengeräte und wenn ja, dann welche?"
)
