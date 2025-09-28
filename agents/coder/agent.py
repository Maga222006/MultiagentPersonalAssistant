from langchain_core.messages import HumanMessage, SystemMessage
from agents.coder.prompts import prompt, system_message
from langgraph.prebuilt import create_react_agent
from agents.coder.states import CoderState
from agents.models import llm_sub_agents
from agents.coder.tools import tools
from langchain.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()

agent = create_react_agent(
    llm_sub_agents,
    tools=tools,
    prompt=prompt,
    state_schema=CoderState,
)

@tool
def coder_agent(project_name: str, task_description: str, private: bool=False):
    """
    Coder Agent, used as a tool for any coding tasks, it creates project, tests it and saves to GitHub.

    Args:
        project_name (str): The name of the GitHub repository and directory for the project.
        task_description (str): A detailed description of the project for the coder to create.
        private (bool, optional): Whether the coder should be private or public. Defaults to False.
    """
    path = f"agents/coder/projects/{project_name}"
    messages = agent.invoke({'messages': [SystemMessage(system_message(project_name, private)), HumanMessage(content=task_description)], 'project_name': project_name, 'private': private})
    if os.path.isdir(path):
        os.rmdir(path)
    return messages['messages'][-1].content