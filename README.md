# MCP Fuzzer

A tool for fuzzing MCP servers, with both a CLI and a GUI. It supports multiple transport protocols, fuzzing phases, and has a built-in safety system.

## Features
- **GUI and CLI Interfaces**: Run the fuzzer from a modern graphical user interface or from the command line.
- **Multi-Protocol Support**: Fuzz servers over HTTP, SSE, Stdio, and StreamableHTTP.
- **Comprehensive Fuzzing**: Perform both tool-level and protocol-level fuzzing.
- **Two-Phase Fuzzing**: Use "realistic" or "aggressive" fuzzing strategies.
- **Safety System**: Protect your system with features like command blocking and filesystem sandboxing.
- **Reporting**: Generate JSON and text reports of fuzzing sessions.
- **Authentication**: Connect to servers that require API Key, Basic, or OAuth authentication.

## Installation

Install with pip:

```bash
pip install -e .
```

## Usage

### GUI

To launch the graphical user interface, run:

```bash
mcp-fuzzer-gui
```

The GUI provides access to all the fuzzer's options in a user-friendly interface.

### Command-Line Interface

You can run the fuzzer from the command line with a wide range of options.

**Basic Usage:**
```bash
mcp-fuzzer-client --url http://localhost:8000/mcp/ --runs 10
```

**Full Usage:**
For a full list of all the command-line options, see the [documentation](https://agent-hellboy.github.io/mcp-server-fuzzer/reference/).

## Output

Results are shown in a colorized table in the CLI, or in a results table in the GUI. Reports can also be generated in JSON and text formats.

---

**Project dependencies are managed via `pyproject.toml`.**

Test result of  fuzz testing of https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-streamablehttp-stateless

![fuzzer](./fuzzer.png)