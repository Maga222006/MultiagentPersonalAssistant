from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

load_dotenv()

llm_supervisor = init_chat_model(
    "groq:openai/gpt-oss-20b",
    max_tokens=1000
)

llm_peripheral = init_chat_model(
    "groq:gemma2-9b-it",
    max_tokens=4000
)

llm_sub_agents = init_chat_model(
    "groq:qwen/qwen3-32b",
    max_tokens=3000
)