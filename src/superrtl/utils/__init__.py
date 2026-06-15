"""
工具函数
"""

import re
import subprocess
import sys
from pathlib import Path

from .verilog import extract_ports, extract_top_module, parse_vcd

__all__ = [
    "extract_top_module",
    "extract_ports",
    "normalize_path",
    "parse_vcd",
    "run_command",
]


def normalize_path(path_str: str) -> str:
    """路径归一化：POSIX 风格 → Windows 风格

    处理 /d/code/... → D:\\code\\... 等 Git Bash 风格路径。

    Args:
        path_str: 原始路径字符串

    Returns:
        归一化后的路径字符串
    """
    if sys.platform != "win32":
        return path_str

    # /d/code/... → D:\code\...
    match = re.match(r"^/([a-zA-Z])/(.*)$", path_str)
    if match:
        drive = match.group(1).upper()
        rest = match.group(2).replace("/", "\\")
        return f"{drive}:\\{rest}"

    return path_str


def resolve_path(path_str: str) -> Path:
    """解析并归一化路径

    Args:
        path_str: 路径字符串（支持 POSIX 和 Windows 格式）

    Returns:
        解析后的 Path 对象
    """
    return Path(normalize_path(path_str))


def run_command(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """
    跨平台运行命令

    自动使用本地安装的 EDA 工具，回退到系统 PATH

    Args:
        cmd: 命令列表，第一个元素为工具名
        **kwargs: 传递给 subprocess.run 的参数

    Returns:
        subprocess.CompletedProcess 对象
    """
    import tempfile

    # 导入 runtime 模块获取工具路径和环境变量
    from ..runtime import get_environ, get_tool_path

    # 获取工具的完整路径
    tool_name = cmd[0]
    cmd = list(cmd)  # 避免修改原始列表
    cmd[0] = get_tool_path(tool_name)

    # 获取包含工具路径的环境变量
    env = get_environ()

    # 确保 TEMP/TMPDIR 指向系统临时目录（避免 .hermes-tmp 等非标准目录权限问题）
    sys_tmp = tempfile.gettempdir()
    if sys.platform == "win32":
        env["TEMP"] = sys_tmp
        env["TMP"] = sys_tmp
    else:
        env["TMPDIR"] = sys_tmp

    if sys.platform == "win32":
        # Windows 上使用 cmd.exe 包装以解决 DLL 依赖问题
        cmd_str = " ".join(str(c) for c in cmd)
        return subprocess.run(
            ["cmd.exe", "/c", cmd_str], capture_output=True, text=True, env=env, **kwargs
        )
    else:
        # Linux/macOS 直接运行
        return subprocess.run(cmd, capture_output=True, text=True, env=env, **kwargs)
