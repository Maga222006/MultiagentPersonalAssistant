from agent.prompts import smart_home_instructions, smart_home_system_message
from langchain_core.messages import HumanMessage, SystemMessage
from agent.models import llm_agents, llm_peripheral
from langgraph.prebuilt import create_react_agent
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from agent.tools import smart_home_tools, get_device_list

agent = create_react_agent(
    llm_agents,
    tools=smart_home_tools,
    prompt=smart_home_instructions
)

def home_control_agent(state: dict):
    system_message = SystemMessage(smart_home_system_message(get_device_list.invoke({})))
    state.update(agent.invoke({
        'messages': [
            system_message,
            HumanMessage(state['messages'][-1].content),
        ]
    }))
    return state

graph = StateGraph(dict)
graph.add_node("home_control_agent", home_control_agent)
graph.add_edge(START, "home_control_agent")
graph.add_edge("home_control_agent", END)

smart_home_agent = graph.compile(name="smart_home_agent")
