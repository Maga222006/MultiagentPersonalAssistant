from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import mimetypes
import asyncio
import base64

load_dotenv()

async def preprocess_file(file_name: str):
    mime_type = mimetypes.guess_type(file_name)[0]
    if "image" in mime_type:
        return await preprocess_image(file_name)
    elif "video" in mime_type:
        pass
    elif "audio" in mime_type:
        return await preprocess_audio(file_name)
    else:
        return await asyncio.to_thread(preprocess_text, file_name, mime_type)


async def preprocess_audio(file_name):
    from agent.models import groq_client
    transcription = await groq_client.audio.transcriptions.create(
        model="whisper-large-v3-turbo",
        file=open(file_name, "rb")
    )
    return transcription.text


async def preprocess_image(file_name: str):
    from agent.models import llm_image
    with open(file_name, "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode("utf-8")
    response = await llm_image.ainvoke([HumanMessage(
                content=[
                    {"type": "text", "text": "Please analyze this image and give detailed description."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    },
                ]
            )
        ]
    )
    return response.content


def preprocess_text(file_name, mime_type: str) -> str:
    if "pdf" in mime_type:
        reader = PdfReader(file_name)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    elif "document" in mime_type:
        doc = Document(file_name)
        return "\n".join(p.text for p in doc.paragraphs)
    try:
        with open(file_name, "r", encoding="utf-8") as file:
            return file.read()
    except Exception:
        return "[Unsupported format]"