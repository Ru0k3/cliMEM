from contextlib import asynccontextmanager

from fastapi import FastAPI

from .filter import get_chat_log
from .proxy import router
from .storage import end_session, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the server starts and once when it stops.
    """

    init_database()

    yield

    end_session()


app = FastAPI(
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def health():
    return {
        "message": "server is alive",
    }


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()