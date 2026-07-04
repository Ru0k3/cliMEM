from contextlib import asynccontextmanager
from pathlib import Path
from .session import save_current_session
from fastapi import FastAPI

from .filter import (
    get_chat_log,
    process_session,
    clear_chat_log,
)

from .proxy import router
from .storage import close_database, end_session, get_current_session, init_database

from .memory import (
    get_dataset_name,
    store_memory,
    improve_memory,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()

    yield

    print("\nSaving session...\n")

    await save_current_session("normal_shutdown")

    close_database()


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def health():
    return {"message": "server is alive"}


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()