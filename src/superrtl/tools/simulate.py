"""
Icarus Verilog 仿真工具
"""

import logging
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ..utils import normalize_path, run_command
from ..validation import ValidationError, validate_code, validate_files_list, validate_timeout

logger = logging.getLogger("superrtl.simulate")


async def simulate_verilog(
    code: str = None,
    testbench: str = None,
    testbench_file: str = None,
    timeout: int = 30,
    design_files: list[str] = None,
    design_file_paths: list[str] = None,
) -> dict:
    """
    运行 Verilog 仿真

    支持两种调用方式：
    1. 单文件模式：传入 code 和 testbench 字符串
    2. 多文件模式：传入 design_files（代码字符串列表）或 design_file_paths（文件路径列表）

    测试平台支持两种传入方式：
    - testbench: 测试平台代码字符串
    - testbench_file: 测试平台文件路径（优先级更高）

    Args:
        code: 单个设计文件代码（单文件模式）
        testbench: 测试平台代码字符串
        testbench_file: 测试平台文件路径（优先于 testbench）
        timeout: 仿真超时时间 (秒)
        design_files: 多个设计文件代码字符串列表（多文件模式）
        design_file_paths: 多个设计文件路径列表（多文件模式）

    Returns:
        仿真结果字典
    """
    start_time = time.perf_counter()
    logger.debug("simulate_verilog: design_file_paths=%s, timeout=%s", design_file_paths, timeout)

    try:
        # 输入验证
        if timeout is None:
            timeout = 30
        timeout = validate_timeout(timeout, "simulate")

        if not testbench and not testbench_file:
            return {
                "success": False,
                "error": "需要提供测试平台 (testbench 或 testbench_file 参数)",
            }

        if design_file_paths is not None:
            if not isinstance(design_file_paths, list):
                return {
                    "success": False,
                    "error": "design_file_paths 必须是列表",
                }
            validate_files_list(design_file_paths, "design_file_paths")
        elif design_files is not None:
            if not isinstance(design_files, list):
                return {
                    "success": False,
                    "error": "design_files 必须是列表",
                }
            validate_files_list(design_files, "design_files")
        elif code:
            validate_code(code, "code")
        else:
            return {"success": False, "error": "需要提供设计文件"}

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            source_files = []

            # 多文件模式：从文件路径读取
            if design_file_paths:
                for fp in design_file_paths:
                    p = Path(normalize_path(fp))
                    if not p.exists():
                        return {"success": False, "error": f"文件不存在: {fp}"}
                    dest = tmpdir_path / p.name
                    shutil.copy2(str(p), str(dest))
                    source_files.append(str(dest))

            # 多文件模式：design_files 自动判断是路径还是代码
            elif design_files:
                for i, item in enumerate(design_files):
                    p = Path(normalize_path(item))
                    if p.exists() and p.suffix in (".v", ".sv", ".vh", ".svh"):
                        # 看起来是存在的文件路径
                        dest = tmpdir_path / p.name
                        shutil.copy2(str(p), str(dest))
                    else:
                        # 当作代码字符串
                        dest = tmpdir_path / f"design_{i}.v"
                        dest.write_text(item, encoding="utf-8")
                    source_files.append(str(dest))

            # 单文件模式
            elif code:
                design_file = tmpdir_path / "design.v"
                design_file.write_text(code, encoding="utf-8")
                source_files.append(str(design_file))

            # 测试平台：优先使用文件路径，回退到代码字符串
            if testbench_file:
                tb_path = Path(normalize_path(testbench_file))
                if not tb_path.exists():
                    return {"success": False, "error": f"测试平台文件不存在: {testbench_file}"}
                dest_tb = tmpdir_path / tb_path.name
                shutil.copy2(str(tb_path), str(dest_tb))
                source_files.append(str(dest_tb))
            else:
                tb_file = tmpdir_path / "testbench.v"
                tb_file.write_text(testbench, encoding="utf-8")
                source_files.append(str(tb_file))

            # 编译
            output_file = tmpdir_path / "simulation.vvp"
            compile_result = run_command(
                ["iverilog", "-o", str(output_file)] + source_files,
                timeout=timeout,
            )

            if compile_result.returncode != 0:
                logger.warning("simulate_verilog: 编译失败 stderr=%s", compile_result.stderr[:200])
                return {
                    "success": False,
                    "stage": "compilation",
                    "error": "仿真编译失败",
                    "errors": compile_result.stderr.splitlines(),
                    "duration": time.perf_counter() - start_time,
                    "suggestion": "检查模块名是否正确、端口连接是否匹配",
                }

            # 仿真
            sim_result = run_command(
                ["vvp", str(output_file)], timeout=timeout, cwd=str(tmpdir_path)
            )

            duration = time.perf_counter() - start_time

            # 判断结果
            passed = "PASS" in sim_result.stdout and "FAIL" not in sim_result.stdout
            logger.info("simulate_verilog: passed=%s duration=%.3fs", passed, duration)

            result = {
                "success": True,
                "passed": passed,
                "stage": "simulation",
                "duration": round(duration, 3),
                "output": sim_result.stdout,
                "source_files": len(source_files) - 1,
            }

            # 查找 VCD 文件
            vcd_files = list(tmpdir_path.glob("*.vcd"))
            if vcd_files:
                vcd_file = vcd_files[0]
                persistent_vcd = Path.cwd() / "simulation.vcd"
                shutil.copy2(str(vcd_file), str(persistent_vcd))
                result["vcd_file"] = str(persistent_vcd)
                result["vcd_size"] = persistent_vcd.stat().st_size

            if sim_result.stderr:
                result["warnings"] = sim_result.stderr.splitlines()

            return result

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
            "stage": "simulation",
            "error": f"仿真超时 (>{timeout}s)",
            "suggestion": "检查是否有无限循环，或使用 --timeout 增加超时时间",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
