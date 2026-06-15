"""
Verilator Lint 工具
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import normalize_path, run_command
from ..validation import ValidationError, validate_code, validate_timeout

logger = logging.getLogger("superrtl.lint")


async def lint_verilog(code: str = None, style: str = "default", file: str = None) -> dict:
    """
    使用 Verilator 进行 Lint 检查

    Args:
        code: Verilog 源代码字符串
        style: 检查风格 (default, strict, relaxed)
        file: Verilog 文件路径（优先于 code）

    Returns:
        Lint 结果字典
    """
    start_time = time.perf_counter()
    logger.debug("lint_verilog: style=%s", style)

    try:
        # 优先从文件读取
        if file:
            p = Path(normalize_path(file))
            if not p.exists():
                return {"success": False, "error": f"文件不存在: {file}"}
            code = p.read_text(encoding="utf-8")

        # 输入验证
        if not code:
            return {"success": False, "error": "需要提供代码 (code 或 file 参数)"}
        validate_code(code, "code")
        validate_timeout(30, "lint")

        with tempfile.TemporaryDirectory() as tmpdir:
            # 写入代码文件
            design_file = Path(tmpdir) / "design.v"
            design_file.write_text(code, encoding="utf-8")

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

            logger.info(
                "lint_verilog: warnings=%d errors=%d duration=%.3fs",
                len(warnings),
                len(errors),
                duration,
            )
            return {
                "success": len(errors) == 0,
                "style": style,
                "duration": round(duration, 3),
                "warnings": warnings,
                "errors": errors,
                "warning_count": len(warnings),
                "error_count": len(errors),
            }

    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Verilator 未安装",
            "suggestion": "运行 superrtl setup 安装 EDA 工具",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Lint 检查超时 (>30s)",
            "suggestion": "检查代码是否有过大的组合逻辑",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
