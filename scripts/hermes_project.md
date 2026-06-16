# RISC-V SoC 项目

你是一个 Verilog 硬件工程师。请使用 SuperRTL MCP 工具完成以下项目。

## 项目目标

设计一个简单的 RISC-V RV32I SoC，包含：

1. **ALU** — 算术逻辑单元
2. **Register File** — 32x32 位寄存器堆
3. **Decoder** — 指令译码器
4. **PC** — 程序计数器
5. **Memory** — 指令/数据存储器
6. **Top** — 顶层集成

## 工作规则

1. 每个模块单独一个 .v 文件
2. 每个模块写完后，用 `compile_verilog` 验证编译
3. 每个模块写 testbench，用 `simulate_verilog` 验证功能
4. 所有文件保存到 `./riscv_soc/` 目录

## 遇到问题时

如果 SuperRTL 工具报错或行为不符合预期，**立即创建 GitHub Issue**：

```
使用 gh 命令创建 Issue：
gh issue create --repo egg-rolls/SuperRTL --title "[AI] <问题描述>" --body "..." --label "ai-generated"
```

Issue 内容必须包含：
- 问题描述
- 复现步骤（具体的 MCP 调用参数）
- 实际结果
- 期望结果
- 环境信息

## 不要停下来

遇到 SuperRTL 的问题时：
1. 创建 Issue
2. 尝试绕过（比如直接用 iverilog 命令）
3. 继续开发下一个模块
4. 不要因为工具问题而停止项目

## 进度记录

每完成一个模块，在 `./riscv_soc/progress.md` 中记录：
- 模块名称
- 编译状态
- 测试状态
- 遇到的 Issues（链接）
