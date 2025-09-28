from langgraph.prebuilt.chat_agent_executor import AgentState

class CoderState(AgentState):
    project_name: str
    private: bool = False
