from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from .filter import get_chat_log, process_session
from .proxy import router
from .storage import close_database, end_session, get_current_session, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()

    yield

    print("\nSaving session...\n")

    process_session(
        get_chat_log(),
        str(Path.cwd()),
        get_current_session(),
    )

    end_session("normal_shutdown")
    close_database()


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def health():
    return {"message": "server is alive"}


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()