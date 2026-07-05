import asyncio
from app.memory import ensure_cognee_connection
from app.config import COGNEE_MODE, COGNEE_SERVICE_URL

async def main():
    print(f"COGNEE_MODE={COGNEE_MODE}")
    print(f"COGNEE_SERVICE_URL={COGNEE_SERVICE_URL}")
    await ensure_cognee_connection()
    print("If no error above, connection call completed.")

asyncio.run(main())