import asyncio
import sys
from pathlib import Path
from app.memory import ensure_cognee_connection
import cognee

from app.memory import get_dataset_name


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/remember_sample.py \"<fact to remember>\"")
        sys.exit(1)

    fact = sys.argv[1]
    dataset_name = get_dataset_name(str(Path.cwd()))

    await ensure_cognee_connection()          # <-- add this line

    print(f"Dataset: {dataset_name}")
    print(f"Remembering: {fact}")

    await cognee.remember(fact, dataset_name=dataset_name)

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())