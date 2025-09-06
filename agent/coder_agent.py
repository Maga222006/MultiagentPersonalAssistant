from agent.prompts import coder_instructions, coder_system_message
from langchain_core.messages import HumanMessage, SystemMessage
from agent.models import llm_agents, llm_peripheral
from langgraph.prebuilt import create_react_agent
from langgraph.constants import START, END
from agent.states import PlanCodingTask
from langgraph.graph import StateGraph
from agent.tools import coder_tools

agent = create_react_agent(
    llm_agents,
    tools=coder_tools,
    prompt=coder_instructions
)

def planning_node(state: dict):
    planer = llm_peripheral.with_structured_output(PlanCodingTask)
    plan = planer.invoke(state['messages'][-1].content)
    state.update(plan)
    return state

def code_agent(state: dict):
    system_message = SystemMessage(coder_system_message(state))
    state.update(agent.invoke({
        'messages': [
            system_message,
            HumanMessage(state['task_description']),
        ]
    }))
    return state

graph = StateGraph(dict)
graph.add_node("planning_node", planning_node)
graph.add_node("code_agent", code_agent)
graph.add_edge(START, "planning_node")
graph.add_edge("planning_node", "code_agent")
graph.add_edge("code_agent", END)

coder_agent = graph.compile(name="coder_agent")
