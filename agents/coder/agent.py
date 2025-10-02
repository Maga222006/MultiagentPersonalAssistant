from langchain_core.messages import HumanMessage, SystemMessage
from agents.coder.prompts import prompt, system_message
from langgraph.prebuilt import create_react_agent
from agents.utils.coder import initialize_project
from agents.coder.states import CoderState
from agents.models import llm_sub_agents
from langchain.tools import tool
from agents.coder import tools
from dotenv import load_dotenv
import shutil
import os

load_dotenv()

agent = create_react_agent(
    llm_sub_agents,
    tools=tools.tools,
    prompt=prompt,
    state_schema=CoderState,
)

@tool
def coder_agent(project_name: str, task_description: str, repo_owner: str = None, branch: str = "main", private: bool = False):
    """
    Coder Agent, used as a tool for any coding tasks, it creates a new project or downloads repo from GitHub to further adjust it, tests it and saves to GitHub.

    Args:
        project_name (str): The name of the GitHub repository and directory for the project.
        repo_owner (str): The owner of the GitHub repository, used only if we want to download the existing repo, not create a new project from scratch. Defaults to None (user's GitHub account)
        branch (str): The branch of the GitHub repository. Defaults to "main".
        task_description (str): A detailed description of the project for the coder to create or adjust.
        private (bool, optional): Whether the coder should be private or public. Defaults to False.
    """
    initialize_project(project_name=project_name, repo_owner=repo_owner, branch=branch, private=private)
    path = f"agents/coder/projects/{project_name}"
    messages = agent.invoke({'messages': [SystemMessage(system_message(project_name, private)), HumanMessage(content=task_description)], 'project_name': project_name, 'private': private})
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    return messages['messages'][-1].content