"""
VCD 波形分析工具
"""

from ..utils import normalize_path
from ..utils.verilog import parse_vcd


async def analyze_waveform(
    vcd_file: str = None,
    vcd_content: str = None,
    signals: list[str] = None,
    compute_coverage: bool = False,
    protocol: str = None,
    protocol_config: dict = None,
) -> dict:
    """
    分析 VCD 波形文件

    Args:
        vcd_file: VCD 文件路径
        vcd_content: VCD 内容 (直接传入)
        signals: 要分析的信号列表
        compute_coverage: 是否计算翻转覆盖率
        protocol: 协议解码 (spi/i2c/uart)
        protocol_config: 协议配置参数

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

    # 计算翻转覆盖率
    if compute_coverage:
        parsed["coverage"] = _compute_toggle_coverage(parsed["signals"])

    # 协议解码
    if protocol:
        from .protocol_decode import decode_protocol

        decoded = decode_protocol(parsed["signals"], protocol, protocol_config)
        parsed["protocol_decode"] = decoded

    # 生成 ASCII 波形图
    if parsed["signals"]:
        parsed["ascii_waveform"] = _generate_ascii_waveform(parsed["signals"], max_cycles=20)

    return parsed


def _compute_toggle_coverage(signals: dict) -> dict:
    """计算翻转覆盖率"""
    if not signals:
        return {"total": 0, "toggled": 0, "coverage": 0.0}

    total = len(signals)
    toggled = 0
    details = {}

    for name, data in signals.items():
        values = data.get("values", [])
        has_toggle = False

        if len(values) >= 2:
            # 检查是否有至少一次值变化
            for i in range(1, len(values)):
                if values[i]["value"] != values[i - 1]["value"]:
                    has_toggle = True
                    break

        if has_toggle:
            toggled += 1

        details[name] = {
            "toggled": has_toggle,
            "value_count": len(values),
        }

    coverage = (toggled / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "toggled": toggled,
        "not_toggled": total - toggled,
        "coverage": round(coverage, 1),
        "details": details,
    }


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
