from agent.prompts import deep_research_instructions, deep_research_system_message
from langchain_core.messages import HumanMessage, SystemMessage
from agent.models import llm_agents, llm_peripheral
from langgraph.prebuilt import create_react_agent
from agent.tools import deep_research_tools
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from agent.states import PlanResearch

agent = create_react_agent(
    llm_agents,
    tools=deep_research_tools,
    prompt=deep_research_instructions
)

def planning_node(state: dict):
    planer = llm_peripheral.with_structured_output(PlanResearch)
    plan = planer.invoke(state['messages'][-1].content)
    state.update(plan)
    return state

def research_agent(state: dict):
    system_message = SystemMessage(deep_research_system_message(state))
    state.update(agent.invoke({
        'messages': [
            system_message,
            HumanMessage(state['messages'][-1].content),
        ]
    }))
    return state

graph = StateGraph(dict)
graph.add_node("planning_node", planning_node)
graph.add_node("research_agent", research_agent)
graph.add_edge(START, "planning_node")
graph.add_edge("planning_node", "research_agent")
graph.add_edge("research_agent", END)

deep_research_agent = graph.compile(name="deep_research_agent")
