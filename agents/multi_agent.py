from database_interaction.config import create_or_update_config, load_config_to_env, init_config_db
from database_interaction.user import get_user_by_id, create_or_update_user, init_user_db
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.messages.utils import count_tokens_approximately
from langchain_core.messages import SystemMessage, AIMessage
from sqlalchemy.ext.asyncio import create_async_engine
from langgraph.prebuilt import create_react_agent
from langmem.short_term import SummarizationNode
from agents.states import State
import os

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
            from agents.models import llm_supervisor, llm_peripheral
            from agents.prompts import prompt
            from agents.tools import tools

            summarization_node = SummarizationNode(
                token_counter=count_tokens_approximately,
                model=llm_peripheral,
                max_tokens=4000,
                max_summary_tokens=1000,
                output_messages_key="llm_input_messages",
            )

            agent = create_react_agent(
                model=llm_supervisor,
                tools=tools,
                prompt=prompt(tools),
                state_schema=State,
                version='v1',
                pre_model_hook=summarization_node,
            )
            return agent

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
        from agents.prompts import system_message
        try:
            user_info = await get_user_by_id(user_id=self.state['user_id'])
            if user_info.get('location'):
                os.environ['LOCATION'] = user_info['location']
            if user_info.get('latitude'):
                os.environ['LATITUDE'] = str(user_info['latitude'])
            if user_info.get('longitude'):
                os.environ['LONGITUDE'] = str(user_info['longitude'])


            await self.message_history.aadd_message(self.state['message'])
            messages = await self.message_history.aget_messages()

            self.state['messages'] = messages[-8:-1] + [SystemMessage(system_message(user_info)), messages[-1]]
            multi_agent_system = self.compile_multi_agent_system()

            result = await multi_agent_system.ainvoke(
                {"messages": self.state["messages"]},
                generation_config=dict(response_modalities=["TEXT"])
            )
            await self.message_history.aadd_message(result['messages'][-1])
            return {"messages": result.get("messages", [])}

        except Exception as e:
            print(f"Multi-agent node error: {e}")
            from langchain_core.messages import HumanMessage
            return {"messages": [AIMessage(content=f"I encountered an error: {str(e)}. Please try again.")]}
