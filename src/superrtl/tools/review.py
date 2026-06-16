"""
Verilog 代码审查工具

基于规则的代码审查，检查可综合性、常见陷阱和编码风格。
"""

import logging
import re
from pathlib import Path

from ..utils import normalize_path
from ..validation import ValidationError, validate_code

logger = logging.getLogger("superrtl.review")


async def review_verilog(code: str = None, checks: list[str] = None, file: str = None) -> dict:
    """
    审查 Verilog 代码

    Args:
        code: Verilog 源代码字符串
        checks: 要执行的检查类别列表 (可选，默认全部)
        file: Verilog 文件路径（优先于 code）

    Returns:
        审查结果字典
    """
    # 优先从文件读取
    if file:
        p = Path(normalize_path(file))
        if not p.exists():
            return {"success": False, "error": f"文件不存在: {file}"}
        code = p.read_text(encoding="utf-8")

    if not code:
        return {"success": False, "error": "需要提供代码 (code 或 file 参数)"}

    try:
        validate_code(code, "code")
    except ValidationError as e:
        return {"success": False, "error": e.message, "suggestion": e.suggestion}

    available_checks = {
        "synthesizability": _check_synthesizability,
        "latch": _check_latch_inference,
        "naming": _check_naming,
        "reset": _check_reset,
        "case": _check_case_statements,
    }

    # 确定要执行的检查
    if checks:
        active_checks = {k: v for k, v in available_checks.items() if k in checks}
    else:
        active_checks = available_checks

    # 执行所有检查
    all_issues = []
    for check_name, check_func in active_checks.items():
        issues = check_func(code)
        all_issues.extend(issues)

    # 统计
    summary = {
        "errors": sum(1 for i in all_issues if i["severity"] == "error"),
        "warnings": sum(1 for i in all_issues if i["severity"] == "warning"),
        "infos": sum(1 for i in all_issues if i["severity"] == "info"),
    }

    # 判断是否可综合
    synthesizable = not any(i["category"] == "synthesizability" for i in all_issues)

    logger.info(
        "review_verilog: errors=%d warnings=%d infos=%d",
        summary["errors"],
        summary["warnings"],
        summary["infos"],
    )

    return {
        "success": True,
        "issues": all_issues,
        "summary": summary,
        "synthesizable": synthesizable,
        "checks_run": list(active_checks.keys()),
    }


def _check_synthesizability(code: str) -> list[dict]:
    """检查不可综合的结构"""
    issues = []

    # 检测 initial 块（非 testbench 中不可综合）
    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()

        # initial 块
        if re.match(r"\binitial\b", stripped) and "begin" not in stripped:
            issues.append(
                {
                    "severity": "warning",
                    "category": "synthesizability",
                    "line": i,
                    "message": "initial 块在综合时可能被忽略",
                    "suggestion": "使用复位逻辑替代 initial 块进行初始化",
                }
            )

        # # 延迟
        if re.search(r"#\d+", stripped) and not stripped.startswith("//"):
            issues.append(
                {
                    "severity": "error",
                    "category": "synthesizability",
                    "line": i,
                    "message": "使用了 # 延迟，不可综合",
                    "suggestion": "使用时钟计数器替代 # 延迟",
                }
            )

        # $display, $finish, $stop 等系统任务
        if re.search(r"\$display|\$finish|\$stop|\$write|\$monitor", stripped):
            issues.append(
                {
                    "severity": "error",
                    "category": "synthesizability",
                    "line": i,
                    "message": "系统任务不可综合",
                    "suggestion": "仅在 testbench 中使用系统任务",
                }
            )

        # $readmemh, $readmemb（某些工具支持，但不通用）
        if re.search(r"\$readmemh|\$readmemb", stripped):
            issues.append(
                {
                    "severity": "info",
                    "category": "synthesizability",
                    "line": i,
                    "message": "$readmemh/$readmemb 的综合支持因工具而异",
                    "suggestion": "确认目标工具是否支持",
                }
            )

    return issues


def _check_latch_inference(code: str) -> list[dict]:
    """检查可能导致锁存器推断的模式"""
    issues = []

    lines = code.splitlines()
    in_always = False
    has_if = False
    has_else = False
    always_start = 0

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 检测组合逻辑 always 块
        if re.match(r"always\s+@\s*\(\s*\*", stripped):
            in_always = True
            has_if = False
            has_else = False
            always_start = i

        elif in_always:
            # 检测 if 语句
            if re.match(r"\bif\b", stripped):
                has_if = True

            # 检测 else
            if re.match(r"\belse\b", stripped):
                has_else = True

            # 块结束
            if stripped == "end" or stripped == "endmodule":
                if has_if and not has_else:
                    issues.append(
                        {
                            "severity": "warning",
                            "category": "latch",
                            "line": always_start,
                            "message": "组合逻辑 always 块中 if 缺少 else，可能推断锁存器",
                            "suggestion": "添加 else 分支或使用完整的 case 语句",
                        }
                    )
                in_always = False

        # 检测不完整的 case
        if re.match(r"\bcase\b", stripped) and in_always:
            # 向前查找是否有 default
            case_start = i
            has_default = False
            depth = 1  # 第一个 case 已经匹配
            for j in range(i, min(i + 50, len(lines))):
                case_line = lines[j].strip()
                if "case" in case_line and j != i:
                    depth += 1
                if "endcase" in case_line:
                    depth -= 1
                    if depth == 0:
                        break
                if "default" in case_line:
                    has_default = True

            if not has_default:
                issues.append(
                    {
                        "severity": "warning",
                        "category": "latch",
                        "line": case_start,
                        "message": "case 语句缺少 default 分支，可能推断锁存器",
                        "suggestion": "添加 default 分支处理未匹配的情况",
                    }
                )

    return issues


def _check_naming(code: str) -> list[dict]:
    """检查命名规范"""
    issues = []

    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()

        # 检测信号声明中的驼峰命名（Verilog 通常用下划线）
        match = re.match(r"\b(input|output|reg|wire)\b.*\b([a-z]+[A-Z]\w+)\b", stripped)
        if match:
            name = match.group(2)
            # 排除常见的驼峰命名（如 clkDiv 在某些风格中可接受）
            # 但不排除 clkDivider、rstGenerator 等更长的名称
            if not (name.startswith("clk") and len(name) <= 6) and not (name.startswith("rst") and len(name) <= 6):
                issues.append(
                    {
                        "severity": "info",
                        "category": "naming",
                        "line": i,
                        "message": f"信号 '{name}' 使用了驼峰命名",
                        "suggestion": "建议使用下划线命名法 (snake_case)",
                    }
                )

    return issues


def _check_reset(code: str) -> list[dict]:
    """检查复位逻辑"""
    issues = []

    # 检测是否有寄存器声明但没有复位
    has_reg = bool(re.search(r"\breg\b", code))
    has_always_clk = bool(re.search(r"always\s+@\s*\(\s*posedge", code))
    has_reset = bool(re.search(r"\brst\b|\breset\b|\brst_n\b|\breset_n\b", code))

    if has_reg and has_always_clk and not has_reset:
        issues.append(
            {
                "severity": "warning",
                "category": "reset",
                "line": 1,
                "message": "检测到时序逻辑但未发现复位信号",
                "suggestion": "考虑添加复位逻辑以确保确定的初始状态",
            }
        )

    # 检测异步复位是否在敏感列表中
    for i, line in enumerate(code.splitlines(), 1):
        stripped = line.strip()
        if re.search(r"always\s+@\s*\(\s*posedge\s+clk\s*\)", stripped):
            # 检查下一行是否有复位使用
            if i < len(code.splitlines()):
                next_line = code.splitlines()[i].strip() if i < len(code.splitlines()) else ""
                if re.search(r"\brst\b|\breset\b", next_line):
                    issues.append(
                        {
                            "severity": "error",
                            "category": "reset",
                            "line": i,
                            "message": "复位信号未在敏感列表中",
                            "suggestion": "使用 always @(posedge clk or posedge rst) 异步复位",
                        }
                    )

    return issues


def _check_case_statements(code: str) -> list[dict]:
    """检查 case 语句"""
    issues = []

    lines = code.splitlines()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # 检测 casex/casez（某些工具不推荐）
        if re.match(r"\bcasex\b", stripped):
            issues.append(
                {
                    "severity": "warning",
                    "category": "case",
                    "line": i,
                    "message": "casex 将 x 和 z 视为无关项，可能导致仿真不一致",
                    "suggestion": "考虑使用 casez 替代，或使用 Verilog-2001 的 case?/casex?",
                }
            )

        # 检测 full_case 综合指令
        if "full_case" in stripped or "parallel_case" in stripped:
            issues.append(
                {
                    "severity": "info",
                    "category": "case",
                    "line": i,
                    "message": "使用了综合指令 full_case/parallel_case",
                    "suggestion": "确保理解这些指令对综合结果的影响",
                }
            )

    return issues
