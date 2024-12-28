import json
import fastapi
import pydantic
from fastapi import Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from .shared import globals
from .chat_with_products import chat_with_products

router = fastapi.APIRouter()
templates = Jinja2Templates(directory="api/templates")


class Message(pydantic.BaseModel):
    """
    Simple Pydantic model for an individual user message:
    content (string) and role (default= "user").
    """
    content: str
    role: str = "user"


class ChatRequest(pydantic.BaseModel):
    """
    Pydantic model describing the shape of the request body for chat.
    """
    messages: list[Message]


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    GET / - Render the main UI (index.html), 
    passing 'request' so Jinja2 can build URLs.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/chat/stream")
async def chat_stream_handler(chat_request: ChatRequest) -> StreamingResponse:
    """
    POST /chat/stream - Streams chat responses line by line in JSON.
    The front end is expected to parse line-delimited JSON for each chunk.
    """
    # Grab the chat client from global
    chat_client = globals["chat"]
    if chat_client is None:
        raise RuntimeError("Chat client not initialized")

    async def response_stream():
        # Convert each Pydantic message object to dict
        messages = [
            {"role": m.role, "content": m.content}
            for m in chat_request.messages
        ]
        # Use your custom function that calls the Azure Chat endpoint, returning a streaming generator
        chat_coroutine = chat_with_products(messages)

        # Iterate over the streaming chat response from chat_with_products
        for event in chat_coroutine:
            if event.choices:
                first_choice = event.choices[0]
                # Skip if there's no delta or no content in that delta
                if not (hasattr(first_choice, "delta") and first_choice.delta.content):
                    continue

                # Build a JSON-friendly chunk
                chunk_data = {
                    "delta": {
                        "content": first_choice.delta.content,
                        "role": first_choice.delta.role
                    }
                }
                # Yield line-delimited JSON (no SSE prefix)
                yield json.dumps(chunk_data, ensure_ascii=False) + "\n"

    # Return a StreamingResponse with plain text so the front end 
    # can read each line as JSON
    return StreamingResponse(
        response_stream(),
        media_type="text/plain"
    )
