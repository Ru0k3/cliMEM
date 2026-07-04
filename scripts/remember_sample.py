import asyncio
from pathlib import Path

import cognee

from app.memory import get_dataset_name

# Import this from your project


async def main():
    dataset_name = get_dataset_name(str(Path.cwd()))

    print(f"Dataset: {dataset_name}")
    print("Remembering...")

    await cognee.remember(
        "The CliMEM project uses FastAPI.",
        dataset_name=dataset_name,
    )

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())