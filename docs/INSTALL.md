# SuperRTL 安装指南

---

## 一、系统要求

| 项目 | 要求 |
|------|------|
| Python | 3.10+ |
| 操作系统 | Windows / macOS / Linux |

---

## 二、安装 SuperRTL

### 从源码安装

```bash
cd SuperRTL
pip install -e .
```

### 验证安装

```bash
superrtl --version
```

---

## 三、安装 EDA 工具

### Windows (使用 Scoop)

[Scoop](https://scoop.sh/) 是 Windows 下的包管理器，推荐使用。

#### 1. 安装 Scoop

```powershell
# 打开 PowerShell，执行：
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression
```

#### 2. 添加 Bucket

```powershell
# 添加主 bucket
scoop bucket add main

# 添加 extras bucket (包含更多工具)
scoop bucket add extras
```

#### 3. 安装 Verilog 工具

```powershell
# 安装 Icarus Verilog (编译仿真)
scoop install main/iverilog

# 安装 Yosys (综合检查)
scoop install main/yosys

# 安装 Verilator (Lint)
scoop install main/verilator
```

#### 4. 验证安装

```powershell
# 检查版本
iverilog -V
yosys -V
verilator --version
```

#### 5. 常见问题

**问题：scoop 找不到包**

```powershell
# 更新 scoop
scoop update

# 搜索包
scoop search iverilog
scoop search yosys
scoop search verilator
```

**问题：iverilog 安装后命令不可用**

```powershell
# 检查 PATH
echo $env:PATH

# 手动添加 PATH
scoop prefix iverilog
# 将输出的路径添加到 PATH
```

**问题：yosys 安装失败**

```powershell
# 尝试从 extras 安装
scoop install extras/yosys

# 或者从 GitHub 下载
# https://github.com/YosysHQ/yosys/releases
```

---

### macOS (使用 Homebrew)

```bash
# 安装 Homebrew (如果没有)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装工具
brew install icarus-verilog
brew install yosys
brew install verilator

# 验证
iverilog -V
yosys -V
verilator --version
```

---

### Linux (Ubuntu/Debian)

```bash
# 更新包列表
sudo apt-get update

# 安装工具
sudo apt-get install -y iverilog
sudo apt-get install -y yosys
sudo apt-get install -y verilator

# 验证
iverilog -V
yosys -V
verilator --version
```

---

## 四、安装 MCP Host (可选)

### Claude Desktop

1. 下载: https://claude.ai/download
2. 配置 MCP Server:

编辑 `~/.claude/claude_desktop_config.json`:

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

### Cursor

1. 下载: https://cursor.sh/
2. 配置 MCP Server:

创建 `.cursor/mcp.json`:

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

## 五、验证完整安装

```bash
# 1. 检查 SuperRTL
superrtl --version

# 2. 检查 EDA 工具
superrtl check-tools

# 3. 测试编译
echo 'module test(input clk, output reg [3:0] cnt); always @(posedge clk) cnt <= cnt + 1; endmodule' > test.v
superrtl compile test.v

# 4. 启动 MCP Server
superrtl mcp
```

---

## 六、卸载

### 卸载 SuperRTL

```bash
pip uninstall superrtl
```

### 卸载 EDA 工具 (Windows Scoop)

```powershell
scoop uninstall iverilog
scoop uninstall yosys
scoop uninstall verilator
```

### 卸载 EDA 工具 (macOS)

```bash
brew uninstall icarus-verilog
brew uninstall yosys
brew uninstall verilator
```

### 卸载 EDA 工具 (Linux)

```bash
sudo apt-get remove iverilog yosys verilator
```
