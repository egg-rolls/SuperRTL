"""
VCD 波形分析工具
"""

import re


async def analyze_waveform(
    vcd_file: str = None,
    vcd_content: str = None,
    signals: list[str] = None
) -> dict:
    """
    分析 VCD 波形文件

    Args:
        vcd_file: VCD 文件路径
        vcd_content: VCD 内容 (直接传入)
        signals: 要分析的信号列表

    Returns:
        波形分析结果
    """
    # 读取 VCD 内容
    if vcd_file:
        try:
            with open(vcd_file) as f:
                content = f.read()
        except FileNotFoundError:
            return {"success": False, "error": f"文件不存在: {vcd_file}"}
    elif vcd_content:
        content = vcd_content
    else:
        return {"success": False, "error": "需要提供 vcd_file 或 vcd_content"}

    # 解析 VCD
    parsed = _parse_vcd(content)

    # 如果指定了信号，只返回相关信号
    if signals:
        parsed["signals"] = {
            k: v for k, v in parsed["signals"].items()
            if k in signals or any(s in k for s in signals)
        }

    # 生成 ASCII 波形图
    if parsed["signals"]:
        parsed["ascii_waveform"] = _generate_ascii_waveform(
            parsed["signals"],
            max_cycles=20
        )

    return parsed


def _parse_vcd(content: str) -> dict:
    """解析 VCD 文件"""
    result = {
        "success": True,
        "timescale": "1ns",
        "signals": {},
        "time_range": {"start": 0, "end": 0}
    }

    current_time = 0
    signal_map = {}  # id -> name

    for line in content.splitlines():
        line = line.strip()

        # 解析时间刻度
        if "$timescale" in line:
            match = re.search(r"\$timescale\s+(.+?)\s+\$end", content)
            if match:
                result["timescale"] = match.group(1)

        # 解析信号定义
        elif line.startswith("$var"):
            match = re.match(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)", line)
            if match:
                width = int(match.group(1))
                sig_id = match.group(2)
                sig_name = match.group(3)
                signal_map[sig_id] = sig_name
                result["signals"][sig_name] = {
                    "width": width,
                    "values": []
                }

        # 解析时间
        elif line.startswith("#"):
            current_time = int(line[1:])
            result["time_range"]["end"] = max(result["time_range"]["end"], current_time)

        # 解析信号值变化
        elif line and line[0] in "01xzXZ":
            value = line[0]
            sig_id = line[1:] if len(line) > 1 else ""
            if sig_id in signal_map:
                sig_name = signal_map[sig_id]
                if sig_name in result["signals"]:
                    result["signals"][sig_name]["values"].append({
                        "time": current_time,
                        "value": value
                    })

        # 多位信号
        elif line.startswith("b"):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # 去掉 'b' 前缀
                sig_id = parts[1]
                if sig_id in signal_map:
                    sig_name = signal_map[sig_id]
                    if sig_name in result["signals"]:
                        result["signals"][sig_name]["values"].append({
                            "time": current_time,
                            "value": value
                        })

    return result


def _generate_ascii_waveform(signals: dict, max_cycles: int = 20) -> str:
    """生成 ASCII 波形图"""
    if not signals:
        return "No signals to display"

    lines = []
    max_name_len = max(len(name) for name in signals.keys())

    for name, data in signals.items():
        values = data["values"][:max_cycles]

        # 构建波形行
        wave = f"{name:>{max_name_len}} |"

        for val in values:
            if val["value"] in ("1", "H"):
                wave += "‾‾‾|"
            elif val["value"] in ("0", "L"):
                wave += "___|"
            elif val["value"] in ("x", "X"):
                wave += "xxx|"
            elif val["value"] in ("z", "Z"):
                wave += "zzz|"
            else:
                wave += f"{val['value']:>3}|"

        lines.append(wave)

    # 添加时间轴
    time_line = " " * max_name_len + " |"
    for i in range(min(max_cycles, max(len(d["values"]) for d in signals.values()))):
        time_line += f"{i:>3}|"
    lines.append(time_line)

    return "\n".join(lines)
