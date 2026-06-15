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
        ports.append(
            {"direction": direction, "width": int(width) + 1 if width else 1, "name": name}
        )

    return ports


def parse_vcd(content: str, include_scope: bool = False) -> dict:
    """解析 VCD 文件内容

    Args:
        content: VCD 文件的文本内容
        include_scope: 是否解析 $scope/$upscope 层次结构并构建完整路径

    Returns:
        解析结果字典，包含 timescale, signals, time_range 等字段
    """
    result = {
        "success": True,
        "timescale": "1ns",
        "signals": {},
        "time_range": {"start": 0, "end": 0},
    }

    current_time = 0
    signal_map = {}  # id -> name
    scope_stack = [] if include_scope else None

    for line in content.splitlines():
        line = line.strip()

        # 解析时间刻度
        if "$timescale" in line:
            match = re.search(r"\$timescale\s+(.+?)\s+\$end", content)
            if match:
                result["timescale"] = match.group(1).strip()

        # 解析层次（仅当 include_scope=True）
        elif include_scope and line.startswith("$scope"):
            match = re.match(r"\$scope\s+\w+\s+(\S+)\s+\$end", line)
            if match:
                scope_stack.append(match.group(1))

        elif include_scope and line.startswith("$upscope"):
            if scope_stack:
                scope_stack.pop()

        # 解析信号定义
        elif line.startswith("$var"):
            match = re.match(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)", line)
            if match:
                width = int(match.group(1))
                sig_id = match.group(2)
                sig_name = match.group(3)
                # 构建完整路径（包含 scope）
                if include_scope and scope_stack:
                    full_name = ".".join(scope_stack + [sig_name])
                else:
                    full_name = sig_name
                signal_map[sig_id] = full_name
                result["signals"][full_name] = {"width": width, "values": []}

        # 解析时间
        elif line.startswith("#"):
            try:
                current_time = int(line[1:])
                result["time_range"]["end"] = max(result["time_range"]["end"], current_time)
            except ValueError:
                pass

        # 解析信号值变化（单位信号）
        elif line and line[0] in "01xzXZ":
            value = line[0]
            sig_id = line[1:].strip() if len(line) > 1 else ""
            if sig_id in signal_map:
                sig_name = signal_map[sig_id]
                if sig_name in result["signals"]:
                    result["signals"][sig_name]["values"].append(
                        {"time": current_time, "value": value}
                    )

        # 多位信号
        elif line.startswith("b"):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # 去掉 'b' 前缀
                sig_id = parts[1]
                if sig_id in signal_map:
                    sig_name = signal_map[sig_id]
                    if sig_name in result["signals"]:
                        result["signals"][sig_name]["values"].append(
                            {"time": current_time, "value": value}
                        )

    return result
