from transformers import AutoTokenizer, AutoModelForCausalLM
from speechbrain.inference.classifiers import EncoderClassifier
import speech_recognition as sr
from pydub import AudioSegment
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from docx import Document
from PIL import Image
import torchaudio
import mimetypes
import asyncio
import torch
import io
import os

load_dotenv()
MID = "apple/FastVLM-1.5B"
IMAGE_TOKEN_INDEX = -200

tok = AutoTokenizer.from_pretrained(MID, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    MID,
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto",
    trust_remote_code=True,
)
language_id = EncoderClassifier.from_hparams(source="speechbrain/lang-id-voxlingua107-ecapa", savedir="tmp")


async def preprocess_file(file_name: str):
    mime_type = mimetypes.guess_type(file_name)[0]
    if "image" in mime_type:
        return await asyncio.to_thread(preprocess_image, file_name)
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


def preprocess_image(file_name: str) -> str:
    """Send an image + instruction to FastVLM and return the model's answer."""

    # Build chat with placeholder <image>
    messages = [{"role": "user", "content": f"<image>\nDescribe this image in detail."}]
    rendered = tok.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    pre, post = rendered.split("<image>", 1)

    # Tokenize text around the image placeholder
    pre_ids = tok(pre, return_tensors="pt", add_special_tokens=False).input_ids
    post_ids = tok(post, return_tensors="pt", add_special_tokens=False).input_ids

    # Insert the image token id (-200)
    img_tok = torch.tensor([[IMAGE_TOKEN_INDEX]], dtype=pre_ids.dtype)
    input_ids = torch.cat([pre_ids, img_tok, post_ids], dim=1).to(model.device)
    attention_mask = torch.ones_like(input_ids, device=model.device)

    # Preprocess the image
    img = Image.open(file_name).convert("RGB")
    px = model.get_vision_tower().image_processor(images=img, return_tensors="pt")["pixel_values"]
    px = px.to(model.device, dtype=model.dtype)

    # Generate response
    with torch.no_grad():
        out = model.generate(
            inputs=input_ids,
            attention_mask=attention_mask,
            images=px,
            max_new_tokens=128,
        )

    return tok.decode(out[0], skip_special_tokens=True)


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