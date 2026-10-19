import os
import logging
from functools import lru_cache
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel, ConfigDict, Field

from stock_tools import STOCK_TOOLS

load_dotenv()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EquityLens API",
    description="Streaming AI stock analysis agent with Yahoo Finance tools.",
    version="0.1.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

checkpointer = InMemorySaver()


class PromptObject(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    id: str
    role: Literal["user"]


class RequestObject(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    prompt: PromptObject
    thread_id: str = Field(alias="threadId", min_length=1, max_length=200)
    response_id: str | None = Field(default=None, alias="responseId")


@lru_cache(maxsize=1)
def get_agent():
    api_key = os.getenv("THESYS_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Configure THESYS_API_KEY with your Thesys API key in the repository root .env file.")
    model = ChatOpenAI(
        model=os.getenv("THESYS_MODEL", "c1/openai/gpt-5/v-20250930"),
        base_url="https://api.thesys.dev/v1/embed/",
        api_key=api_key,
    )
    return create_agent(model=model, checkpointer=checkpointer, tools=STOCK_TOOLS)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "equitylens-api"}


@app.post("/api/chat")
async def chat(request: RequestObject) -> StreamingResponse:
    try:
        agent = get_agent()
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    config = {"configurable": {"thread_id": request.thread_id}}

    def generate():
        try:
            messages = [
                SystemMessage(
                    "You are EquityLens, an AI stock analysis assistant. You can retrieve the latest available stock close, "
                    "historical OHLCV prices for a date range, recent company news, and balance sheet data using your tools. "
                    "Use tools for current or ticker-specific facts; never invent results. Explain the source and date of figures, "
                    "distinguish facts from interpretation, and state when data is missing. You may generate interactive charts, "
                    "tables, summaries, and follow-up actions. Do not make personalized investment recommendations. "
                    "This is educational research, not financial advice."
                ),
                HumanMessage(request.prompt.content),
            ]
            for token, _metadata in agent.stream(
                {"messages": messages},
                stream_mode="messages",
                config=config,
            ):
                if isinstance(token.content, str) and token.content:
                    yield token.content
                elif isinstance(token.content, list):
                    for block in token.content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            yield block.get("text", "")
        except Exception:
            logger.exception("Stock analysis request failed for thread %s", request.thread_id)
            yield "\n\nThe analysis request failed. Check the server configuration and try again."

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )