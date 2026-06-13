# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperRTL is a Python MCP/CLI client that wraps Verilog EDA toolchains (Icarus Verilog, Yosys, Verilator) into standard MCP interfaces. It supports two modes:
- **MCP Server mode**: Called by Claude Desktop, Cursor, Hermes Agent
- **CLI mode**: Standalone command-line usage

## Common Commands

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Install EDA tools (first time)
superrtl setup

# Run tests
pytest

# Run a single test file
pytest tests/test_compile.py

# Run with coverage
pytest --cov=superrtl

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Check EDA tools installation
superrtl check-tools

# Start MCP Server
superrtl mcp

# CLI usage examples
superrtl compile design.v
superrtl simulate design.v testbench.v
superrtl lint design.v
superrtl synthesize design.v --top counter
```

## Architecture

### Dual Interface Pattern

The codebase follows a dual interface pattern where the same core logic serves both MCP and CLI:

```
CLI (cli.py) ──┐
                ├──▶ tools/*.py ──▶ EDA Tools (iverilog, yosys, verilator)
MCP (server.py)─┘
```

- **`src/superrtl/cli.py`**: Click-based CLI entry point (`superrtl` command)
- **`src/superrtl/server.py`**: MCP Server using `mcp` library, registers tools and resources

### Core Layers

1. **Tools Layer** (`src/superrtl/tools/`): Each tool wraps an EDA tool via subprocess
   - `compile.py`: Icarus Verilog compilation
   - `simulate.py`: Icarus Verilog simulation (calls compile first)
   - `lint.py`: Verilator lint checking
   - `synthesize.py`: Yosys synthesis
   - `testbench.py`: Auto-generates testbench from Verilog code
   - `waveform.py`: VCD waveform analysis

2. **Resources Layer** (`src/superrtl/resources/`): MCP Resources
   - `skills.py`: Design pattern documentation (from `shared/skills/`)
   - `templates.py`: Code templates (from `shared/templates/`)

3. **Utils** (`src/superrtl/utils/verilog.py`): Verilog code analysis helpers (`extract_top_module`, `extract_ports`)

4. **Shared Resources** (`shared/`): Design skills and code templates
   - `skills/`: Markdown files with Verilog design patterns
   - `templates/`: Verilog code templates

### Key Patterns

- All EDA tool invocations use `subprocess.run()` with `tempfile.TemporaryDirectory()` for isolation
- Tool functions are `async` but use synchronous subprocess calls internally
- Results are always returned as dicts with `success: bool` field
- MCP tools return `list[TextContent]` wrapping JSON-serialized results
- CLI commands use `asyncio.run()` to call the async tool functions

### Dependencies

**Runtime**: mcp>=1.0.0, click>=8.0.0, rich>=13.0.0

**External EDA Tools** (auto-installed via `superrtl setup`):
- `iverilog` / `vvp`: Icarus Verilog (compile/simulate)
- `verilator`: Verilator (lint)
- `yosys`: Yosys (synthesize)

**Dev**: pytest, pytest-asyncio, pytest-cov, ruff

## Testing

Tests use `pytest` with `pytest-asyncio`. Async tests require the `@pytest.mark.asyncio` decorator (though `asyncio_mode = "auto"` is configured). Tests that invoke EDA tools will gracefully handle missing tools by checking `result["success"]`.

## Build System

Uses Hatch (`hatchling` build backend). Package source is in `src/superrtl/`.

```bash
# Build wheel
hatch build

# Publish (when ready)
hatch publish
```

## Project Conventions

- Python 3.10+ required (uses `list[str]` syntax, not `List[str]`)
- Line length: 100 (ruff config)
- Ruff lint rules: E, F, I, N, W, UP
- Chinese (中文) is used for user-facing messages and documentation
- All tool functions return dict with standardized structure (`success`, `duration`, `errors`, etc.)
