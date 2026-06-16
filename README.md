# SuperRTL

[![CI](https://github.com/egg-rolls/SuperRTL/actions/workflows/ci.yml/badge.svg)](https://github.com/egg-rolls/SuperRTL/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/superrtl)](https://pypi.org/project/superrtl/)
[![Python](https://img.shields.io/pypi/pyversions/superrtl)](https://pypi.org/project/superrtl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![codecov](https://codecov.io/gh/egg-rolls/SuperRTL/branch/main/graph/badge.svg)](https://codecov.io/gh/egg-rolls/SuperRTL)

> Verilog EDA 工具链的 MCP/CLI 客户端 — `pip install` 即用

## 30 秒上手

```bash
pip install superrtl        # 安装
superrtl setup              # 下载 EDA 工具（一次性）
superrtl compile design.v   # 开始使用
```

MCP 零配置启动 — Host（Vessel/Claude Desktop/Cursor）自动拉起 `superrtl mcp` 子进程，无需后台服务。

## MCP Tools (9 个)

| Tool | 功能 | 依赖 |
|------|------|------|
| `compile_verilog` | 编译 Verilog | Icarus Verilog |
| `simulate_verilog` | 仿真（支持文件路径） | Icarus Verilog |
| `simulate_parallel` | 并发仿真多个 testbench | Icarus Verilog |
| `lint_verilog` | Lint 检查 | Verilator |
| `synthesize_verilog` | 综合检查 | Yosys |
| `formal_verify` | 形式验证 (BMC) | SymbiYosys |
| `review_verilog` | 代码审查（5 类检查） | 内置 |
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

或使用配置向导：`superrtl init-mcp`

## 诊断

```bash
superrtl doctor             # 系统健康检查
superrtl check-tools        # EDA 工具状态
superrtl init-mcp           # 生成 MCP 配置
```

## 文档

- [完整文档](docs/README.md)
- [安装指南](docs/INSTALL.md)
- [能力边界](docs/BOUNDARIES.md)
- [发布流程](docs/RELEASE.md)
- [贡献指南](CONTRIBUTING.md)
- [更新日志](CHANGELOG.md)

## 许可证

[MIT](LICENSE)
