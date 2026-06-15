"""
工具函数
"""

import subprocess
import sys

from .verilog import extract_ports, extract_top_module, parse_vcd

__all__ = [
    "extract_top_module",
    "extract_ports",
    "parse_vcd",
    "run_command",
]


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
    # 导入 runtime 模块获取工具路径和环境变量
    from ..runtime import get_environ, get_tool_path

    # 获取工具的完整路径
    tool_name = cmd[0]
    cmd = list(cmd)  # 避免修改原始列表
    cmd[0] = get_tool_path(tool_name)

    # 获取包含工具路径的环境变量
    env = get_environ()

    if sys.platform == "win32":
        # Windows 上使用 cmd.exe 包装以解决 DLL 依赖问题
        cmd_str = " ".join(str(c) for c in cmd)
        return subprocess.run(
            ["cmd.exe", "/c", cmd_str], capture_output=True, text=True, env=env, **kwargs
        )
    else:
        # Linux/macOS 直接运行
        return subprocess.run(cmd, capture_output=True, text=True, env=env, **kwargs)
