# SuperRTL 安装指南

## 系统要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| 操作系统 | Windows / macOS / Linux |

---

## 安装

```bash
pip install superrtl
```

验证：

```bash
superrtl --version
```

---

## 安装 EDA 工具

```bash
superrtl setup
```

自动下载 [OSS CAD Suite](https://github.com/YosysHQ/oss-cad-suite-build)，包含：
- **Icarus Verilog** — 编译仿真
- **Yosys** — 综合检查
- **Verilator** — Lint
- **SymbiYosys** — 形式验证

首次运行约 500MB，之后无需重复下载。

---

## 系统检查

```bash
superrtl doctor
```

输出示例：

```
SuperRTL v0.5.0 系统检查

  Python:     3.12.8
  EDA 工具:   已安装
    + iverilog: Icarus Verilog (编译仿真)
    + vvp: Icarus Verilog (仿真器)
    + yosys: Yosys (综合检查)
    + verilator: Verilator (Lint)
    + sby: SymbiYosys (形式验证)

  MCP 配置:
    + Claude Desktop: 已配置 superrtl
    - Cursor (global): 未配置
```

---

## MCP 配置

### 自动配置

```bash
superrtl init-mcp               # 所有 Host
superrtl init-mcp --host cursor # 指定 Host
```

### 手动配置

**Claude Desktop** — `~/.claude/claude_desktop_config.json`：
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

**Cursor** — `.cursor/mcp.json`：
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

**Vessel / Hermes Agent**：
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

配置完成后重启 MCP Host 即可使用。

---

## 手动安装 EDA 工具

如果 `superrtl setup` 不可用，可手动安装：

```bash
# Ubuntu/Debian
sudo apt-get install iverilog yosys verilator

# macOS (Homebrew)
brew install icarus-verilog yosys verilator

# Windows (Scoop)
scoop install iverilog yosys verilator
```

---

## 卸载

```bash
superrtl uninstall              # 卸载 EDA 工具
pip uninstall superrtl          # 卸载 SuperRTL
```
