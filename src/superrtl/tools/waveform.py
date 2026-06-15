"""
VCD 波形分析工具
"""

from ..utils import normalize_path
from ..utils.verilog import parse_vcd


async def analyze_waveform(
    vcd_file: str = None, vcd_content: str = None, signals: list[str] = None
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
        vcd_file = normalize_path(vcd_file)
        try:
            with open(vcd_file, encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            return {"success": False, "error": f"文件不存在: {vcd_file}"}
    elif vcd_content:
        content = vcd_content
    else:
        return {"success": False, "error": "需要提供 vcd_file 或 vcd_content"}

    # 解析 VCD
    parsed = parse_vcd(content)

    # 如果指定了信号，只返回相关信号
    if signals:
        parsed["signals"] = {
            k: v
            for k, v in parsed["signals"].items()
            if k in signals or any(s in k for s in signals)
        }

    # 生成 ASCII 波形图
    if parsed["signals"]:
        parsed["ascii_waveform"] = _generate_ascii_waveform(parsed["signals"], max_cycles=20)

    return parsed


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
