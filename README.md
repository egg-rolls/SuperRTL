# SuperRTL

[![CI](https://github.com/egg-rolls/SuperRTL/actions/workflows/ci.yml/badge.svg)](https://github.com/egg-rolls/SuperRTL/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/superrtl)](https://pypi.org/project/superrtl/)
[![Python](https://img.shields.io/pypi/pyversions/superrtl)](https://pypi.org/project/superrtl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/egg-rolls/SuperRTL/branch/main/graph/badge.svg)](https://codecov.io/gh/egg-rolls/SuperRTL)

> Verilog EDA 工具链的 MCP/CLI 客户端 — 一键安装，开箱即用

## 快速开始

```bash
pip install superrtl
superrtl setup          # 自动安装 EDA 工具
superrtl compile design.v
superrtl simulate tb.v design.v
```

## 核心功能

| MCP Tool | 功能 | 依赖 |
|----------|------|------|
| `compile_verilog` | 编译 Verilog | Icarus Verilog |
| `simulate_verilog` | 仿真（支持文件路径） | Icarus Verilog |
| `simulate_parallel` | 并发仿真多个 testbench | Icarus Verilog |
| `lint_verilog` | Lint 检查 | Verilator |
| `synthesize_verilog` | 综合检查 | Yosys |
| `formal_verify` | 形式验证 (BMC) | SymbiYosys |
| `review_verilog` | 代码审查 | 内置 |
| `verify_design` | 一键综合验证 | 全部 |
| `analyze_waveform` | 波形分析 + 协议解码 | 内置 |

## MCP 集成

```json
{
  "mcpServers": {
    "superrtl": {
      "command": "superrtl",
      "args": ["mcp"]
    }
  }
}
```

支持 Claude Desktop、Cursor、Hermes Agent 等 MCP Host。

## 文档

- [完整文档](docs/README.md)
- [安装指南](docs/INSTALL.md)
- [能力边界](docs/BOUNDARIES.md)
- [发布流程](docs/RELEASE.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

## 许可证

[MIT](LICENSE)
