from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
load_dotenv()

llm_supervisor = init_chat_model(
    model="groq:openai/gpt-oss-120b",
    max_tokens=1000
)

llm_peripheral = init_chat_model(
   model="groq:gemma2-9b-it"
)

llm_agents = init_chat_model(
    model="groq:qwen/qwen3-32b"
)