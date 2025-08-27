import logging
import traceback
import uuid
from typing import Any, Dict, List, Optional

import httpx

from mcp_fuzzer.strategies import (
    make_fuzz_strategy_from_jsonschema,
    make_protocol_fuzz_strategy,
)
from mcp_fuzzer.transport.factory import create_transport


async def run_fuzzer(settings: dict):
    """Runs the fuzzer and yields summary results."""
    protocol = settings.get("protocol", "http")
    url = settings.get("url")
    transport = create_transport(protocol, url)

    mode = settings.get("mode", "tools")
    if mode in ["tools", "both"]:
        async for summary in run_tool_fuzzer(transport, settings):
            yield summary
    if mode in ["protocol", "both"]:
        async for summary in run_protocol_fuzzer(transport, settings):
            yield summary


async def run_tool_fuzzer(transport, settings: dict):
    """Runs the tool fuzzer and yields summary results."""
    tools = await transport.get_tools()
    if not tools:
        logging.warning("Server returned an empty list of tools. Exiting.")
        return

    for tool in tools:
        logging.info(f"Fuzzing tool: {tool['name']}")
        summary = {}
        try:
            results = await fuzz_tool(transport, tool, settings)
            exceptions = [r for r in results if "exception" in r]
            summary[tool["name"]] = {
                "total_runs": settings.get("runs", 10),
                "exceptions": len(exceptions),
                "example_exception": exceptions[0] if exceptions else None,
            }
        except Exception as e:
            summary[tool["name"]] = {"error": str(e)}
        yield summary


async def run_protocol_fuzzer(transport, settings: dict):
    """Runs the protocol fuzzer and yields summary results."""
    runs = settings.get("runs_per_type", 5)
    logging.info(f"Fuzzing protocol with {runs} runs per type.")
    summary = {}
    try:
        results = await fuzz_protocol(transport, settings)
        exceptions = [r for r in results if "exception" in r]
        summary["protocol"] = {
            "total_runs": runs,
            "exceptions": len(exceptions),
            "example_exception": exceptions[0] if exceptions else None,
        }
    except Exception as e:
        summary["protocol"] = {"error": str(e)}
    yield summary


async def fuzz_protocol(transport, settings: dict):
    """Fuzz the protocol with malformed requests."""
    runs = settings.get("runs_per_type", 5)
    phase = settings.get("phase", "aggressive")
    results = []
    strategy = make_protocol_fuzz_strategy(phase)
    for _ in range(runs):
        payload = strategy.example()
        try:
            result = await transport.send_raw(payload)
            results.append({"payload": payload, "result": result})
        except Exception as e:
            results.append(
                {"payload": payload, "exception": str(e), "traceback": traceback.format_exc()}
            )
    return results


async def fuzz_tool(transport, tool: dict, settings: dict):
    """Fuzz a tool by calling it with random/edge-case arguments."""
    runs = settings.get("runs", 10)
    phase = settings.get("phase", "aggressive")
    results = []
    schema = tool.get("inputSchema", {})
    strategy = make_fuzz_strategy_from_jsonschema(schema, phase)
    for _ in range(runs):
        args = strategy.example()
        try:
            result = await transport.call_tool(tool["name"], args)
            results.append({"args": args, "result": result})
        except Exception as e:
            results.append(
                {"args": args, "exception": str(e), "traceback": traceback.format_exc()}
            )
    return results
