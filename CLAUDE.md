# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperRTL is a Python MCP/CLI client that wraps Verilog EDA toolchains (Icarus Verilog, Yosys, Verilator) into standard MCP interfaces. It supports:
- **MCP Server mode**: Called by Claude Desktop, Cursor, Hermes Agent
- **CLI mode**: Standalone command-line usage
- **Auto-install**: EDA tools are automatically downloaded on first run

## Quick Start

```bash
# Install from PyPI
pip install superrtl

# Or using uvx (recommended)
uvx superrtl

# Or using pipx
pipx install superrtl

# Install EDA tools (first time)
superrtl setup

# Check tools status
superrtl check-tools
```

## Common Commands

```bash
# Development setup
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run a single test file
pytest tests/test_compile.py -v

# Run with coverage
pytest tests/ --cov=superrtl --cov-report=term-missing

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Build package
python -m build

# Version management
python scripts/bump_version.py patch  # 0.2.0 -> 0.2.1
python scripts/bump_version.py minor  # 0.2.0 -> 0.3.0
python scripts/bump_version.py major  # 0.2.0 -> 1.0.0

# CLI usage
superrtl compile design.v
superrtl simulate design.v testbench.v
superrtl lint design.v
superrtl synthesize design.v --top counter
superrtl testbench design.v
superrtl waveform simulation.vcd
superrtl mcp  # Start MCP Server
```

## Architecture

### Dual Interface Pattern

```
CLI (cli.py) ──┐
                ├──▶ tools/*.py ──▶ EDA Tools (iverilog, yosys, verilator)
MCP (server.py)─┘
```

### Core Layers

1. **Tools Layer** (`src/superrtl/tools/`): Wraps EDA tools via subprocess
   - `compile.py`: Icarus Verilog compilation
   - `simulate.py`: Icarus Verilog simulation
   - `lint.py`: Verilator lint checking
   - `synthesize.py`: Yosys synthesis
   - `testbench.py`: Auto-generates testbench
   - `waveform.py`: VCD waveform analysis

2. **Resources Layer** (`src/superrtl/resources/`): MCP Resources
   - `skills.py`: Design pattern documentation
   - `templates.py`: Code templates

3. **Runtime Layer** (`src/superrtl/runtime.py`): Manages tool paths and environment

4. **Setup Layer** (`src/superrtl/setup.py`): Downloads and installs EDA tools

5. **Utils** (`src/superrtl/utils/`): Helper functions
   - `run_command()`: Cross-platform subprocess wrapper
   - `verilog.py`: Verilog code analysis

### Key Patterns

- All EDA tool invocations use `run_command()` with automatic PATH management
- Tools are auto-detected from `.superrtl/oss-cad-suite/bin/` or system PATH
- Results are always returned as dicts with `success: bool` field
- MCP tools return `list[TextContent]` wrapping JSON-serialized results

### Dependencies

**Runtime**: mcp>=1.0.0, click>=8.0.0, rich>=13.0.0

**External EDA Tools** (auto-installed via `superrtl setup`):
- `iverilog` / `vvp`: Icarus Verilog (compile/simulate)
- `verilator`: Verilator (lint)
- `yosys`: Yosys (synthesize)

**Dev**: pytest, pytest-asyncio, pytest-cov, ruff

## Testing

Tests use `pytest` with `pytest-asyncio`. Async tests use `asyncio_mode = "auto"`. Tests that invoke EDA tools gracefully handle missing tools by checking `result["success"]`.

Current test coverage: 104 tests, ~83% coverage.

## Build System

Uses Hatch (`hatchling` build backend). Package source is in `src/superrtl/`.

```bash
# Build
python -m build

# Publish to PyPI (via GitHub Actions)
git tag v0.3.0
git push --tags
```

## Distribution

- **PyPI**: `pip install superrtl`
- **GitHub**: https://github.com/egg-rolls/SuperRTL
- **Auto-install**: `superrtl setup` downloads OSS CAD Suite

## Project Conventions

- Python 3.10+ required
- Line length: 100 (ruff config)
- Ruff lint rules: E, F, I, N, W, UP
- Chinese (中文) is used for user-facing messages
- All tool functions return dict with standardized structure
- Commit messages follow conventional commits: `feat:`, `fix:`, `docs:`, etc.

## Collaboration

- Main repository: https://github.com/egg-rolls/SuperRTL
- Team members fork and submit PRs
- See `CONTRIBUTING.md` for guidelines
- GitHub Actions CI/CD for testing and publishing
