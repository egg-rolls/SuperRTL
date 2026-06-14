"""
Yosys 综合检查工具
"""

import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import extract_top_module, run_command
from ..validation import ValidationError, validate_code, validate_target, validate_top_module

# 目标工艺库对应的综合命令
_TARGET_SYNTH = {
    "generic": "synth",
    "xilinx": "synth_xilinx",
    "ice40": "synth_ice40",
}


async def synthesize_verilog(code: str, top_module: str = "", target: str = "generic") -> dict:
    """
    使用 Yosys 进行综合检查

    Args:
        code: Verilog 源代码
        top_module: 顶层模块名
        target: 目标工艺库 (generic, xilinx, ice40)

    Returns:
        综合结果字典
    """
    start_time = time.perf_counter()

    try:
        # 输入验证
        validate_code(code, "code")
        target = validate_target(target)
        top_module = top_module or extract_top_module(code)
        if top_module:
            top_module = validate_top_module(top_module)

        synth_cmd = _TARGET_SYNTH.get(target, "synth")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 写入代码文件
            design_file = tmpdir_path / "design.v"
            design_file.write_text(code, encoding="utf-8")

            # 创建综合脚本
            synth_script = f"""
read_verilog {design_file}
hierarchy -check -top {top_module}
proc
opt
fsm
opt
{synth_cmd}
stat
"""
            script_file = tmpdir_path / "synth.ys"
            script_file.write_text(synth_script, encoding="utf-8")

            # 执行综合
            result = run_command(["yosys", "-s", str(script_file)], timeout=120)

            duration = time.perf_counter() - start_time

            # 解析资源报告
            resources = _parse_resources(result.stdout)

            return {
                "success": result.returncode == 0,
                "top_module": top_module,
                "target": target,
                "duration": round(duration, 3),
                "resources": resources,
                "errors": result.stderr.splitlines() if result.returncode != 0 else [],
            }

    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Yosys 未安装",
            "suggestion": "运行 superrtl setup 安装 EDA 工具",
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "综合超时 (>120s)",
            "suggestion": "检查代码是否有过大的组合逻辑或循环依赖",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_resources(output: str) -> dict:
    """解析 Yosys 资源报告"""
    import re

    resources = {}

    patterns = {
        "wires": r"Number of wires:\s+(\d+)",
        "wire_bits": r"Number of wire bits:\s+(\d+)",
        "cells": r"Number of cells:\s+(\d+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, output)
        if match:
            resources[key] = int(match.group(1))

    return resources
