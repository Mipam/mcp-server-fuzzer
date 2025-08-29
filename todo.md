# MCP Fuzzer GUI - TODO List

This file tracks the remaining tasks to complete the MCP Fuzzer GUI and implement all the features from the documentation.

## Phase 1: Core Fuzzing Features (Completed)

- [x] Implement GUI with all settings widgets
- [x] Implement Tool Fuzzing
- [x] Implement Protocol Fuzzing
- [x] Implement Transport Layer Abstraction
- [x] Implement HTTP Transport
- [x] Implement SSE Transport
- [x] Implement Fuzzing Phases (realistic/aggressive)

## Phase 2: Remaining Protocols

- [ ] Implement Stdio Transport
  - [ ] Create `mcp_fuzzer/transport/stdio.py`
  - [ ] Implement logic to run server command as a subprocess using a new `runtime` module for process management.
  - [ ] Handle stdin/stdout communication.
  - [ ] Add to transport factory.
- [ ] Implement StreamableHTTP Transport
  - [ ] Create `mcp_fuzzer/transport/streamablehttp.py`
  - [ ] Implement logic for initial handshake and session management.
  - [ ] Add to transport factory.

## Phase 3: Advanced Features

- [ ] Implement Authentication
  - [ ] Create `mcp_fuzzer/auth` module.
  - [ ] Implement `AuthManager` to handle different auth providers.
  - [ ] Add support for API Key, Basic Auth, and OAuth from config file (`--auth-config`).
  - [ ] Add support for auth from environment variables (`--auth-env`).
  - [ ] Integrate `AuthManager` with the transport layer.
- [ ] Implement Safety System
  - [ ] Create `mcp_fuzzer/safety_system` module.
  - [ ] Implement `SafetySystem` class with argument filtering.
  - [ ] Implement `SystemBlocker` for command blocking (`--enable-safety-system`).
  - [ ] Add filesystem sandboxing (`--fs-root`).
  - [ ] Add support for custom safety plugins (`--safety-plugin`).
  - [ ] Add `--no-safety` and `--retry-with-safety-on-interrupt` flags.
  - [ ] Integrate with `run_fuzzer`.
- [ ] Implement Reporting System
  - [ ] Create `mcp_fuzzer/reports` module.
  - [ ] Implement `Reporter` class to handle report generation.
  - [ ] Add formatters for JSON and Text reports.
  - [ ] Implement report generation to a specified directory (`--output-dir`).
  - [ ] Implement safety report generation (`--safety-report`).
  - [ ] Implement safety data export (`--export-safety-data`).
  - [ ] Integrate with `run_fuzzer` to generate reports at the end of a session.

## Phase 4: Final Touches & Integration

- [ ] Integrate all new features with the GUI.
  - [ ] Ensure all settings from the GUI are correctly passed to the fuzzer.
  - [ ] Display safety and reporting information in the GUI.
- [ ] Thorough testing of all features and GUI options.
- [ ] Code Cleanup
  - [x] Remove unused `mcp_fuzzer/utils.py` file.
  - [ ] Add docstrings and type hints throughout the codebase.
  - [ ] General code cleanup and refactoring.
- [ ] Update project documentation to reflect the new architecture and features.
