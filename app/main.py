from contextlib import asynccontextmanager

from fastapi import FastAPI

from .filter import get_chat_log
from .memory import ensure_cognee_connection
from .proxy import router
from .session import save_current_session
from .storage import close_database, init_database
import asyncio
import cognee
from .session import (
    idle_watcher,
    save_current_session,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local mode: returns immediately.
    # Cloud mode: verifies the Cognee connection once at startup.
    await ensure_cognee_connection()
    await cognee.run_migrations()
    init_database()

    watcher_task = asyncio.create_task(
        idle_watcher()
    )

    try:
        yield

    finally:

        watcher_task.cancel()

        print("\nSaving session...\n")

        await save_current_session(
            "normal_shutdown"
        )

        close_database()


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def health():
    return {"message": "server is alive"}


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()