import argparse
import asyncio
import logging

from rich.console import Console
from rich.table import Table

from mcp_fuzzer.client import run_fuzzer

logging.basicConfig(level=logging.INFO)


async def main():
    parser = argparse.ArgumentParser(description="MCP Fuzzer Client (JSON-RPC 2.0)")
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the MCP server's JSON-RPC endpoint (e.g., http://localhost:8000/rpc)",
    )
    parser.add_argument(
        "--runs", type=int, default=10, help="Number of fuzzing runs per tool"
    )
    args = parser.parse_args()

    settings = {"url": args.url, "runs": args.runs}

    console = Console()
    table = Table(title="Fuzzing Summary")
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Total Runs", justify="right")
    table.add_column("Exceptions", justify="right")
    table.add_column("Example Exception", style="red")
    table.add_column("Error", style="magenta")

    async for summary in run_fuzzer(settings):
        for tool, result in summary.items():
            error = result.get("error", "")
            total_runs = str(result.get("total_runs", ""))
            exceptions = str(result.get("exceptions", ""))
            example_exception = ""
            if result.get("example_exception"):
                ex = result["example_exception"]
                example_exception = ex.get("exception", "")
            table.add_row(tool, total_runs, exceptions, example_exception, error)

    console.print(table)


if __name__ == "__main__":
    asyncio.run(main())
