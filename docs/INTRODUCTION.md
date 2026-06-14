# SuperRTL 项目介绍

## 项目背景

FPGA 开发流程中，工程师面临以下挑战：

- **设计模式学习成本高**：FSM、FIFO、CDC 等设计模式需要大量经验积累
- **仿真验证效率低**：手动编写 Testbench、分析波形耗时
- **项目管理复杂**：多文件依赖关系、编译顺序需要手动维护
- **知识难以复用**：设计经验停留在个人脑中，无法标准化传递

SuperRTL 旨在通过 AI 技术降低这些门槛，让 FPGA 开发更高效。

## 项目简介

SuperRTL 是一个 AI 驱动的 Verilog EDA 工具链，提供：

- **设计知识库**：20 个经过验证的 Verilog 设计模式
- **自动化仿真**：一键编译、仿真、波形分析
- **AI 集成**：通过 MCP 协议与 AI 助手无缝协作
- **项目管理**：依赖解析、自动编译、模块依赖图

## 核心功能

### 设计知识库 (20 Skills)

| 分类 | 设计模式 |
|------|----------|
| 基础模块 | FSM、FIFO (同步/异步)、计数器、移位寄存器、译码器、多路选择器 |
| 通信接口 | SPI、I2C、UART、AXI-Lite |
| 信号处理 | FIR 滤波器、PWM 生成器、CRC 校验 |
| 可靠性设计 | CDC、复位同步器、按键消抖、边沿检测、仲裁器 |

### 代码模板 (10 Templates)

counter、register、fsm、sync_fifo、decoder、mux、shift_reg、clk_div、synchronizer、ram

### AI Prompts (6 个)

design-fsm、design-fifo、design-uart、design-cdc、review-code、generate-testbench

### 自动化仿真

- 多文件编译支持
- 依赖自动解析 (拓扑排序)
- 波形可视化查看器 (Web 界面)

### 项目管理

- `.superrtl.yaml` 项目配置
- `superrtl build` 自动依赖排序编译
- `superrtl test` 运行所有测试
- `superrtl graph` 模块依赖图
- `superrtl watch` 文件变化自动编译

## 使用方式

### 安装

```bash
pip install superrtl
superrtl setup  # 安装 EDA 工具
```

### 项目工作流

```bash
# 初始化项目
superrtl init --name my_project --top top_module

# 查看设计模式
superrtl skills show fsm
superrtl skills show spi

# 编译和测试
superrtl build
superrtl test

# 查看波形
superrtl waveform view simulation.vcd
```

### AI 集成

SuperRTL 支持 MCP 协议，可与 Claude Desktop、Cursor 等 AI 助手集成：

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

集成后 AI 助手可以：
- 调用编译、仿真、综合等工具
- 读取设计模式知识库
- 生成 Testbench
- 分析波形

## 能力边界

**SuperRTL 负责：**
- RTL 代码生成和辅助
- 仿真验证自动化
- 项目管理和依赖解析

**不负责：**
- 约束文件 (XDC) 生成
- Bitstream 生成
- 布局布线

约束文件和实现阶段由 Vivado/Quartus 等厂商工具完成。

## 技术栈

- Python 3.10+
- MCP Protocol (Model Context Protocol)
- EDA 工具：Icarus Verilog、Yosys、Verilator
- Web 波形查看器：Canvas + HTTP Server

## 开源信息

- 仓库：github.com/egg-rolls/SuperRTL
- 许可：MIT
- 安装：`pip install superrtl`
