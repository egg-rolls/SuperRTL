"""
输入验证模块

提供统一的输入验证、大小限制和安全检查。
"""

from pathlib import Path

# 限制常量
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_CODE_LENGTH = 1_000_000  # 1M 字符
MAX_FILES_COUNT = 100  # 最大文件数
ALLOWED_EXTENSIONS = {".v", ".sv", ".vh", ".svh"}


class ValidationError(Exception):
    """验证错误"""

    def __init__(self, message: str, suggestion: str = ""):
        self.message = message
        self.suggestion = suggestion
        super().__init__(message)


def validate_code(code: str, name: str = "code") -> str:
    """验证代码字符串

    Args:
        code: 代码内容
        name: 参数名（用于错误信息）

    Returns:
        验证后的代码

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(code, str):
        raise ValidationError(f"{name} 必须是字符串", f"检查传入的 {name} 参数类型")

    if len(code) == 0:
        raise ValidationError(f"{name} 不能为空", f"确保 {name} 包含有效的 Verilog 代码")

    if len(code) > MAX_CODE_LENGTH:
        raise ValidationError(
            f"{name} 过大 ({len(code)} 字符，最大 {MAX_CODE_LENGTH})", "考虑将代码拆分为多个文件"
        )

    return code


def validate_file_path(filepath: str, must_exist: bool = True) -> Path:
    """验证文件路径

    Args:
        filepath: 文件路径
        must_exist: 是否必须存在

    Returns:
        验证后的 Path 对象

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(filepath, str):
        raise ValidationError("文件路径必须是字符串", "检查传入的文件路径参数")

    path = Path(filepath)

    # 检查路径遍历攻击
    try:
        path.resolve()
    except Exception:
        raise ValidationError(f"无效的文件路径: {filepath}", "检查路径是否包含非法字符")

    if must_exist and not path.exists():
        raise ValidationError(
            f"文件不存在: {filepath}", "检查文件路径是否正确，或运行 superrtl setup 安装工具"
        )

    if must_exist and path.is_dir():
        raise ValidationError(f"路径是目录而非文件: {filepath}", "指定具体的文件路径")

    if must_exist:
        size = path.stat().st_size
        if size > MAX_FILE_SIZE:
            raise ValidationError(
                f"文件过大 ({size / 1024 / 1024:.1f}MB，最大 {MAX_FILE_SIZE / 1024 / 1024}MB)",
                "考虑将大文件拆分为多个小文件",
            )

    return path


def validate_verilog_file(filepath: str) -> Path:
    """验证 Verilog 文件

    Args:
        filepath: 文件路径

    Returns:
        验证后的 Path 对象

    Raises:
        ValidationError: 验证失败
    """
    path = validate_file_path(filepath, must_exist=True)

    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"不支持的文件类型: {path.suffix}", f"支持的文件类型: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    return path


def validate_files_list(files: list, name: str = "files") -> list[str]:
    """验证文件列表

    Args:
        files: 文件路径列表
        name: 参数名

    Returns:
        验证后的文件列表

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(files, list):
        raise ValidationError(f"{name} 必须是列表", f"检查传入的 {name} 参数类型")

    if len(files) == 0:
        raise ValidationError(f"{name} 不能为空", f"确保 {name} 包含至少一个文件路径")

    if len(files) > MAX_FILES_COUNT:
        raise ValidationError(
            f"{name} 文件数过多 ({len(files)}，最大 {MAX_FILES_COUNT})",
            "考虑使用 glob 模式或目录模式",
        )

    return files


def validate_timeout(timeout: int, tool: str = "default") -> int:
    """验证超时时间

    Args:
        timeout: 超时秒数
        tool: 工具名

    Returns:
        验证后的超时时间

    Raises:
        ValidationError: 验证失败
    """
    if not isinstance(timeout, (int, float)):
        raise ValidationError("超时时间必须是数字", "检查 timeout 参数")

    if timeout < 1:
        raise ValidationError("超时时间不能小于 1 秒", "设置合理的超时时间")

    # 工具特定上限
    max_timeouts = {
        "compile": 60,
        "simulate": 300,
        "lint": 60,
        "synthesize": 300,
        "default": 300,
    }
    max_timeout = max_timeouts.get(tool, max_timeouts["default"])

    if timeout > max_timeout:
        raise ValidationError(
            f"超时时间过长 ({timeout}s，{tool} 最大 {max_timeout}s)",
            f"考虑优化代码或增加 {tool} 的效率",
        )

    return int(timeout)


def validate_top_module(top: str) -> str:
    """验证顶层模块名

    Args:
        top: 模块名

    Returns:
        验证后的模块名
    """
    if not top:
        return ""

    if not isinstance(top, str):
        raise ValidationError("顶层模块名必须是字符串", "检查 top_module 参数")

    # 检查 Verilog 标识符格式
    import re

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", top):
        raise ValidationError(
            f"无效的模块名: {top}", "模块名必须是有效的 Verilog 标识符 (字母/数字/下划线)"
        )

    return top


def validate_target(target: str) -> str:
    """验证综合目标

    Args:
        target: 目标平台

    Returns:
        验证后的目标
    """
    valid_targets = {"generic", "xilinx", "ice40"}

    if target not in valid_targets:
        raise ValidationError(f"不支持的目标: {target}", f"支持的目标: {', '.join(valid_targets)}")

    return target
