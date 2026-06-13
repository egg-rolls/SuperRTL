"""
Verilog 代码分析工具函数
"""

import re


def extract_top_module(code: str) -> str:
    """从代码中提取顶层模块名"""
    match = re.search(r"\bmodule\s+(\w+)\b", code)
    return match.group(1) if match else "top"


def extract_ports(code: str) -> list[dict]:
    """从 Verilog 代码中提取端口信息"""
    ports = []

    # 匹配端口声明
    pattern = r"(input|output)\s+(?:reg\s+)?(?:\[(\d+):0\]\s+)?(\w+)"

    for match in re.finditer(pattern, code):
        direction, width, name = match.groups()
        ports.append({
            "direction": direction,
            "width": int(width) + 1 if width else 1,
            "name": name
        })

    return ports
