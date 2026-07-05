import asyncio
from pathlib import Path
from cognee.api.v1.visualize.visualize import visualize_graph
from app.memory import get_dataset_name

async def main():
    working_directory = str(Path.cwd())
    dataset_name = get_dataset_name(working_directory)
    print(f"Visualizing dataset: {dataset_name}")

    output_path = str(Path.cwd() / "graph_after_recall.html")
    await visualize_graph(output_path, dataset=dataset_name)
    print(f"Graph written to {output_path} — open it in a browser")

if __name__ == "__main__":
    asyncio.run(main())