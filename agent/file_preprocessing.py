from speechbrain.inference.classifiers import EncoderClassifier
from langchain_core.messages import HumanMessage
from agent.models import llm_image
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
import torchaudio
import mimetypes
import asyncio
import base64
import os

load_dotenv()
language_id = EncoderClassifier.from_hparams(source="speechbrain/lang-id-voxlingua107-ecapa", savedir="tmp")


async def preprocess_file(file_name: str):
    mime_type = mimetypes.guess_type(file_name)[0]
    if "image" in mime_type:
        return await preprocess_image(file_name)
    elif "video" in mime_type:
        prompt = "Give a detailed description of the video."
    elif "audio" in mime_type:
        return await asyncio.to_thread(preprocess_audio, file_name)
    else:
        return await asyncio.to_thread(preprocess_text, file_name, mime_type)


def preprocess_audio(file_name: str):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"File not found: {file_name}")

    wav_file = os.path.splitext(file_name)[0] + ".wav"
    audio = AudioSegment.from_file(file_name)
    audio.export(wav_file, format="wav")
    signal = language_id.load_audio(wav_file)
    out = language_id.classify_batch(signal)[0].tolist()[0]
    lang_mapping = {
        20: "en",
        106: "zh",
        35: "hi",
        22: "es",
        3: "ar",
        28: "fr",
        77: "ru",
        75: "pt",
        9: "bn",
        45: "ja",
        18: "de",
        51: "ko",
        102: "vi",
        99: "uk"
    }
    scores = [out[index] for index in lang_mapping.keys()]
    language = list(lang_mapping.values())[scores.index(max(scores))]
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_file) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            text = "[Unintelligible audio]"
        except sr.RequestError as e:
            text = f"[API error: {e}]"
    os.remove(wav_file)
    return text


async def preprocess_image(file_name: str):
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