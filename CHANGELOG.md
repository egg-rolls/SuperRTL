# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- GitHub Actions CI/CD pipeline
- PyPI publishing workflow

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

[Unreleased]: https://github.com/RTL-Agent/SuperRTL/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/RTL-Agent/SuperRTL/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/RTL-Agent/SuperRTL/releases/tag/v0.1.0
