"""
Icarus Verilog 仿真工具
"""

import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import run_command


async def simulate_verilog(code: str, testbench: str, timeout: int = 30) -> dict:
    """
    运行 Verilog 仿真

    Args:
        code: Verilog 源代码
        testbench: 测试平台代码
        timeout: 仿真超时时间 (秒)

    Returns:
        仿真结果字典
    """
    start_time = time.perf_counter()

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 写入文件
            design_file = tmpdir_path / "design.v"
            design_file.write_text(code)

            tb_file = tmpdir_path / "testbench.v"
            tb_file.write_text(testbench)

            # 编译
            output_file = tmpdir_path / "simulation.vvp"
            compile_result = run_command(
                ["iverilog", "-o", str(output_file), str(design_file), str(tb_file)],
                timeout=timeout,
            )

            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "stage": "compilation",
                    "errors": compile_result.stderr.splitlines(),
                    "duration": time.perf_counter() - start_time,
                }

            # 仿真
            vcd_file = tmpdir_path / "waveform.vcd"
            sim_result = run_command(
                ["vvp", str(output_file)], timeout=timeout, cwd=str(tmpdir_path)
            )

            duration = time.perf_counter() - start_time

            # 判断结果
            passed = "PASS" in sim_result.stdout

            result = {
                "success": True,
                "passed": passed,
                "stage": "simulation",
                "duration": round(duration, 3),
                "output": sim_result.stdout,
            }

            # 如果有 VCD 文件，记录信息
            if vcd_file.exists():
                result["vcd_file"] = str(vcd_file)
                result["vcd_size"] = vcd_file.stat().st_size

            # 如果有错误输出
            if sim_result.stderr:
                result["warnings"] = sim_result.stderr.splitlines()

            return result

    except FileNotFoundError:
        return {
            "success": False,
            "error": (
                "Icarus Verilog 未安装。"
                "请运行: scoop install iverilog (Windows)"
                " 或 brew install icarus-verilog (macOS)"
            ),
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stage": "simulation", "error": f"仿真超时 (>{timeout}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}
