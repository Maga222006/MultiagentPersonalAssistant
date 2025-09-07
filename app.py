from fastapi import FastAPI, UploadFile, File, HTTPException
from agent.file_preprocessing import preprocess_file
from langchain_core.messages import HumanMessage
from agent.multi_agent import Assistant
from typing import Any, Dict
from fastapi import Form
from pathlib import Path
import json
import os

MEDIA_DIR = Path("mediafiles")
(MEDIA_DIR.mkdir(exist_ok=True))

app = FastAPI()

@app.post("/voice")
async def file_mode(
        state: str = Form(...),
        file: UploadFile = File(...)
) -> Dict[str, Any]:
    # Parse JSON string form field into dict
    try:
        state_data = json.loads(state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'state' form field")

    # Save the uploaded file asynchronously
    dest = MEDIA_DIR / file.filename
    data = await file.read()
    dest.write_bytes(data)

    # Initialize agent
    assistant = Assistant(state=state_data)
    await assistant.authorization()

    # Preprocess file
    transcription = await preprocess_file(str(dest))
    state_data["message"] = HumanMessage(
        content=transcription
    )
    # Call the agents
    assistant.state = state_data
    response = await assistant.run()
    os.remove(str(dest))
    return response

@app.post("/image")
async def file_mode(
        state: str = Form(...),
        file: UploadFile = File(...)
) -> Dict[str, Any]:
    # Parse JSON string form field into dict
    try:
        state_data = json.loads(state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'state' form field")

    # Save the uploaded file asynchronously
    dest = MEDIA_DIR / file.filename
    data = await file.read()
    dest.write_bytes(data)

    # Initialize agent
    assistant = Assistant(state=state_data)
    await assistant.authorization()

    # Preprocess file
    file_contents = await preprocess_file(str(dest))
    state_data["message"] = HumanMessage(
        content=f"{state_data.get('message', {}).get('content' 'User uploaded the image.')} \nImage Description: {file_contents}"
    )

    # Call the agents
    assistant.state = state_data
    response = await assistant.run()
    os.remove(str(dest))
    return response

@app.post("/file")
async def file_mode(
    state: str = Form(...),
    file: UploadFile = File(...)
) -> Dict[str, Any]:
    # Parse JSON string form field into dict
    try:
        state_data = json.loads(state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'state' form field")

    # Save the uploaded file asynchronously
    dest = MEDIA_DIR / file.filename
    data = await file.read()
    dest.write_bytes(data)

    #Initialize agent
    assistant = Assistant(state=state_data)
    await assistant.authorization()

    # Preprocess file
    file_contents = await preprocess_file(str(dest))
    state_data["message"] = HumanMessage(
        content=f"{state_data.get('message', {}).get('content' 'User uploaded the file.')} \nFile description: {file_contents}"
    )

    # Call the agents
    assistant.state = state_data
    response = await assistant.run()
    os.remove(str(dest))
    return response

@app.post("/text")
async def text_mode(
    state: str = Form(...),
) -> Dict[str, Any]:
    # Parse JSON string form field into dict
    try:
        state_data = json.loads(state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'state' form field")
    # Reformat the message
    state_data['message'] = HumanMessage(content=state_data['message']['content'])
    # Call the agents
    assistant = Assistant(state=state_data)
    await assistant.authorization()
    response = await assistant.run()
    return response

@app.post("/authorization")
async def authorization_mode(
    state: str = Form(...),
):
    # Parse JSON string form field into dict
    try:
        state_data = json.loads(state)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in 'state' form field")
    # Call the agents
    assistant = Assistant(state=state_data)
    await assistant.authorization()
    return {"message": "Authorization successful"}
