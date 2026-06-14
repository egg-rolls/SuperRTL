"""
Verilator Lint 工具
"""

import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import run_command


async def lint_verilog(code: str, style: str = "default") -> dict:
    """
    使用 Verilator 进行 Lint 检查

    Args:
        code: Verilog 源代码
        style: 检查风格 (default, strict, relaxed)

    Returns:
        Lint 结果字典
    """
    start_time = time.perf_counter()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            design_file = Path(tmpdir) / "design.v"
            design_file.write_text(code)

            # 构建命令
            cmd = ["verilator", "--lint-only"]

            if style == "strict":
                cmd.extend(["-Wall", "-Wno-fatal"])
            elif style == "relaxed":
                cmd.extend(["-Wno-fatal"])

            cmd.append(str(design_file))

            # 执行
            result = run_command(cmd, timeout=30)

            duration = time.perf_counter() - start_time

            # 解析输出
            warnings = []
            errors = []

            for line in result.stderr.splitlines():
                if "Warning" in line:
                    warnings.append(line.strip())
                elif "Error" in line:
                    errors.append(line.strip())

            return {
                "success": len(errors) == 0,
                "style": style,
                "duration": round(duration, 3),
                "warnings": warnings,
                "errors": errors,
                "warning_count": len(warnings),
                "error_count": len(errors),
            }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "Verilator 未安装。请运行: superrtl setup",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Lint 检查超时 (>30s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
