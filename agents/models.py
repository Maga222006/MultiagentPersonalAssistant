from langchain.chat_models import init_chat_model
from dotenv import load_dotenv
from openai import AsyncOpenAI
import os

load_dotenv()

groq_client = AsyncOpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.getenv("GROQ_API_KEY"),
)

llm_supervisor = init_chat_model(
    model="groq:openai/gpt-oss-120b",
    max_tokens=1000
)

llm_peripheral = init_chat_model(
   model="groq:gemma2-9b-it"
)

llm_sub_agents = init_chat_model(
    model="groq:qwen/qwen3-32b"
)

llm_image = init_chat_model(
    model="groq:meta-llama/llama-4-scout-17b-16e-instruct"
)