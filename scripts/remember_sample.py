import asyncio
import sys

import cognee

from app.memory import ensure_cognee_connection, get_dataset_name
from app.utils import get_cwd


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/remember_sample.py \"<fact to remember>\"")
        sys.exit(1)

    fact = sys.argv[1]
    dataset_name = get_dataset_name(str(get_cwd()))

    await ensure_cognee_connection()          # <-- add this line

    print(f"Dataset: {dataset_name}")
    print(f"Remembering: {fact}")

    await cognee.remember(fact, dataset_name=dataset_name)

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())