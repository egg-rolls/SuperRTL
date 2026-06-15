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

## v0.5.0 — 下一版本规划

### IP 核库扩展

| IP 核 | 优先级 | 说明 |
|--------|--------|------|
| AXI-Lite Slave | 高 | 参数化寄存器接口 |
| AXI-Stream | 高 | 数据流管道接口 |
| DDR Controller | 低 | 简化版，仅仿真 |
| Wishbone | 中 | 开源 SoC 总线 |

### 波形分析增强

- 协议解码 (SPI/I2C/UART 波形自动解析)
- 时序测量 (setup/hold 检查)
- 波形比较 (diff 两个 VCD 文件)

### 模块化设计

- 参数化模块库 (可配置位宽、深度等)
- 模块组合器 (自动连接模块)
- 接口标准化 (基于 SystemVerilog interface)

### 覆盖率统计

- 代码覆盖率 (行覆盖率、分支覆盖率)
- 功能覆盖率 (基于 cover 属性)
- 覆盖率驱动的测试生成
