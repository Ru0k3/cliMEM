import asyncio
from cognee.api.v1.visualize.visualize import visualize_graph
from app.storage import build_dataset_name  # adjust import to match actual location

async def main():
    working_directory = "."  # or pass explicitly if checking a specific project
    dataset_name = build_dataset_name(working_directory)
    print(f"Visualizing dataset: {dataset_name}")

    output_path = "graph_after_recall.html"
    await visualize_graph(output_path)
    print(f"Graph written to {output_path} — open it in a browser")

if __name__ == "__main__":
    asyncio.run(main())