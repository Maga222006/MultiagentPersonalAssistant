from langgraph.prebuilt.chat_agent_executor import AgentState
from langchain_core.messages import AnyMessage

class State(AgentState):
    message: AnyMessage
    user_id: str
    first_name: str
    last_name: str
    assistant_name: str
    latitude: str
    longitude: str
    location: str
    openweathermap_api_key: str
    github_token: str
    tavily_api_key: str
    groq_api_key: str
    tuya_access_id: str
    tuya_access_key: str
    tuya_username: str
    tuya_password: str
    tuya_country: str
    clear_history: bool