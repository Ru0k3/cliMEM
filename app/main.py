from fastapi import FastAPI

from .filter import get_chat_log
from .proxy import router

app = FastAPI()

app.include_router(router)


@app.get("/")
async def health():
    return {
        "message": "server is alive",
    }


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()