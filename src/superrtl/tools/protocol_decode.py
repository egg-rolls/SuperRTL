"""
波形协议解码器

从 VCD 信号数据中解码 SPI/I2C/UART 协议帧。
"""

import logging

logger = logging.getLogger("superrtl.protocol_decode")


def decode_protocol(signals: dict, protocol: str, config: dict = None) -> dict:
    """
    解码协议帧

    Args:
        signals: VCD 解析后的信号字典
        protocol: 协议类型 (spi/i2c/uart)
        config: 协议配置参数

    Returns:
        解码结果
    """
    config = config or {}

    if protocol == "spi":
        return _decode_spi(signals, config)
    elif protocol == "i2c":
        return _decode_i2c(signals, config)
    elif protocol == "uart":
        return _decode_uart(signals, config)
    else:
        return {"success": False, "error": f"不支持的协议: {protocol}"}


def _get_signal_values(signals: dict, name_pattern: str) -> list:
    """查找匹配的信号值"""
    for name, data in signals.items():
        if name_pattern.lower() in name.lower():
            return data.get("values", [])
    return []


def _decode_spi(signals: dict, config: dict) -> dict:
    """解码 SPI 协议

    配置参数：
        cpol: 时钟极性 (0/1, 默认 0)
        cpha: 时钟相位 (0/1, 默认 0)
        bits: 每帧位数 (默认 8)
    """
    cpol = config.get("cpol", 0)
    cpha = config.get("cpha", 0)
    bits = config.get("bits", 8)

    # 查找信号
    clk_vals = (
        _get_signal_values(signals, "sck")
        or _get_signal_values(signals, "clk")
        or _get_signal_values(signals, "spi_clk")
    )
    mosi_vals = _get_signal_values(signals, "mosi") or _get_signal_values(signals, "copi")
    miso_vals = _get_signal_values(signals, "miso") or _get_signal_values(signals, "cipo")
    cs_vals = (
        _get_signal_values(signals, "cs")
        or _get_signal_values(signals, "ss")
        or _get_signal_values(signals, "cs_n")
    )

    if not clk_vals:
        return {"success": False, "error": "未找到 SPI 时钟信号 (sck/clk/spi_clk)"}

    frames = []
    current_bits = []
    current_miso_bits = []
    in_frame = False
    last_clk = str(cpol)

    for i, entry in enumerate(clk_vals):
        clk = str(entry["value"])

        # 检测时钟边沿
        is_rising = last_clk == "0" and clk == "1"
        is_falling = last_clk == "1" and clk == "0"
        last_clk = clk

        # CS 检测
        if cs_vals and i < len(cs_vals):
            cs = str(cs_vals[i]["value"])
            if cs == "0" and not in_frame:
                in_frame = True
                current_bits = []
                current_miso_bits = []
            elif cs == "1" and in_frame:
                in_frame = False
                if current_bits:
                    frames.append(
                        {
                            "mosi": _bits_to_hex(current_bits),
                            "miso": _bits_to_hex(current_miso_bits) if current_miso_bits else None,
                            "time": entry["time"],
                            "bits": len(current_bits),
                        }
                    )

        # 采样数据
        if in_frame:
            sample_edge = (cpha == 0 and is_rising) or (cpha == 1 and is_falling)
            if sample_edge:
                if mosi_vals and i < len(mosi_vals):
                    current_bits.append(str(mosi_vals[i]["value"]))
                if miso_vals and i < len(miso_vals):
                    current_miso_bits.append(str(miso_vals[i]["value"]))

    return {
        "success": True,
        "protocol": "spi",
        "config": {"cpol": cpol, "cpha": cpha, "bits": bits},
        "frames": frames,
        "frame_count": len(frames),
    }


def _decode_i2c(signals: dict, config: dict) -> dict:
    """解码 I2C 协议

    配置参数：
        address_bits: 地址位数 (7/10, 默认 7)
    """
    address_bits = config.get("address_bits", 7)

    sda_vals = _get_signal_values(signals, "sda")
    scl_vals = _get_signal_values(signals, "scl")

    if not sda_vals or not scl_vals:
        return {"success": False, "error": "未找到 I2C 信号 (sda/scl)"}

    frames = []
    current_byte = 0
    bit_count = 0
    in_transaction = False
    last_sda = "1"
    last_scl = "1"
    byte_index = 0
    addr_byte = 0
    data_bytes = []

    for i in range(min(len(sda_vals), len(scl_vals))):
        sda = str(sda_vals[i]["value"])
        scl = str(scl_vals[i]["value"])
        time = sda_vals[i]["time"]

        # 起始条件: SDA 下降沿 while SCL 高
        if sda == "0" and last_sda == "1" and scl == "1":
            in_transaction = True
            current_byte = 0
            bit_count = 0
            byte_index = 0
            data_bytes = []

        # 停止条件: SDA 上升沿 while SCL 高
        elif sda == "1" and last_sda == "0" and scl == "1":
            if in_transaction and data_bytes:
                addr = addr_byte >> 1
                rw = "W" if (addr_byte & 1) == 0 else "R"
                frames.append(
                    {
                        "address": f"0x{addr:02X}",
                        "rw": rw,
                        "data": [f"0x{d:02X}" for d in data_bytes],
                        "time": time,
                    }
                )
            in_transaction = False

        # 数据采样: SCL 上升沿
        elif scl == "1" and last_scl == "0" and in_transaction:
            bit = 1 if sda == "1" else 0
            current_byte = (current_byte << 1) | bit
            bit_count += 1

            if bit_count == 8:
                if byte_index == 0:
                    addr_byte = current_byte
                else:
                    data_bytes.append(current_byte)
                byte_index += 1
                current_byte = 0
                bit_count = 0

        # ACK 检测 (第 9 个时钟)
        elif bit_count == 8 and scl == "1" and last_scl == "0":
            # ACK = SDA low
            pass

        last_sda = sda
        last_scl = scl

    return {
        "success": True,
        "protocol": "i2c",
        "config": {"address_bits": address_bits},
        "frames": frames,
        "frame_count": len(frames),
    }


def _decode_uart(signals: dict, config: dict) -> dict:
    """解码 UART 协议

    配置参数：
        baud: 波特率 (用于计算，可选)
        bits: 数据位 (默认 8)
        parity: 校验 (none/odd/even, 默认 none)
        stop: 停止位 (1/2, 默认 1)
    """
    bits = config.get("bits", 8)
    parity = config.get("parity", "none")
    stop_bits = config.get("stop", 1)

    tx_vals = _get_signal_values(signals, "tx") or _get_signal_values(signals, "uart_tx")
    rx_vals = _get_signal_values(signals, "rx") or _get_signal_values(signals, "uart_rx")

    if not tx_vals and not rx_vals:
        return {"success": False, "error": "未找到 UART 信号 (tx/rx)"}

    frames = []

    for channel, vals in [("TX", tx_vals), ("RX", rx_vals)]:
        if not vals:
            continue

        # 检测起始位 (下降沿)
        in_frame = False
        bit_index = 0
        current_byte = 0
        frame_start_time = 0

        # 解码
        last_val = "1"  # 空闲状态
        for entry in vals:
            val = str(entry["value"])

            # 起始位检测
            if val == "0" and last_val == "1" and not in_frame:
                in_frame = True
                bit_index = 0
                current_byte = 0
                frame_start_time = entry["time"]

            elif in_frame:
                # 跳过起始位
                if bit_index == 0:
                    bit_index = 1
                    continue

                # 数据位
                if 1 <= bit_index <= bits:
                    bit = 1 if val == "1" else 0
                    current_byte = current_byte | (bit << (bit_index - 1))

                bit_index += 1

                # 帧结束
                expected_bits = 1 + bits + (1 if parity != "none" else 0) + stop_bits
                if bit_index > expected_bits:
                    in_frame = False
                    frames.append(
                        {
                            "channel": channel,
                            "data": f"0x{current_byte:02X}",
                            "char": chr(current_byte) if 32 <= current_byte < 127 else ".",
                            "time": frame_start_time,
                        }
                    )

            last_val = val

    return {
        "success": True,
        "protocol": "uart",
        "config": {"bits": bits, "parity": parity, "stop": stop_bits},
        "frames": frames,
        "frame_count": len(frames),
    }


def _bits_to_hex(bits: list) -> str:
    """位列表转十六进制字符串"""
    if not bits:
        return "0x0"
    value = 0
    for b in bits:
        if b in ("1", "H"):
            value = (value << 1) | 1
        else:
            value = value << 1
    nibbles = max(1, (len(bits) + 3) // 4)
    return f"0x{value:0{nibbles}X}"
