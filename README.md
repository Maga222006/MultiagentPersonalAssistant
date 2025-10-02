---
license: mit
title: 🧠 Multi-Agent AI Assistant
sdk: docker
emoji: 💻
colorFrom: indigo
colorTo: indigo
pinned: true
---

# 🧠 Multi-Agent AI Assistant

This project is a **voice- and text-based AI assistant** powered by **FastAPI**, **LangGraph**, and **LangChain**. It supports:
- 🤖 Multi-agent system
- 🗣️ Voice input via speech-to-text
- 🌄 Image processing
- 📂 File processing
- 🌐 Web search, GitHub actions, weather, time, and geolocation tools
- 🧠 Memory-based conversation history per user
- 📍 Location-aware capabilities (e.g., timezone, weather)

---

## 🚀 Features

- **FastAPI backend** with `/text`, `/image`, `/voice` and `/file` endpoints
- **LangGraph agents** with memory, tools, and typed state
- **User database** with persistent settings and config
- **Agents**:
  - Supervisor agent
  - Coding agent
- **Supervisor tools**:
  - Web search
  - Current time
  - Weather
  - Yahoo finance news
  - Change device states (Smart Home)
- **Coder tools**:
  - Github toolkit
  - Web search (For docs research)
  - Code Interpreter
---

## 🛠️ Setup Instructions

### 1. Environment

This project requires no manual environment configuration — all secrets are passed dynamically with each request and stored in the database.

Just run:

```bash
docker build -t multi-agent-assistant .
docker run -p 7860:7860 multi-agent-assistant
```

The server will launch automatically at http://localhost:7860, with all dependencies installed and configured inside the container.

---

## 📦 API Reference

### `/text` – Send Text Prompt

```http
POST /text
Form data:
- state (str): JSON-encoded state dict
```

### `/voice` – Send Audio Prompt

```http
POST /voice
Form data:
- state (str): JSON-encoded state dict
- file (binary): Audio file (WAV, MP3, etc.)
```

### `/image` – Send Image Prompt

```http
POST /image
Form data:
- state (str): JSON-encoded state dict
- file (binary): Image file (JPEG, PNG, etc.)
```

### `/file` – Send File Prompt

```http
POST /file
Form data:
- state (str): JSON-encoded state dict
- file (binary): Image file (PDF, TXT, etc.)
```
---

## 🧩 Agent State Structure

The system operates using a JSON-based shared state object passed between agents.  
It follows a `TypedDict` schema and may contain keys such as:

```json
{
    message: AnyMessage (message to the agent)
    user_id: str (unique user id) 
    first_name: str
    last_name: str
    assistant_name: str
    latitude: str
    longitude: str
    location: str (user-readable location)
    openweathermap_api_key: str
    github_token: str
    tavily_api_key: str
    groq_api_key: str,
    tuya_access_id: str
    tuya_access_key: str
    tuya_username: str
    tuya_password: str
    tuya_country: str
    clear_history: bool (True/False)
    messages: list (Filled automatically from the database) 

}
```

This dictionary acts as a single mutable state shared across all agent steps, allowing for data accumulation, tool responses, and message tracking.


---

## ⚙️ Tuya Setup

Take a look at the [official instructions](https://developer.tuya.com/en/docs/iot/device-control-best-practice?id=Ka72202tz4m67)

---

## 🧠 Built With

- [Groq](https://github.com/groq/groq-python)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [LangChain](https://github.com/langchain-ai/langchain)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Whisper](https://github.com/openai/whisper)
- [SQLAlchemy + Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Tuya Smart Home](https://github.com/tuya/tuya-iot-python-sdk?tab=readme-ov-file)

---

## 📝 License

MIT — Feel free to use, modify, and contribute!
