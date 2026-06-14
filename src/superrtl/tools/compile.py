"""
Icarus Verilog 编译工具
"""

import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import extract_top_module, run_command


async def compile_verilog(code: str, top_module: str = "") -> dict:
    """
    编译 Verilog 代码

    Args:
        code: Verilog 源代码
        top_module: 顶层模块名 (可选)

    Returns:
        编译结果字典
    """
    top_module = top_module or extract_top_module(code)
    start_time = time.perf_counter()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            design_file = Path(tmpdir) / "design.v"
            design_file.write_text(code)

            # 编译
            output_file = Path(tmpdir) / "output.vvp"
            result = run_command(
                ["iverilog", "-o", str(output_file), "-s", top_module, str(design_file)], timeout=30
            )

            duration = time.perf_counter() - start_time

            if result.returncode == 0:
                return {
                    "success": True,
                    "top_module": top_module,
                    "duration": round(duration, 3),
                    "message": f"编译成功: {top_module}",
                }
            else:
                # 解析错误信息
                errors = _parse_errors(result.stderr)
                return {
                    "success": False,
                    "top_module": top_module,
                    "duration": round(duration, 3),
                    "errors": errors,
                    "raw_output": result.stderr,
                }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Icarus Verilog 未安装。请运行: superrtl setup",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "编译超时 (>30s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_errors(stderr: str) -> list[dict]:
    """解析 iverilog 错误输出"""
    import re

    errors = []

    # 匹配格式: file.v:line: error: message
    pattern = r"(.+?):(\d+):\s*(error|warning):\s*(.+)"

    for line in stderr.splitlines():
        match = re.match(pattern, line)
        if match:
            errors.append(
                {
                    "file": match.group(1),
                    "line": int(match.group(2)),
                    "level": match.group(3),
                    "message": match.group(4),
                }
            )
        elif line.strip():
            errors.append({"message": line.strip()})

    return errors
