# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-06-17

### Added

**Remote MCP Transport**
- SSE transport mode: `superrtl mcp --transport sse`
- Streamable HTTP transport mode: `superrtl mcp --transport streamable-http`
- CLI options: `--transport`, `--host`, `--port`
- `init-mcp` generates remote URL configuration

**Protocol Decode Enhancements**
- I2C: ACK/NACK detection, Repeated START support, state machine rewrite
- SPI: CS-active-high mode, inter-frame gap detection, frame duration
- UART: LSB-first bit assembly fix, value lookup logic, parity verification, frame error detection

**Test Suite**
- New test_protocol_decode.py (28 tests for SPI/I2C/UART)
- New test_mcp_prompts.py (9 tests for MCP prompts)
- New test_simulate_parallel.py (5 tests for parallel simulation)
- New test_verify.py (6 tests for verify_design pipeline)

### Fixed
- GitHub URL inconsistency (unified to egg-rolls/SuperRTL)
- Windows command injection in run_command() (use list2cmdline)
- Protocol decoders now use time-based signal lookup (not array index)
- `--verbose` flag now works (console handler level matches logger)
- VCD filename uniqueness (avoids concurrent simulation conflicts)
- I2C dead branch after ACK state

### Changed
- compile_verilog and lint_verilog now accept `timeout` parameter
- formal_verify now accepts `solver` parameter (yices/boolector/z3)
- Error handling: narrow exception catching with logging
- YAML config parse errors now produce warnings

### Removed
- cleanup.py module (unused)
- testbench.py module (dead code, replaced by MCP prompt for AI agent)
- LogContext class (unused)
- resolve_path function (unused)

## [0.5.0] - 2026-06-15

### Added

**Verify Workflow**
- `superrtl verify` CLI command: one-click compile + simulate + lint + review
- MCP tool `verify_design` for comprehensive validation
- Skip individual steps with `--skip compile/simulate/lint/review`

**Parallel Simulation**
- MCP tool `simulate_parallel`: run multiple testbenches concurrently
- Configurable max concurrency (default 4)

**Protocol Decode**
- SPI decoder (CPOL/CPHA support, MOSI/MISO extraction)
- I2C decoder (address/data byte extraction, start/stop detection)
- UART decoder (TX/RX frame extraction)
- Integrated into `analyze_waveform` via `protocol` parameter

**Coverage**
- Toggle coverage computation from VCD data
- Per-signal toggle status and coverage percentage

**AXI-Lite IP**
- `shared/templates/axi_lite_slave.v`: parameterized register interface
- `shared/skills/verilog_axi_lite_slave.md`: design guide

### Changed
- All tools support `file` parameter for file path input
- POSIX path normalization (`/d/...` → `D:\...` on Windows)
- Error messages localized to Chinese
- TEMP dir explicitly set to system temp (fixes .hermes-tmp issues)
- CLI formal verification renamed to `superrtl formal`
- MCP tools: 10 total (was 8)

## [0.4.0] - 2026-06-15

### Added

**Formal Verification (SymbiYosys)**
- `superrtl verify` CLI command for BMC model checking
- MCP tool `formal_verify` for AI-driven formal verification
- New skill: `verilog_formal.md` with property assertion patterns
- Supports assert/assume/cover properties
- Configurable BMC depth and timeout

**Code Review Tool**
- `superrtl review` CLI command for static code analysis
- MCP tool `review_verilog` for AI-driven code review
- Checks: synthesizability, latch inference, naming, reset, case statements
- Structured issue reports with severity levels

**Testbench Enhancement**
- Boundary value testing in comprehensive mode (min, 1, max-1, max for each port)
- Random test checks (X-propagation detection)
- Walking pattern generation for bus signals

**CI Enhancement**
- EDA tools installed on Ubuntu CI (iverilog, yosys, verilator)
- Shared test fixtures in `conftest.py`
- Custom pytest markers for integration tests
- `pytest-timeout` dependency (60s default)
- pip dependency caching in CI

**Error Handling**
- Unified error return structure across all tools
- `stage` field on all multi-stage tool errors
- Error summary strings alongside detailed error lists
- Logging in dependency analysis for silent failures

### Changed
- `sby` (SymbiYosys) now shown in `superrtl check-tools`
- Test count: 159 tests (was 139), all passing
- Tools now use structured logging via `logging` module

### Fixed
- `waveform.py` missing `encoding="utf-8"` on file open
- Duplicated VCD parsing logic (refactored to shared `parse_vcd()`)
- Unused `get_skill_raw` export removed
- Misleading `--port` parameter removed from `mcp` command
- `INTRODUCTION.md` incorrect GitHub URL
- `CHANGELOG.md` missing 0.3.1 comparison link

## [0.3.1] - 2026-06-14

### Added

**Skills Expansion**
- 20 skills total (was 11): added SPI, I2C, AXI-Lite, PWM, debouncer, edge detector, arbiter, CRC, reset sync
- All skills include: design points, code templates, common errors, verification checklist

**Testbench Generation**
- Generate actual test stimulus (zero, all-ones, increment, alternating, random)
- Comprehensive mode with self-checking assertions
- Test summary with pass/fail counts
- Better comments explaining each test case

**Robustness**
- Input validation module (file size, code length, file count limits)
- Logging system with configurable levels
- Resource cleanup with signal handlers
- MCP Prompts: 6 skill-based prompts for AI agents

## [0.3.0] - 2026-06-14

### Added

**Project Management (Breaking)**
- **Project configuration**: `.superrtl.yaml` project config file
- **`superrtl init`**: Auto-detect sources, generate project config
- **`superrtl build`**: Compile with automatic dependency ordering
- **`superrtl test`**: Run all testbenches from config
- **`superrtl graph`**: Module dependency visualization (text/dot/json)
- **`superrtl watch`**: Auto-compile on file changes

**Multi-file Support (Breaking)**
- `compile` and `simulate` commands now support multiple files
- Glob patterns: `superrtl compile src/*.v`
- Directory mode: `superrtl compile src/`
- Dependency auto-resolution: topological sort for compilation order
- Circular dependency detection

**Waveform Viewer**
- Interactive web-based waveform viewer: `superrtl waveform view`
- Canvas-based rendering with zoom/pan
- Signal search and filtering
- Bus signal grouping (hex display)
- Cursor tracking with value tooltip
- HiDPI/Retina display support

**Skills & Templates**
- 11 skills (was 9): added UART, memory, testbench methodology
- 10 templates (was 2): added FSM, FIFO, decoder, mux, shift_reg, clk_div, synchronizer, RAM
- YAML frontmatter metadata for all skills
- `superrtl skills list` and `superrtl skills show` CLI commands

**CLI Improvements**
- `--json` flag on all tool commands
- Rich progress spinners during execution
- `waveform` command group with `analyze` and `view` subcommands

### Changed
- `simulate` command syntax: `superrtl simulate <testbench> <designs...>`
- `compile` command accepts multiple files
- VCD files now copied to current directory after simulation
- Synthesis `target` parameter now functional (generic/xilinx/ice40)
- Testbench `style` parameter now affects generation

### Fixed
- VCD file deleted before caller could use it
- `target` parameter in synthesize was a no-op
- `style` parameter in testbench had no effect
- FileNotFoundError messages now recommend `superrtl setup`
- Windows CI encoding issues with Chinese characters
- Parameterized module instantiation parsing

### Tests
- 139 tests (was 104), all passing
- Added test_project.py: 14 tests for project configuration
- Added test_deps.py: 21 tests for dependency resolution

## [0.2.0] - 2026-06-13

### Added
- **Automatic EDA tool installation**: `superrtl setup` command downloads OSS CAD Suite
- **Docker support**: Complete Dockerfile with all EDA tools pre-installed
- **Runtime environment management**: Automatic PATH configuration for local tools
- **New CLI commands**: `setup`, `uninstall`, `check-tools`
- **Cross-platform support**: Windows, Linux, macOS
- **Comprehensive test suite**: 110 tests with 83% coverage

### Changed
- Migrated from bare subprocess calls to `run_command` wrapper
- Updated MCP Server to use correct `@app.list_tools()` decorator API
- Improved error handling in all tool wrappers
- Updated testbench generator to handle modules without clock/reset

### Fixed
- Windows DLL dependency issues with iverilog
- Unicode encoding issues in Windows console
- Import order and unused import warnings
- Resources path resolution for skills and templates

## [0.1.0] - 2026-06-11

### Added
- Initial release
- MCP Server with 6 tools
- CLI with 8 commands
- Verilog compilation (Icarus Verilog)
- Verilog simulation (Icarus Verilog + vvp)
- Lint checking (Verilator)
- Synthesis checking (Yosys)
- Testbench generation
- VCD waveform analysis
- Skills and templates resources

[0.5.0]: https://github.com/egg-rolls/SuperRTL/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/egg-rolls/SuperRTL/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/egg-rolls/SuperRTL/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/egg-rolls/SuperRTL/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/egg-rolls/SuperRTL/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/egg-rolls/SuperRTL/releases/tag/v0.1.0
