import asyncio

import cognee

from app.memory import get_dataset_name
from app.utils import get_cwd


async def main():
    dataset_name = get_dataset_name(str(get_cwd()))

    print(f"Dataset: {dataset_name}")

    result = await cognee.recall(
        query_text="What do you know about the CliMEM project?",
        datasets=[dataset_name],      # <-- IMPORTANT
        only_context=True,
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(main())