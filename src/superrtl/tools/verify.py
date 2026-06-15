"""
综合验证工具 — 一键运行 compile + simulate + lint + review
"""

import logging
import time

from ..utils import normalize_path
from ..validation import ValidationError, validate_files_list, validate_timeout

logger = logging.getLogger("superrtl.verify")


async def verify_design(
    design_files: list[str] = None,
    testbench_file: str = None,
    testbench: str = None,
    timeout: int = 60,
    top_module: str = "",
    skip: list[str] = None,
) -> dict:
    """
    综合验证：compile → simulate → lint → review

    Args:
        design_files: 设计文件路径列表
        testbench_file: 测试平台文件路径
        testbench: 测试平台代码字符串
        timeout: 仿真超时 (秒)
        top_module: 顶层模块名
        skip: 要跳过的步骤 (compile/simulate/lint/review)

    Returns:
        综合验证结果
    """
    start_time = time.perf_counter()
    skip = skip or []
    results = {}
    all_passed = True

    try:
        if not design_files:
            return {"success": False, "error": "需要提供设计文件 (design_files)"}
        validate_files_list(design_files, "design_files")
        timeout = validate_timeout(timeout, "simulate")
    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}

    # 读取所有设计文件内容
    from pathlib import Path

    code_parts = []
    for fp in design_files:
        p = Path(normalize_path(fp))
        if not p.exists():
            return {"success": False, "error": f"文件不存在: {fp}"}
        code_parts.append(p.read_text(encoding="utf-8"))
    combined_code = "\n".join(code_parts)

    # 读取 testbench
    tb_code = None
    if testbench_file:
        tb_path = Path(normalize_path(testbench_file))
        if not tb_path.exists():
            return {"success": False, "error": f"测试平台文件不存在: {testbench_file}"}
        tb_code = tb_path.read_text(encoding="utf-8")
    elif testbench:
        tb_code = testbench

    # Step 1: Compile
    if "compile" not in skip:
        from .compile import compile_verilog

        logger.info("verify: 开始编译")
        compile_result = await compile_verilog(files=design_files, top_module=top_module)
        results["compile"] = compile_result
        if not compile_result.get("success"):
            all_passed = False

    # Step 2: Simulate
    if "simulate" not in skip and tb_code:
        from .simulate import simulate_verilog

        logger.info("verify: 开始仿真")
        sim_result = await simulate_verilog(
            testbench=tb_code,
            testbench_file=testbench_file,
            timeout=timeout,
            design_file_paths=design_files,
        )
        results["simulate"] = sim_result
        if not sim_result.get("success") or not sim_result.get("passed"):
            all_passed = False

    # Step 3: Lint
    if "lint" not in skip:
        from .lint import lint_verilog

        logger.info("verify: 开始 Lint")
        lint_result = await lint_verilog(code=combined_code)
        results["lint"] = lint_result
        if not lint_result.get("success"):
            all_passed = False

    # Step 4: Review
    if "review" not in skip:
        from .review import review_verilog

        logger.info("verify: 开始审查")
        review_result = await review_verilog(code=combined_code)
        results["review"] = review_result
        if review_result.get("summary", {}).get("errors", 0) > 0:
            all_passed = False

    duration = time.perf_counter() - start_time

    # 汇总
    summary = {}
    for step, res in results.items():
        summary[step] = "PASS" if res.get("success") else "FAIL"
        if step == "simulate":
            summary[step] = "PASS" if res.get("passed") else "FAIL"

    return {
        "success": True,
        "passed": all_passed,
        "duration": round(duration, 3),
        "steps": summary,
        "results": results,
    }
