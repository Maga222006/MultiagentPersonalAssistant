from database_interaction.config import create_or_update_config, load_config_to_env, init_config_db
from database_interaction.user import get_user_by_id, create_or_update_user, init_user_db
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages import SystemMessage, AnyMessage, AIMessage
from langchain_core.messages.utils import count_tokens_approximately
from sqlalchemy.ext.asyncio import create_async_engine
from langgraph_supervisor import create_supervisor
from langmem.short_term import SummarizationNode
from typing_extensions import TypedDict
import os

class State(TypedDict):
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
    messages: list

class Assistant:
    def __init__(self, state: State):
        self.state = state
        self.engine = create_async_engine("sqlite+aiosqlite:///./database_files/main.db", echo=False)
        self.message_history = SQLChatMessageHistory(
            session_id=state['user_id'],
            connection=self.engine,
            async_mode=True
        )

    async def authorization(self):
        """Handle user authorization and configuration setup"""
        try:
            await init_user_db()
            await init_config_db()
            await create_or_update_user(
                user_id=self.state['user_id'],
                first_name=self.state.get('first_name'),
                last_name=self.state.get('last_name'),
                latitude=float(self.state['latitude']) if self.state.get('latitude') else None,
                longitude=float(self.state['longitude']) if self.state.get('longitude') else None,
            )

            config_data = {}
            config_fields = [
                'assistant_name', 'openweathermap_api_key', 'github_token',
                'tavily_api_key', 'groq_api_key', 'tuya_access_id', 'tuya_access_key',
                'tuya_username', 'tuya_password', 'tuya_country'
            ]

            for field in config_fields:
                if self.state.get(field):
                    config_data[field] = self.state[field]

            if config_data:
                await create_or_update_config(user_id=self.state['user_id'], **config_data)
            await load_config_to_env(user_id=self.state['user_id'])

            if 'clear_history' in self.state and self.state['clear_history']:
                await self.message_history.aclear()

        except Exception as e:
            print(f"Authorization/setup error: {e}")

    def compile_multi_agent_system(self):
        """Create and return the multi-agent system"""
        try:
            from agent.smart_home_agent import smart_home_agent
            from agent.deep_research_agent import deep_research_agent
            from agent.coder_agent import coder_agent
            from agent.prompts import supervisor_instructions
            from agent.models import llm_supervisor, llm_peripheral
            from agent.tools import supervisor_tools

            summarization_node = SummarizationNode(
                token_counter=count_tokens_approximately,
                model=llm_peripheral,
                max_tokens=4000,
                max_summary_tokens=1000,
                output_messages_key="llm_input_messages",
            )

            agents = [coder_agent, deep_research_agent, smart_home_agent]

            supervisor = create_supervisor(
                model=llm_supervisor,
                tools=supervisor_tools,
                agents=agents,
                prompt=supervisor_instructions(supervisor_tools, agents),
                add_handoff_back_messages=False,
                add_handoff_messages=False,
                output_mode="full_history",
                pre_model_hook=summarization_node
            )

            return supervisor.compile()

        except Exception as e:
            print(f"Error creating multi-agent system: {e}")
            # Return a simple fallback system with proper async interface
            from langchain_core.messages import HumanMessage
            from langgraph.graph import StateGraph
            from typing import Dict, Any

            def fallback_node(state: Dict[str, Any]):
                return {"messages": state.get("messages", []) + [
                    HumanMessage(content=f"System error: {str(e)}. Please check configuration and try again.")]}

            fallback_graph = StateGraph(dict)
            fallback_graph.add_node("fallback", fallback_node)
            fallback_graph.set_entry_point("fallback")
            fallback_graph.set_finish_point("fallback")

            return fallback_graph.compile()

    async def run(self):
        """Process messages through the multi-agent system"""
        try:
            user_info = await get_user_by_id(user_id=self.state['user_id'])
            if user_info.get('location'):
                os.environ['LOCATION'] = user_info['location']
            if user_info.get('latitude'):
                os.environ['LATITUDE'] = str(user_info['latitude'])
            if user_info.get('longitude'):
                os.environ['LONGITUDE'] = str(user_info['longitude'])

            system_msg = SystemMessage(
                content=f"""
                            You are an intelligent assistant named {os.getenv('ASSISTANT_NAME', 'Assistant')}, helpful personal assistant built using a multi-agent system architecture. Your tools include web search, weather and time lookups, code execution, and GitHub integration. You work inside a Telegram interface and respond concisely, clearly, and informatively.

                            The user you are assisting is:
                            - **Name**: {user_info.get('first_name', 'Unknown') or 'Unknown'} {user_info.get('last_name', '') or ''}
                            - **User ID**: {self.state['user_id']}
                            - **Location**: {user_info.get('location', 'Unknown') or 'Unknown'}
                            - **Coordinates**: ({user_info.get('latitude', 'N/A') or 'N/A'}, {user_info.get('longitude', 'N/A') or 'N/A'})

                            You may use their location when answering weather or time-related queries. If the location is unknown, you may ask the user to share it.

                            Stay helpful, respectful, and relevant to the user's query.
                            """.strip()
            )

            await self.message_history.aadd_message(self.state['message'])
            messages = await self.message_history.aget_messages()

            self.state['messages'] = messages[-8:-1] + [system_msg, messages[-1]]
            multi_agent_system = self.compile_multi_agent_system()

            result = await multi_agent_system.ainvoke({"messages": self.state["messages"]},
                                                      generation_config=dict(response_modalities=["TEXT"]))
            await self.message_history.aadd_message(result['messages'][-1])
            return {"messages": result.get("messages", [])}

        except Exception as e:
            print(f"Multi-agent node error: {e}")
            from langchain_core.messages import HumanMessage
            return {"messages": [AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")]}
