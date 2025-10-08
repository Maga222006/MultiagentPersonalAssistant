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
   model="llama-3.1-8b-instant"
)

llm_sub_agents = init_chat_model(
    model="groq:moonshotai/kimi-k2-instruct-0905",
    max_tokens=4000
)

llm_image = init_chat_model(
    model="groq:meta-llama/llama-4-scout-17b-16e-instruct"
)