"""
Icarus Verilog 编译工具
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import extract_top_module, normalize_path, run_command
from ..validation import ValidationError, validate_code, validate_files_list, validate_top_module

logger = logging.getLogger("superrtl.compile")


async def compile_verilog(code: str = None, top_module: str = "", files: list[str] = None) -> dict:
    """
    编译 Verilog 代码

    支持两种调用方式：
    1. 单文件模式：传入 code 字符串
    2. 多文件模式：传入 files（文件路径列表）

    Args:
        code: 单个设计文件代码（单文件模式）
        top_module: 顶层模块名 (可选)
        files: 多个设计文件路径列表（多文件模式）

    Returns:
        编译结果字典
    """
    start_time = time.perf_counter()
    logger.debug("compile_verilog: files=%s, top_module=%s", files, top_module)

    try:
        # 输入验证
        if files:
            validate_files_list(files, "files")
        elif code:
            validate_code(code, "code")
        else:
            return {"success": False, "error": "需要提供设计文件（code 或 files 参数）"}

        if top_module:
            top_module = validate_top_module(top_module)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            source_files = []

            # 多文件模式
            if files:
                for fp in files:
                    p = Path(normalize_path(fp))
                    if not p.exists():
                        return {"success": False, "error": f"文件不存在: {fp}"}
                    dest = tmpdir_path / p.name
                    dest.write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
                    source_files.append(str(dest))

                if not top_module:
                    first_code = Path(normalize_path(files[0])).read_text(encoding="utf-8")
                    top_module = extract_top_module(first_code)

            # 单文件模式
            elif code:
                design_file = tmpdir_path / "design.v"
                design_file.write_text(code, encoding="utf-8")
                source_files.append(str(design_file))

                if not top_module:
                    top_module = extract_top_module(code)

            # 编译
            output_file = tmpdir_path / "output.vvp"
            cmd = ["iverilog", "-o", str(output_file)]
            if top_module:
                cmd.extend(["-s", top_module])
            cmd.extend(source_files)

            result = run_command(cmd, timeout=30)

            duration = time.perf_counter() - start_time

            if result.returncode == 0:
                logger.info(
                    "compile_verilog: 成功 top_module=%s duration=%.3fs", top_module, duration
                )
                return {
                    "success": True,
                    "top_module": top_module,
                    "source_files": len(source_files),
                    "duration": round(duration, 3),
                    "message": f"编译成功: {top_module}",
                }
            else:
                errors = _parse_errors(result.stderr)
                logger.warning("compile_verilog: 失败 errors=%d", len(errors))
                return {
                    "success": False,
                    "stage": "compilation",
                    "error": f"编译失败 ({len(errors)} 个错误)",
                    "top_module": top_module,
                    "source_files": len(source_files),
                    "duration": round(duration, 3),
                    "errors": errors,
                    "raw_output": result.stderr,
                }

    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Icarus Verilog 未安装",
            "suggestion": "运行 superrtl setup 安装 EDA 工具",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "编译超时 (>30s)",
            "suggestion": "检查代码是否有无限循环或过大的组合逻辑",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_errors(stderr: str) -> list[dict]:
    """解析 iverilog 错误输出"""
    import re

    errors = []

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
