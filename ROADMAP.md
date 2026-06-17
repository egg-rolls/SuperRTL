# SuperRTL Roadmap

## v0.3.1 — 已完成 (清理修复)

- ✅ 版本号同步 (pyproject.toml / __init__.py / CHANGELOG.md)
- ✅ 修复 waveform.py 缺失 encoding="utf-8" (Windows 兼容)
- ✅ VCD 解析逻辑去重 (提取到 utils/verilog.py)
- ✅ 移除死代码 (get_skill_raw、未使用的 --port 参数)
- ✅ 集成 logging 模块到所有工具和入口点
- ✅ 修复 INTRODUCTION.md 错误的 GitHub URL
- ✅ CHANGELOG.md 补充 0.3.1 比较链接

---

## v0.4.0 — 已完成 (验证深度提升)

### 核心功能

- ✅ 形式验证集成 (SymbiYosys BMC) — `superrtl verify` + `formal_verify` MCP tool
- ✅ 代码审查工具 — `superrtl review` + `review_verilog` MCP tool
- ✅ Testbench 增强 — 边界值测试、随机测试检查
- ✅ 新增 Skill: `verilog_formal.md` (形式验证设计模式)

### 基础设施

- ✅ CI 安装 EDA 工具 (Ubuntu)
- ✅ 共享 conftest.py fixtures
- ✅ pytest-timeout (60s 默认)
- ✅ 统一错误返回结构
- ✅ logging 集成到所有工具模块

### 测试

- ✅ 159 tests (was 139), all passing
- ✅ 新增 test_formal.py (8 tests)
- ✅ 新增 test_review.py (11 tests)
- ✅ test_testbench.py 增加 3 个新测试

---

## v0.5.0 — 已完成 (协议解码 + 远程 MCP)

### 远程 MCP 服务

- ✅ SSE 传输模式 — `superrtl mcp --transport sse`
- ✅ Streamable HTTP 传输模式 — `superrtl mcp --transport streamable-http`
- ✅ CLI 传输选项 — `--transport`, `--host`, `--port`
- ✅ `init-mcp` 支持远程配置生成

### 协议解码增强

- ✅ I2C: ACK/NACK 检测、Repeated START、状态机重构
- ✅ SPI: CS-active-high、帧间隔检测、帧持续时间
- ✅ UART: LSB-first 位组装修复、值查找逻辑、奇偶校验、帧错误检测
- ✅ 新增 28 个协议解码测试

### IP 核

- ✅ AXI-Lite Slave 模板和 Skill

---

## v0.6.0 — Q3 2026 (质量加固 + 工程改进)

> **主题：把地基打牢**

### 必须完成

#### 1. 安全与正确性修复

| 项目 | 优先级 | 说明 |
|------|--------|------|
| 修复 GitHub URL 不一致 | P0 | 统一为正确的组织名 |
| Windows 命令注入防护 | P0 | `run_command()` 参数转义 |
| 协议解码器时间戳对齐 | P0 | 用时间戳索引替代数组索引 |
| `--verbose` 标志修复 | P1 | 让 debug 日志真正输出到 console |

#### 2. 死代码清理

| 项目 | 说明 |
|------|------|
| `cleanup.py` | 整个模块未使用，删除 |
| `testbench.py` | 439 行死代码，决定：注册为 MCP 工具或删除 |
| `LogContext` | 未使用，删除 |
| `resolve_path` | 未使用，删除 |
| I2C 解码器死分支 | 修复 `state_ack_data` 后的条件判断 |

#### 3. 配置化改进

| 项目 | 说明 |
|------|------|
| 超时参数化 | compile/lint/synthesize 添加 `timeout` 参数 |
| SMT solver 可选 | formal.py 支持配置 solver engine |
| VCD 输出路径 | simulate.py 不再自动复制到 cwd |

#### 4. 错误处理改进

| 项目 | 说明 |
|------|------|
| 缩窄异常捕获 | 替换 `except Exception` 为具体异常类型 |
| YAML 配置错误提示 | project.py 解析失败时警告用户 |
| SSE/HTTP 依赖检查 | 启动时检查 starlette/uvicorn，给出安装提示 |

#### 5. 测试补全

| 项目 | 说明 |
|------|------|
| test_simulate_parallel.py | 并行仿真测试 |
| test_verify.py | verify_design 管道测试 |
| test_mcp_prompts.py | MCP prompts 列表和获取测试 |
| test_cleanup.py | 如果保留 cleanup 模块 |

#### 6. 文档更新

| 项目 | 说明 |
|------|------|
| CLAUDE.md 更新 | 测试数量、覆盖率、架构变更 |
| Dockerfile 修复 | 移除硬编码 URL，使用 setup.py 动态获取 |

### 目标指标

- 测试数量: 182 → 220+
- 代码覆盖率: → 90%
- 死代码: 0 (全部清理或激活)
- P0/P1 issue: 0

---

## v0.7.0 — Q4 2026 (波形分析增强)

> **主题：让波形分析更智能**

### 核心功能

#### 1. 协议解码扩展

| 协议 | 优先级 | 说明 |
|------|--------|------|
| AXI-Stream | 高 | TLAST/TREADY/TVALID 握手解码 |
| AXI-Lite | 高 | 读写事务解码 |
| Wishbone | 中 | 总线周期解码 |
| CAN | 低 | 帧 ID、数据、CRC |

#### 2. 时序分析

| 功能 | 说明 |
|------|------|
| Setup/Hold 检查 | 基于时钟边沿的时序验证 |
| 频率测量 | 自动检测时钟频率 |
| 传播延迟 | 信号从输入到输出的延迟 |

#### 3. 波形比较

| 功能 | 说明 |
|------|------|
| VCD Diff | 两个波形文件的差异比较 |
| 信号匹配 | 自动匹配不同命名的信号 |
| 差异高亮 | ASCII 波形中标记差异 |

#### 4. 波形覆盖率增强

| 功能 | 说明 |
|------|------|
| 翻转覆盖率 | 当前已有，增强报告格式 |
| 条件覆盖率 | 基于条件表达式的覆盖 |
| FSM 状态覆盖率 | 状态机状态访问统计 |

### MCP 工具更新

- `analyze_waveform` 扩展: 新增 `comparison` 参数
- 新增 `timing_check` 工具: setup/hold 验证
- 波形覆盖率报告格式统一

### 目标指标

- 支持协议: 3 → 7+
- 新增 MCP 工具: 1-2 个
- 测试数量: 220 → 280+

---

## v0.8.0 — Q1 2027 (IP 核库 + 生态)

> **主题：构建 RTL 设计生态**

### 核心功能

#### 1. IP 核库扩展

| IP 核 | 优先级 | 说明 |
|--------|--------|------|
| AXI-Stream | 高 | 数据流管道接口 |
| DDR Controller | 中 | 简化版，仅仿真验证 |
| Wishbone | 中 | 开源 SoC 总线 |
| APB | 低 | 低速外设总线 |

#### 2. 模块化设计工具

| 功能 | 说明 |
|------|------|
| 参数化模块库 | 可配置位宽、深度、时序参数 |
| 模块组合器 | 自动连接模块端口 |
| 接口标准化 | 基于 SystemVerilog interface |
| 依赖图可视化 | `superrtl graph` 增强为交互式 |

#### 3. Testbench 自动生成 (激活 testbench.py)

| 功能 | 说明 |
|------|------|
| 暴露为 MCP 工具 | `generate_testbench` 工具 |
| CLI 命令 | `superrtl generate-tb` |
| 语义分析 | 基于设计意图生成测试场景 |
| 自动运行 | 生成后自动仿真验证 |

#### 4. 覆盖率驱动测试

| 功能 | 说明 |
|------|------|
| 代码覆盖率 | 行覆盖率、分支覆盖率 (需 iverilog 支持) |
| 功能覆盖率 | 基于 cover 属性 |
| 覆盖率报告 | HTML 报告生成 |
| 测试优化 | 基于覆盖率缺口自动补充测试 |

### 开发者体验

| 功能 | 说明 |
|------|------|
| API 文档 | `/docs/API.md` 开发者参考 |
| 插件系统 | 自定义协议解码器、自定义检查规则 |
| 配置文件增强 | `.superrtl.yaml` 支持更多选项 |

### 目标指标

- IP 核模板: 11 → 15+
- Skills: 22 → 28+
- MCP 工具: 9 → 12+
- 测试数量: 280 → 350+

---

## 长期愿景 (2027+)

### SuperRTL v1.0 目标

1. **完整的 RTL 设计验证平台** — 从代码编写到验证的全流程覆盖
2. **AI 原生** — 所有功能通过 MCP 暴露，AI 可自主完成设计验证
3. **社区生态** — 用户贡献的 Skills、Templates、IP 核
4. **多语言支持** — SystemVerilog、VHDL (通过 GHDL)
5. **云端集成** — 远程 EDA 工具、协作验证

### 竞争定位

| 对比维度 | SuperRTL | Verilator | cocotb | HDLChecker |
|----------|----------|-----------|--------|------------|
| AI 集成 | ✅ MCP 原生 | ❌ | ❌ | ❌ |
| 一键安装 | ✅ pip install | ❌ 手动编译 | ❌ 依赖多 | ✅ |
| 协议解码 | ✅ 7+ 协议 | ❌ | ❌ | ❌ |
| 形式验证 | ✅ SymbiYosys | ❌ | ❌ | ❌ |
| 代码审查 | ✅ 内置 | ❌ | ❌ | ❌ |
| 波形分析 | ✅ Web + CLI | ❌ | ❌ | ❌ |
