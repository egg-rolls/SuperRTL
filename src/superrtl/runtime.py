"""
运行时环境管理

管理 EDA 工具的路径和环境变量
"""

import os
import sys
from pathlib import Path


def get_project_root() -> Path:
    """获取项目根目录（当前工作目录）"""
    return Path.cwd()


def get_tools_dir() -> Path:
    """获取工具安装目录"""
    return get_project_root() / ".superrtl"


def get_oss_cad_suite_dir() -> Path:
    """获取 OSS CAD Suite 目录"""
    return get_tools_dir() / "oss-cad-suite"


def get_tools_bin_dir() -> Path:
    """获取工具 bin 目录"""
    return get_oss_cad_suite_dir() / "bin"


def get_tool_path(tool_name: str) -> str:
    """
    获取工具的完整路径

    优先使用本地安装的工具，回退到系统 PATH

    Args:
        tool_name: 工具名称 (如 iverilog, yosys, verilator)

    Returns:
        工具的完整路径或工具名（回退到系统 PATH）
    """
    bin_dir = get_tools_bin_dir()

    if sys.platform == "win32":
        tool_path = bin_dir / f"{tool_name}.exe"
    else:
        tool_path = bin_dir / tool_name

    if tool_path.exists():
        return str(tool_path)

    # 回退到系统 PATH
    return tool_name


def get_environ() -> dict:
    """
    获取包含工具路径的环境变量

    将本地工具目录添加到 PATH 最前面
    """
    env = os.environ.copy()

    # 添加 bin 和 lib 目录到 PATH
    oss_dir = get_oss_cad_suite_dir()
    dirs_to_add = [
        str(oss_dir / "bin"),
        str(oss_dir / "lib"),
    ]

    current_path = env.get("PATH", "")
    for d in dirs_to_add:
        if d not in current_path:
            current_path = d + os.pathsep + current_path

    env["PATH"] = current_path

    return env


def tools_installed() -> bool:
    """检查工具是否已安装"""
    bin_dir = get_tools_bin_dir()

    if sys.platform == "win32":
        return (bin_dir / "iverilog.exe").exists()
    else:
        return (bin_dir / "iverilog").exists()


def get_tools_status() -> dict:
    """获取工具安装状态"""
    tools = {
        "iverilog": "Icarus Verilog (编译仿真)",
        "vvp": "Icarus Verilog (仿真器)",
        "yosys": "Yosys (综合检查)",
        "verilator": "Verilator (Lint)",
        "sby": "SymbiYosys (形式验证)",
    }

    status = {}
    bin_dir = get_tools_bin_dir()

    for tool, desc in tools.items():
        if sys.platform == "win32":
            tool_path = bin_dir / f"{tool}.exe"
        else:
            tool_path = bin_dir / tool

        status[tool] = {
            "name": desc,
            "installed": tool_path.exists(),
            "path": str(tool_path) if tool_path.exists() else None,
        }

    return status
