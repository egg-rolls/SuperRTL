# SuperRTL

> Verilog EDA 工具的 MCP/CLI 客户端

---

## 概述

**SuperRTL** 将 Verilog EDA 工具链封装为标准 MCP 接口，支持：

- **MCP Server 模式**：被 Claude Desktop、Cursor、Hermes Agent 等调用
- **CLI 命令行模式**：独立使用，无需 MCP Host
- **自动安装工具**：首次运行时自动下载 EDA 工具，无需手动配置

---

## 核心功能

### 项目管理

| 命令 | 功能 |
|------|------|
| `superrtl init` | 初始化项目配置 (.superrtl.yaml) |
| `superrtl build` | 根据配置编译 (自动依赖排序) |
| `superrtl test` | 运行所有测试平台 |
| `superrtl graph` | 显示模块依赖图 |
| `superrtl watch` | 监视文件变化，自动编译 |

### MCP Tools

| Tool | 命令 | 功能 | 依赖 |
|------|------|------|------|
| `compile_verilog` | `superrtl compile` | 编译 (支持多文件) | Icarus Verilog |
| `simulate_verilog` | `superrtl simulate` | 仿真 (支持文件路径) | Icarus Verilog |
| `lint_verilog` | `superrtl lint` | Lint 检查 | Verilator |
| `synthesize_verilog` | `superrtl synthesize` | 综合检查 | Yosys |
| `formal_verify` | `superrtl verify` | 形式验证 (BMC) | SymbiYosys |
| `review_verilog` | `superrtl review` | 代码审查 | 内置 |
| `generate_testbench` | `superrtl testbench` | 生成测试平台骨架 (可选) | 内置 |
| `analyze_waveform` | `superrtl waveform` | 波形分析/查看 | 内置 |

> **推荐工作流**：AI 自行生成 `design.v` 和 `testbench.v` 文件，通过文件路径调用 `simulate_verilog` 运行仿真，根据返回的错误信息迭代修复。

### MCP Resources

| Resource | 功能 |
|----------|------|
| `skills://{name}` | 设计模式文档 (20 个) |
| `templates://{name}` | 代码模板 (10 个) |

### MCP Prompts

| Prompt | 功能 |
|--------|------|
| `design-fsm` | FSM 设计助手 |
| `design-fifo` | FIFO 设计助手 |
| `design-uart` | UART 设计助手 |
| `design-cdc` | CDC 设计助手 |
| `review-code` | 代码审查助手 |
| `generate-testbench` | Testbench 生成助手 |

---

## 快速开始

### 安装 SuperRTL

```bash
# 从源码安装
cd SuperRTL
pip install -e .

# 或从 PyPI (发布后)
pip install superrtl
```

### 安装 EDA 工具

**方式一：自动安装（推荐）**

```bash
# 自动下载并安装 EDA 工具
superrtl setup
```

这会自动下载 [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build) 并安装到项目目录 `.superrtl/`。

**方式二：手动安装**

```bash
# Ubuntu/Debian
sudo apt-get install iverilog yosys verilator

# macOS
brew install icarus-verilog yosys verilator

# Windows (Scoop)
scoop install iverilog yosys verilator
```

### 验证安装

```bash
# 检查工具状态
superrtl check-tools
```

输出示例：
```
EDA 工具状态

  + iverilog: Icarus Verilog (编译仿真)
  + vvp: Icarus Verilog (仿真器)
  + yosys: Yosys (综合检查)
  + verilator: Verilator (Lint)

所有工具已安装
```

### 使用 CLI - 项目模式

```bash
# 初始化项目
superrtl init --name my_project --top top_module

# 编译 (自动依赖排序)
superrtl build

# 运行所有测试
superrtl test

# 查看模块依赖图
superrtl graph

# 监视文件变化
superrtl watch
```

### 使用 CLI - 单文件模式

```bash
# 编译
superrtl compile design.v

# 仿真
superrtl simulate testbench.v design.v

# Lint
superrtl lint design.v

# 综合
superrtl synthesize design.v --top counter

# 生成 Testbench
superrtl testbench design.v

# 波形分析
superrtl waveform analyze simulation.vcd

# 波形查看器
superrtl waveform view simulation.vcd
```

### 使用 CLI - 多文件模式

```bash
# 多文件编译
superrtl compile src/*.v
superrtl compile src/

# 多文件仿真
superrtl simulate tb.v src/*.v
superrtl simulate tb.v alu.v counter.v
```

### 使用 MCP Server

```bash
# 启动 MCP Server (stdio 模式)
superrtl mcp
```

### 配置 MCP Host

**Claude Desktop** (`~/.claude/claude_desktop_config.json`):
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

**Cursor** (`.cursor/mcp.json`):
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

**Hermes Agent**:
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

---

## Docker 支持

### 构建镜像

```bash
# 构建 Docker 镜像
docker build -t superrtl .
```

### 使用 Docker

```bash
# 启动 MCP Server
docker run -it superrtl

# 挂载目录使用 CLI
docker run -v $(pwd):/workspace -it superrtl compile /workspace/design.v

# 交互式使用
docker run -it -v $(pwd):/workspace superrtl bash
```

---

## CLI 命令

| 命令 | 说明 |
|------|------|
| `superrtl setup` | 安装 EDA 工具 |
| `superrtl check-tools` | 检查工具状态 |
| `superrtl compile <file>` | 编译 Verilog 代码 |
| `superrtl simulate <testbench> <designs...>` | 运行仿真 |
| `superrtl lint <file>` | Lint 检查 |
| `superrtl synthesize <file>` | 综合检查 |
| `superrtl verify <file>` | 形式验证 (SymbiYosys BMC) |
| `superrtl review <file>` | 代码审查 |
| `superrtl testbench <file>` | 生成 Testbench 骨架 |
| `superrtl waveform <file>` | 分析波形 |
| `superrtl mcp` | 启动 MCP Server |
| `superrtl uninstall` | 卸载 EDA 工具 |

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

## 项目结构

```
SuperRTL/
├── src/superrtl/
│   ├── __init__.py
│   ├── server.py              # MCP Server 主入口
│   ├── cli.py                 # CLI 入口
│   ├── setup.py               # EDA 工具安装管理
│   ├── runtime.py             # 运行时环境管理
│   ├── validation.py          # 输入验证
│   ├── deps.py                # 模块依赖解析
│   ├── project.py             # 项目配置管理
│   ├── logging.py             # 日志系统
│   │
│   ├── tools/                 # MCP Tools
│   │   ├── compile.py         # Icarus Verilog 编译
│   │   ├── simulate.py        # Icarus Verilog 仿真
│   │   ├── lint.py            # Verilator Lint
│   │   ├── synthesize.py      # Yosys 综合检查
│   │   ├── formal.py          # SymbiYosys 形式验证
│   │   ├── review.py          # 代码审查
│   │   ├── testbench.py       # Testbench 生成骨架
│   │   ├── waveform.py        # VCD 波形分析
│   │   └── waveform_server.py # Web 波形查看器
│   │
│   ├── resources/             # MCP Resources
│   │   ├── skills.py
│   │   └── templates.py
│   │
│   └── utils/
│       ├── __init__.py        # run_command
│       └── verilog.py         # Verilog 解析 + VCD 解析
│
├── shared/                    # 共享资源
│   ├── skills/                # 设计模式文档 (21 个)
│   ├── templates/             # 代码模板 (10 个)
│   └── waveform/              # 波形查看器 HTML
│
├── .superrtl/                 # EDA 工具安装目录（自动生成）
│   └── oss-cad-suite/
│       ├── bin/               # iverilog, yosys, verilator, sby
│       └── lib/
│
├── Dockerfile                 # Docker 镜像
├── tests/                     # 测试 (159 tests)
├── examples/
└── pyproject.toml
```

---

## 工作原理

### 自动安装

1. 运行 `superrtl setup`
2. 检测操作系统和架构
3. 从 GitHub 下载对应的 OSS CAD Suite
4. 解压到 `.superrtl/oss-cad-suite/`
5. 运行时自动添加到 PATH

### 运行时

1. 工具调用时自动检测本地安装
2. 优先使用 `.superrtl/oss-cad-suite/bin/` 中的工具
3. 回退到系统 PATH
4. 自动处理 Windows DLL 依赖问题

---

## 示例

### CLI 示例

```bash
# 编译并仿真
$ superrtl compile counter.v
[OK] 编译成功: counter
   耗时: 0.058s

$ superrtl simulate counter.v counter_tb.v
[OK] 仿真通过
   耗时: 0.456s
   输出: PASS
```

### MCP 调用示例

**编译**（传入代码字符串）：
```json
{
  "name": "compile_verilog",
  "arguments": {
    "code": "module counter(input clk, input rst_n, output reg [3:0] count); ...",
    "top_module": "counter"
  }
}
```

**仿真**（传入文件路径 — 推荐方式）：
```json
{
  "name": "simulate_verilog",
  "arguments": {
    "design_file_paths": ["./src/counter.v"],
    "testbench_file": "./tb/counter_tb.v",
    "timeout": 30
  }
}
```

**仿真**（传入代码字符串）：
```json
{
  "name": "simulate_verilog",
  "arguments": {
    "code": "module counter(...); ...",
    "testbench": "module tb; ... initial $display(\"PASS\"); ...",
    "timeout": 30
  }
}
```

**返回结构**：
```json
{
  "success": true,
  "passed": true,
  "stage": "simulation",
  "duration": 0.456,
  "output": "PASS\n",
  "vcd_file": "simulation.vcd"
}
```

---

## 许可证

MIT License

---

## 致谢

- [Icarus Verilog](https://github.com/steveicarus/iverilog)
- [Yosys](https://github.com/YosysHQ/yosys)
- [Verilator](https://github.com/verilator/verilator)
- [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)
