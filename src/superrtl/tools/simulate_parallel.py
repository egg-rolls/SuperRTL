"""
并行仿真工具 — 多个 testbench 并发运行
"""

import asyncio
import logging

from .simulate import simulate_verilog

logger = logging.getLogger("superrtl.simulate_parallel")


async def simulate_parallel(
    design_file_paths: list[str],
    testbench_files: list[str],
    timeout: int = 30,
    max_concurrent: int = 4,
) -> dict:
    """
    并行运行多个 testbench

    Args:
        design_file_paths: 设计文件路径列表
        testbench_files: 测试平台文件路径列表
        timeout: 每个仿真的超时时间 (秒)
        max_concurrent: 最大并发数

    Returns:
        并行仿真结果
    """
    if not design_file_paths:
        return {"success": False, "error": "需要提供设计文件路径 (design_file_paths)"}
    if not testbench_files:
        return {"success": False, "error": "需要提供至少一个测试平台文件"}
    if not isinstance(design_file_paths, list):
        return {"success": False, "error": "design_file_paths 必须是列表"}
    if not isinstance(testbench_files, list):
        return {"success": False, "error": "testbench_files 必须是列表"}

    sem = asyncio.Semaphore(max_concurrent)
    results = {}

    async def run_one(tb_file: str):
        async with sem:
            logger.info("simulate_parallel: 开始 %s", tb_file)
            result = await simulate_verilog(
                design_file_paths=design_file_paths,
                testbench_file=tb_file,
                timeout=timeout,
            )
            results[tb_file] = result

    # 并发运行所有 testbench
    tasks = [run_one(tb) for tb in testbench_files]
    await asyncio.gather(*tasks)

    # 汇总
    passed = sum(1 for r in results.values() if r.get("passed"))
    total = len(results)
    all_passed = passed == total

    return {
        "success": True,
        "passed": all_passed,
        "total": total,
        "passed_count": passed,
        "failed_count": total - passed,
        "results": results,
    }
