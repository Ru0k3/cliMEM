from contextlib import asynccontextmanager

from fastapi import FastAPI

from .filter import get_chat_log
from .memory import ensure_cognee_connection
from .proxy import router
from .session import save_current_session
from .storage import close_database, init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Local mode: returns immediately.
    # Cloud mode: verifies the Cognee connection once at startup.
    await ensure_cognee_connection()

    # Initialize SQLite session database.
    init_database()

    try:
        yield
    finally:
        print("\nSaving session...\n")

        # Save the current session before shutting down.
        await save_current_session("normal_shutdown")

        # Always close the database.
        close_database()


app = FastAPI(lifespan=lifespan)

app.include_router(router)


@app.get("/")
async def health():
    return {"message": "server is alive"}


@app.get("/chat-log")
async def chat_log():
    return get_chat_log()