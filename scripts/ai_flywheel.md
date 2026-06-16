# AI 数据飞轮

## 概念

让 AI Agent 作为"生产者"，使用 SuperRTL 完成一个大型 Verilog 项目。
遇到问题自动创建 GitHub Issue，团队作为"分解者"修复。
修复后 AI 继续开发，形成正向循环。

## 使用方法

### 方式一：Claude Code 直接运行

在 Claude Code 中执行：

```
请按照 scripts/projects/riscv_soc.md 的需求，设计一个 RISC-V SoC。

规则：
1. 每个模块写完后，用 superrtl compile 验证
2. 每个模块写完 testbench，用 superrtl simulate 验证
3. 遇到 superrtl 的 bug 或缺失功能时，用 gh issue create 创建 Issue
4. Issue 标题格式：[AI] <描述>
5. 每完成一个模块，在 progress.md 中记录进度
```

### 方式二：Hermes / Vessel 自动运行

配置 MCP 后，AI Agent 可以直接调用：
- `compile_verilog` — 编译
- `simulate_verilog` — 仿真
- `review_verilog` — 代码审查
- `formal_verify` — 形式验证

### 方式三：GitHub Actions 定时任务

```yaml
# .github/workflows/ai-flywheel.yml
on:
  schedule:
    - cron: '0 9 * * 1'  # 每周一早上 9 点
  workflow_dispatch:
```

## Issue 创建规则

AI 遇到以下情况时创建 Issue：

| 情况 | Issue 类型 | 标签 |
|------|-----------|------|
| superrtl compile 报错但代码正确 | Bug | `ai-bug`, `compile` |
| superrtl simulate 结果不一致 | Bug | `ai-bug`, `simulate` |
| 缺少某个 MCP tool | Feature | `ai-feature` |
| 错误信息不清晰 | Enhancement | `ai-enhancement` |
| 需要新的 Skill/Template | Feature | `ai-resource` |
| 性能问题 | Bug | `ai-performance` |

## 预期产出

- **真实 Issues**：不是人造的，是 AI 在实际开发中遇到的
- **测试覆盖**：AI 写的 testbench 就是集成测试
- **文档**：AI 的开发过程本身就是使用文档
- **边界发现**：大型项目会暴露 SuperRTL 的边界情况

## 项目建议

适合 AI 开发的 Verilog 项目（按复杂度递增）：

1. **UART 控制器** — 简单，适合冷启动
2. **SPI Master/Slave** — 中等，涉及时序
3. **I2C 控制器** — 中等，协议复杂
4. **RISC-V RV32I ALU** — 较难，组合逻辑多
5. **RISC-V SoC** — 最难，模块间交互
6. **AXI 总线互联** — 最难，协议严格
