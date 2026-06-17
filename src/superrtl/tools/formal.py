"""
SymbiYosys 形式验证工具
"""

import logging
import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import extract_top_module, normalize_path, run_command
from ..validation import ValidationError, validate_code, validate_timeout, validate_top_module

logger = logging.getLogger("superrtl.formal")


async def formal_verify(
    code: str = None,
    top_module: str = "",
    properties: list[str] = None,
    timeout: int = 300,
    depth: int = 20,
    file: str = None,
    solver: str = "yices",
) -> dict:
    """
    使用 SymbiYosys 进行形式验证

    Args:
        code: Verilog 源代码（需包含 assert/assume/cover 语句）
        top_module: 顶层模块名 (可选)
        properties: 要验证的属性名列表 (可选，验证全部)
        timeout: 验证超时时间 (秒)
        depth: BMC 搜索深度
        file: Verilog 文件路径（优先于 code）
        solver: SMT solver 引擎 (yices, boolector, z3, 默认 yices)

    Returns:
        验证结果字典
    """
    start_time = time.perf_counter()
    logger.debug("formal_verify: top_module=%s depth=%d timeout=%d", top_module, depth, timeout)

    try:
        # 优先从文件读取
        if file:
            p = Path(normalize_path(file))
            if not p.exists():
                return {"success": False, "error": f"文件不存在: {file}"}
            code = p.read_text(encoding="utf-8")

        if not code:
            return {"success": False, "error": "需要提供代码 (code 或 file 参数)"}

        # 输入验证
        validate_code(code, "code")
        timeout = validate_timeout(timeout, "formal")

        top_module = top_module or extract_top_module(code)
        if top_module:
            top_module = validate_top_module(top_module)

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 写入设计文件
            design_file = tmpdir_path / "design.v"
            design_file.write_text(code, encoding="utf-8")

            # 生成 SBY 配置文件
            sby_config = _generate_sby_config(design_file, top_module, depth, solver)
            sby_file = tmpdir_path / "verify.sby"
            sby_file.write_text(sby_config, encoding="utf-8")

            # 执行 sby
            result = run_command(
                ["sby", "-f", str(sby_file)],
                timeout=timeout,
                cwd=str(tmpdir_path),
            )

            duration = time.perf_counter() - start_time

            # 解析结果
            passed = result.returncode == 0
            properties_result = _parse_sby_output(result.stdout, result.stderr)

            logger.info(
                "formal_verify: passed=%s properties=%d duration=%.3fs",
                passed,
                len(properties_result),
                duration,
            )

            output = {
                "success": True,
                "passed": passed,
                "top_module": top_module,
                "depth": depth,
                "duration": round(duration, 3),
                "properties": properties_result,
                "output": result.stdout,
            }

            if not passed:
                output["error"] = "形式验证失败"
                output["suggestion"] = "检查属性定义是否正确，或增加 BMC 深度"
                if result.stderr:
                    output["stderr"] = result.stderr

            return output

    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "SymbiYosys 未安装",
            "suggestion": "运行 superrtl setup 安装 EDA 工具",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stage": "formal",
            "error": f"形式验证超时 (>{timeout}s)",
            "suggestion": "减小 BMC 深度或优化验证属性",
        }
    except OSError as e:
        logger.exception("formal_verify: 系统错误")
        return {"success": False, "error": f"系统错误: {e}"}
    except Exception as e:
        logger.exception("formal_verify: 未预期错误")
        return {"success": False, "error": f"内部错误: {type(e).__name__}: {e}"}


def _generate_sby_config(
    design_file: Path, top_module: str, depth: int, solver: str = "yices"
) -> str:
    """生成 SymbiYosys 配置文件"""
    return f"""[tasks]
bmc

[options]
bmc: mode bmc
bmc: depth {depth}

[engines]
smtbmc {solver}

[script]
read_verilog {design_file.name}
prep -top {top_module}

[files]
{design_file.name}
"""


def _parse_sby_output(stdout: str, stderr: str) -> list[dict]:
    """解析 sby 输出，提取属性验证结果"""
    properties = []

    for line in stdout.splitlines():
        line = line.strip()

        # BMC pass
        if "PASS" in line or "proved" in line.lower():
            properties.append({"status": "passed", "detail": line})

        # BMC fail / counterexample
        elif "FAIL" in line or "counterexample" in line.lower():
            properties.append({"status": "failed", "detail": line})

        # Assertion result
        elif "assert" in line.lower() and ("pass" in line.lower() or "fail" in line.lower()):
            status = "passed" if "pass" in line.lower() else "failed"
            properties.append({"status": status, "detail": line})

    # 如果没有解析到具体属性，根据整体结果生成
    if not properties:
        if "DONE" in stdout and "PASS" in stdout:
            properties.append({"status": "passed", "detail": "BMC 验证通过"})
        elif "DONE" in stdout and "FAIL" in stdout:
            properties.append({"status": "failed", "detail": "BMC 发现反例"})

    return properties
