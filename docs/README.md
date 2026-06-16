# SuperRTL

> Verilog EDA 工具链的 MCP/CLI 客户端 — `pip install` 即用

---

## 概述

**SuperRTL** 将 Verilog EDA 工具链封装为标准 MCP 接口：

- **pip 安装即用** — `pip install superrtl`，无需编译、无需 gateway
- **MCP 零配置** — Host 自动拉起子进程，无需后台服务
- **CLI 独立使用** — 不依赖 MCP Host 也能用
- **EDA 工具自动管理** — `superrtl setup` 一键下载

---

## 快速开始

```bash
pip install superrtl        # 1. 安装
superrtl setup              # 2. 下载 EDA 工具（一次性）
superrtl compile design.v   # 3. 开始使用
```

### 系统检查

```bash
superrtl doctor             # 检查 Python / EDA 工具 / MCP 配置状态
```

### MCP 配置

```bash
superrtl init-mcp           # 自动生成 MCP 配置（Claude Desktop / Cursor）
superrtl init-mcp --host vessel  # 为 Vessel 生成配置片段
```

或手动配置：

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

支持 Claude Desktop、Cursor、Vessel、Hermes Agent 等 MCP Host。

---

## MCP Tools (9 个)

| Tool | CLI 命令 | 功能 | 依赖 |
|------|----------|------|------|
| `compile_verilog` | `superrtl compile` | 编译 (支持多文件/目录/glob) | Icarus Verilog |
| `simulate_verilog` | `superrtl simulate` | 仿真 (支持文件路径) | Icarus Verilog |
| `simulate_parallel` | — | 并发仿真多个 testbench | Icarus Verilog |
| `lint_verilog` | `superrtl lint` | Lint 检查 (支持文件路径) | Verilator |
| `synthesize_verilog` | `superrtl synthesize` | 综合检查 (支持文件路径) | Yosys |
| `formal_verify` | `superrtl formal` | 形式验证 BMC (支持文件路径) | SymbiYosys |
| `review_verilog` | `superrtl review` | 代码审查 (支持文件路径) | 内置 |
| `verify_design` | `superrtl verify` | 一键综合验证 (compile+simulate+lint+review) | 全部 |
| `analyze_waveform` | `superrtl waveform` | 波形分析 + 协议解码 (SPI/I2C/UART) | 内置 |

> **推荐工作流**：AI 自行编写 `testbench.v`，通过 `simulate_verilog(testbench_file=..., design_file_paths=...)` 运行，根据错误信息迭代修复。

### MCP Resources

| Resource | 功能 |
|----------|------|
| `skills://{name}` | 设计模式文档 (22 个) |
| `templates://{name}` | 代码模板 (11 个) |

### MCP Prompts

| Prompt | 功能 |
|--------|------|
| `design-fsm` | FSM 设计助手 |
| `design-fifo` | FIFO 设计助手 |
| `design-uart` | UART 设计助手 |
| `design-cdc` | CDC 设计助手 |
| `review-code` | 代码审查助手 |
| `generate-testbench` | Testbench 编写指导 |

---

## CLI 命令

### 系统管理

| 命令 | 说明 |
|------|------|
| `superrtl setup` | 安装 EDA 工具（自动下载） |
| `superrtl check-tools` | 检查 EDA 工具状态 |
| `superrtl doctor` | 系统健康检查 |
| `superrtl init-mcp` | 生成 MCP 配置 |
| `superrtl uninstall` | 卸载 EDA 工具 |

### 项目管理

| 命令 | 说明 |
|------|------|
| `superrtl init` | 初始化项目配置 (.superrtl.yaml) |
| `superrtl build` | 根据配置编译 (自动依赖排序) |
| `superrtl test` | 运行所有测试平台 |
| `superrtl graph` | 显示模块依赖图 |
| `superrtl watch` | 监视文件变化，自动编译 |

### 工具命令

| 命令 | 说明 |
|------|------|
| `superrtl compile <files...>` | 编译 (支持 glob/目录) |
| `superrtl simulate <tb> <designs...>` | 仿真 |
| `superrtl lint <file>` | Lint 检查 |
| `superrtl synthesize <file>` | 综合检查 |
| `superrtl formal <file>` | 形式验证 |
| `superrtl review <file>` | 代码审查 |
| `superrtl verify <designs...> --tb <file>` | 一键综合验证 |
| `superrtl waveform analyze <file>` | 波形分析 |
| `superrtl waveform view <file>` | 波形查看器 |

---

## 安装 EDA 工具

**方式一：自动安装（推荐）**

```bash
superrtl setup
```

自动下载 [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)（含 iverilog, yosys, verilator, sby）。

**方式二：手动安装**

```bash
# Ubuntu/Debian
sudo apt-get install iverilog yosys verilator

# macOS
brew install icarus-verilog yosys verilator

# Windows (Scoop)
scoop install iverilog yosys verilator
```

---

## MCP 调用示例

**编译**（文件路径）：
```json
{"name": "compile_verilog", "arguments": {"files": ["./src/counter.v"]}}
```

**仿真**（文件路径 — 推荐）：
```json
{"name": "simulate_verilog", "arguments": {"design_file_paths": ["./src/counter.v"], "testbench_file": "./tb/counter_tb.v"}}
```

**代码审查**（文件路径）：
```json
{"name": "review_verilog", "arguments": {"file": "./src/counter.v"}}
```

**综合验证**（一键）：
```json
{"name": "verify_design", "arguments": {"design_files": ["./src/counter.v"], "testbench_file": "./tb/counter_tb.v"}}
```

**波形协议解码**：
```json
{"name": "analyze_waveform", "arguments": {"vcd_file": "./sim.vcd", "protocol": "spi"}}
```

---

## 技术栈

| 组件 | 选型 | 版本 |
|------|------|------|
| 语言 | Python | 3.10+ |
| MCP 协议 | mcp | >=1.0.0 |
| CLI 框架 | click | >=8.0.0 |
| 终端美化 | rich | >=13.0.0 |
| EDA 工具 | OSS CAD Suite | 2026.06 |

---

## 许可证

[MIT](../LICENSE)

---

## 致谢

- [Icarus Verilog](https://github.com/steveicarus/iverilog)
- [Yosys](https://github.com/YosysHQ/yosys)
- [Verilator](https://github.com/verilator/verilator)
- [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)
