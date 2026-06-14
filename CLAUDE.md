# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SuperRTL is a Python MCP/CLI client that wraps Verilog EDA toolchains (Icarus Verilog, Yosys, Verilator) into standard MCP interfaces. It supports:
- **MCP Server mode**: Called by Claude Desktop, Cursor, Hermes Agent
- **CLI mode**: Standalone command-line usage
- **Auto-install**: EDA tools are automatically downloaded on first run
- **Project management**: `.superrtl.yaml` configuration, dependency resolution

## 能力边界

**SuperRTL 负责：** RTL 代码生成、仿真验证、项目管理
**不做：** 约束文件生成 (XDC)、Bitstream 生成、布局布线

详见 `docs/BOUNDARIES.md`

## Quick Start

```bash
# Install from PyPI
pip install superrtl

# Or using uvx (recommended)
uvx superrtl

# Install EDA tools (first time)
superrtl setup

# Initialize a project
superrtl init --name my_project --top top_module

# Build and test
superrtl build
superrtl test
```

## Common Commands

```bash
# Development setup
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=superrtl --cov-report=term-missing

# Lint & Format
ruff check src/ tests/
ruff format src/ tests/

# Build package
python -m build

# CLI usage - Project management
superrtl init                           # Initialize project config
superrtl build                          # Compile with dependency ordering
superrtl test                           # Run all testbenches
superrtl graph                          # Show module dependency graph
superrtl watch                          # Auto-compile on file changes

# CLI usage - Single file
superrtl compile design.v
superrtl simulate testbench.v design.v
superrtl lint design.v
superrtl synthesize design.v --top counter

# CLI usage - Multi-file
superrtl compile src/*.v
superrtl compile src/
superrtl simulate tb.v src/*.v

# CLI usage - Waveform
superrtl waveform analyze simulation.vcd
superrtl waveform view simulation.vcd

# CLI usage - Skills
superrtl skills list
superrtl skills show fsm

# CLI usage - Tools
superrtl setup
superrtl check-tools
superrtl mcp                            # Start MCP Server
```

## Architecture

### Core Layers

1. **Project Layer** (`src/superrtl/project.py`): Project configuration management
2. **Dependency Layer** (`src/superrtl/deps.py`): Module dependency resolution
3. **Tools Layer** (`src/superrtl/tools/`): EDA tool wrappers
4. **Resources Layer** (`src/superrtl/resources/`): MCP Resources (skills, templates)
5. **Waveform Server** (`src/superrtl/tools/waveform_server.py`): Web waveform viewer

### Key Patterns

- All EDA tool invocations use `run_command()` with automatic PATH management
- Tools are auto-detected from `.superrtl/oss-cad-suite/bin/` or system PATH
- Results are always returned as dicts with `success: bool` field
- MCP tools return `list[TextContent]` wrapping JSON-serialized results
- Multi-file support via `files` parameter (list of file paths)

## Testing

Tests use `pytest` with `pytest-asyncio`. Async tests use `asyncio_mode = "auto"`.

Current test coverage: 139 tests, ~85% coverage.

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_project.py -v

# Run with coverage
pytest tests/ --cov=superrtl --cov-report=term-missing
```

## CI/CD

CI runs on push to main/develop and PRs. Pre-push hook runs `ruff format` and `ruff check`.

```bash
# Pre-commit checks
ruff format src/ tests/
ruff check src/ tests/
pytest tests/ -v
```

## Project Conventions

- Python 3.10+ required
- Line length: 100 (ruff config)
- Chinese (中文) is used for user-facing messages
- All tool functions return dict with standardized structure
- Commit messages follow conventional commits: `feat:`, `fix:`, `docs:`, etc.
