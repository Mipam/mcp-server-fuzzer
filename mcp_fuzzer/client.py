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


from mcp_fuzzer.auth.manager import AuthManager
from mcp_fuzzer.safety_system.safety import SafetySystem
from mcp_fuzzer.safety_system.system_blocker import SystemBlocker
from mcp_fuzzer.reports.reporter import Reporter
from mcp_fuzzer.transport.base import TransportProtocol


async def run_fuzzer(settings: Dict[str, Any]) -> None:
    """
    Runs the fuzzer with the given settings.

    This is the main entry point for the fuzzer. It creates the transport,
    safety system, and reporter, and then runs the fuzzer in the selected
    mode.

    Args:
        settings: A dictionary of fuzzer settings.
    """
    protocol = settings.get("protocol", "http")
    url = settings.get("url")
    auth_config = settings.get("auth_config")
    use_env = settings.get("auth_env")
    auth_manager = AuthManager(auth_config, use_env)
    transport = create_transport(protocol, url, auth_manager)

    safety_system = SafetySystem(
        fs_root=settings.get("fs_root"), no_safety=settings.get("no_safety")
    )

    reporter = Reporter(output_dir=settings.get("output_dir", "reports"))

    async def execute_fuzzing():
        mode = settings.get("mode", "tools")
        if mode in ["tools", "both"]:
            async for summary in run_tool_fuzzer(transport, settings, safety_system, reporter):
                yield summary
        if mode in ["protocol", "both"]:
            async for summary in run_protocol_fuzzer(transport, settings, safety_system, reporter):
                yield summary

    if protocol == "stdio" and settings.get("enable_safety_system"):
        with SystemBlocker():
            async for summary in execute_fuzzing():
                yield summary
    else:
        async for summary in execute_fuzzing():
            yield summary

    reporter.generate_json_report()
    reporter.generate_text_report()

    await transport.close()


async def run_tool_fuzzer(
    transport: TransportProtocol,
    settings: Dict[str, Any],
    safety_system: SafetySystem,
    reporter: Reporter,
):
    """
    Runs the tool fuzzer.

    This function discovers the available tools from the server and then
    fuzzes each one.

    Args:
        transport: The transport to use for communication.
        settings: A dictionary of fuzzer settings.
        safety_system: The safety system to use for filtering.
        reporter: The reporter to use for recording results.
    """
    tools = await transport.get_tools()
    if not tools:
        logging.warning("Server returned an empty list of tools. Exiting.")
        return

    for tool in tools:
        logging.info(f"Fuzzing tool: {tool['name']}")
        summary = {}
        try:
            results = await fuzz_tool(transport, tool, settings, safety_system)
            exceptions = [r for r in results if "exception" in r]
            summary[tool["name"]] = {
                "total_runs": settings.get("runs", 10),
                "exceptions": len(exceptions),
                "example_exception": exceptions[0] if exceptions else None,
            }
        except Exception as e:
            summary[tool["name"]] = {"error": str(e)}

        reporter.add_result({"target": tool["name"], **summary[tool["name"]]})
        yield summary


async def run_protocol_fuzzer(
    transport: TransportProtocol,
    settings: Dict[str, Any],
    safety_system: SafetySystem,
    reporter: Reporter,
):
    """
    Runs the protocol fuzzer.

    Args:
        transport: The transport to use for communication.
        settings: A dictionary of fuzzer settings.
        safety_system: The safety system to use for filtering.
        reporter: The reporter to use for recording results.
    """
    runs = settings.get("runs_per_type", 5)
    logging.info(f"Fuzzing protocol with {runs} runs per type.")
    summary = {}
    try:
        results = await fuzz_protocol(transport, settings, safety_system)
        exceptions = [r for r in results if "exception" in r]
        summary["protocol"] = {
            "total_runs": runs,
            "exceptions": len(exceptions),
            "example_exception": exceptions[0] if exceptions else None,
        }
    except Exception as e:
        summary["protocol"] = {"error": str(e)}

    reporter.add_result({"target": "protocol", **summary["protocol"]})
    yield summary


async def fuzz_protocol(
    transport: TransportProtocol,
    settings: Dict[str, Any],
    safety_system: SafetySystem,
) -> List[Dict[str, Any]]:
    """
    Fuzz the protocol with malformed requests.

    Args:
        transport: The transport to use for communication.
        settings: A dictionary of fuzzer settings.
        safety_system: The safety system to use for filtering.

    Returns:
        A list of fuzzing results.
    """
    runs = settings.get("runs_per_type", 5)
    phase = settings.get("phase", "aggressive")
    results = []
    strategy = make_protocol_fuzz_strategy(phase)
    for _ in range(runs):
        payload = strategy.example()
        try:
            safe_payload = safety_system.filter_arguments(payload)
            result = await transport.send_raw(safe_payload)
            results.append({"payload": safe_payload, "result": result})
        except Exception as e:
            results.append(
                {"payload": payload, "exception": str(e), "traceback": traceback.format_exc()}
            )
    return results


async def fuzz_tool(
    transport: TransportProtocol,
    tool: Dict[str, Any],
    settings: Dict[str, Any],
    safety_system: SafetySystem,
) -> List[Dict[str, Any]]:
    """
    Fuzz a tool by calling it with random/edge-case arguments.

    Args:
        transport: The transport to use for communication.
        tool: The tool to fuzz.
        settings: A dictionary of fuzzer settings.
        safety_system: The safety system to use for filtering.

    Returns:
        A list of fuzzing results.
    """
    runs = settings.get("runs", 10)
    phase = settings.get("phase", "aggressive")
    results = []
    schema = tool.get("inputSchema", {})
    strategy = make_fuzz_strategy_from_jsonschema(schema, phase)
    for _ in range(runs):
        args = strategy.example()
        try:
            safe_args = safety_system.filter_arguments(args)
            result = await transport.call_tool(tool["name"], safe_args)
            results.append({"args": safe_args, "result": result})
        except Exception as e:
            results.append(
                {"args": args, "exception": str(e), "traceback": traceback.format_exc()}
            )
    return results
