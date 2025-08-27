import json
import logging
import traceback
import uuid
from typing import Any, Dict, List, Optional

import httpx

from mcp_fuzzer.strategies import make_fuzz_strategy_from_jsonschema


def jsonrpc_request(
    url: str, method: str, params: Optional[Dict[str, Any]] = None
) -> Any:
    """Make a JSON-RPC request to the MCP server."""
    request_id = str(uuid.uuid4())
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params or {},
    }

    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()

        # Try to parse as JSON first
        try:
            data = response.json()
        except json.JSONDecodeError:
            # If not JSON, try to parse as SSE
            logging.info("Response is not JSON, trying to parse as SSE")
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    try:
                        data = json.loads(line[len("data:") :].strip())
                        break
                    except json.JSONDecodeError:
                        logging.error("Failed to parse SSE data line as JSON")
                        raise
            else:
                logging.error("No valid data: line found in SSE response")
                raise Exception("Invalid SSE response format")

        if "error" in data:
            logging.error("Server returned error: %s", data["error"])
            raise Exception(f"Server error: {data['error']}")
        # If the payload is a full JSON-RPC envelope keep existing behaviour,
        # otherwise fall back to the raw object (covers SSE streams that send
        # only the result).
        return data.get("result", data)
    except httpx.HTTPError:
        logging.error("HTTP error during request")
        raise
    except json.JSONDecodeError:
        logging.error("Raw response: %s", response.text)
        raise


def get_tools_from_server(url: str) -> List[Dict[str, Any]]:
    """Fetch the list of tools and their schemas from the MCP server using JSON-RPC."""
    try:
        response = jsonrpc_request(url, "tools/list")
        logging.info("Raw server response: %s", response)

        if not isinstance(response, dict):
            logging.warning(
                "Server response is not a dictionary. Got type: %s", type(response)
            )
            return []

        if "tools" not in response:
            logging.warning(
                "Server response missing 'tools' key. Keys present: %s",
                list(response.keys()),
            )
            return []

        tools = response["tools"]
        logging.info("Found %d tools from server", len(tools))
        return tools

    except Exception as e:
        logging.exception("Failed to fetch tools from server: %s", e)
        return []
        logging.warning("Error fetching tools list: %s", str(e))
        return []


async def run_fuzzer(url: str, runs: int):
    """Runs the fuzzer and yields summary results."""
    tools = get_tools_from_server(url)
    if not tools:
        logging.warning("Server returned an empty list of tools. Exiting.")
        return

    for tool in tools:
        logging.info(f"Fuzzing tool: {tool['name']}")
        summary = {}
        try:
            results = await fuzz_tool(url, tool, runs)
            exceptions = [r for r in results if "exception" in r]
            summary[tool["name"]] = {
                "total_runs": runs,
                "exceptions": len(exceptions),
                "example_exception": exceptions[0] if exceptions else None,
            }
        except Exception as e:
            summary[tool["name"]] = {"error": str(e)}
        yield summary


async def fuzz_tool(url: str, tool, runs: int = 10):
    """Fuzz a tool by calling it with random/edge-case arguments."""
    results = []
    schema = tool.get("inputSchema", {})
    strategy = make_fuzz_strategy_from_jsonschema(schema)
    headers = {
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    for _ in range(runs):
        args = strategy.example()
        try:
            params = {"name": tool["name"], "arguments": args}
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tools/call",
                "params": params,
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                try:
                    result = resp.json()
                except Exception:
                    # SSE fallback
                    for line in resp.text.splitlines():
                        if line.startswith("data:"):
                            import json

                            data_json = line[len("data:") :].strip()
                            result = json.loads(data_json)
                            break
                    else:
                        logging.warning(
                            "Server returned a non-JSON (or SSE) response for tool call. Appending dummy result."
                        )
                        result = {"error": "Non-JSON response"}
            results.append({"args": args, "result": result})
        except Exception as e:
            results.append(
                {"args": args, "exception": str(e), "traceback": traceback.format_exc()}
            )
    return results
