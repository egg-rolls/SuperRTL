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
    """查找匹配的信号值

    优先精确匹配，然后前缀匹配，最后包含匹配
    """
    # 精确匹配
    for name, data in signals.items():
        if name.lower() == name_pattern.lower():
            return data.get("values", [])

    # 前缀匹配（信号名以 pattern 开头，后面是 _ 或 . 或 [）
    for name, data in signals.items():
        name_lower = name.lower()
        pattern_lower = name_pattern.lower()
        if name_lower.startswith(pattern_lower) and (
            len(name_lower) == len(pattern_lower) or name_lower[len(pattern_lower)] in "_.["
        ):
            return data.get("values", [])

    # 包含匹配（作为后备）
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
        cs_active_high: CS 高有效 (默认 False，即 CS 低有效)
    """
    cpol = config.get("cpol", 0)
    cpha = config.get("cpha", 0)
    bits = config.get("bits", 8)
    cs_active_high = config.get("cs_active_high", False)
    cs_active = "1" if cs_active_high else "0"
    cs_idle = "0" if cs_active_high else "1"

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
    frame_start_time = 0
    last_cs = cs_idle
    inter_frame_gaps = []

    for entry in clk_vals:
        clk = str(entry["value"])
        t = entry["time"]

        # 检测时钟边沿
        is_rising = last_clk == "0" and clk == "1"
        is_falling = last_clk == "1" and clk == "0"
        last_clk = clk

        # CS 检测 — 使用时间戳查找，不要求信号数组对齐
        if cs_vals:
            cs = _lookup_value_at_time(cs_vals, len(cs_vals), t)
            if cs == cs_active and last_cs == cs_idle:
                # CS 激活 — 新帧开始
                in_frame = True
                current_bits = []
                current_miso_bits = []
                frame_start_time = t
            elif cs == cs_idle and last_cs == cs_active:
                # CS 释放 — 帧结束
                in_frame = False
                if current_bits:
                    frame = {
                        "mosi": _bits_to_hex(current_bits),
                        "miso": _bits_to_hex(current_miso_bits) if current_miso_bits else None,
                        "start_time": frame_start_time,
                        "stop_time": t,
                        "bits": len(current_bits),
                    }
                    # 计算帧持续时间
                    frame["duration"] = t - frame_start_time
                    frames.append(frame)
            last_cs = cs

        # 采样数据 — 使用时间戳查找
        if in_frame:
            sample_edge = (cpha == 0 and is_rising) or (cpha == 1 and is_falling)
            if sample_edge:
                if mosi_vals:
                    current_bits.append(_lookup_value_at_time(mosi_vals, len(mosi_vals), t))
                if miso_vals:
                    current_miso_bits.append(_lookup_value_at_time(miso_vals, len(miso_vals), t))

    # 计算帧间间隔
    if len(frames) >= 2:
        for j in range(1, len(frames)):
            gap = frames[j]["start_time"] - frames[j - 1]["stop_time"]
            inter_frame_gaps.append(gap)

    # 统计
    errors = []
    for idx, frame in enumerate(frames):
        if frame["bits"] != bits:
            errors.append(f"帧 {idx}: 期望 {bits} 位，实际 {frame['bits']} 位")

    return {
        "success": True,
        "protocol": "spi",
        "config": {
            "cpol": cpol,
            "cpha": cpha,
            "bits": bits,
            "cs_active_high": cs_active_high,
        },
        "frames": frames,
        "frame_count": len(frames),
        "inter_frame_gaps": inter_frame_gaps if inter_frame_gaps else None,
        "errors": errors if errors else None,
    }


def _decode_i2c(signals: dict, config: dict) -> dict:
    """解码 I2C 协议

    配置参数：
        address_bits: 地址位数 (7/10, 默认 7)

    状态机状态:
        IDLE       — 等待 START
        ADDR       — 收集地址字节 (8 bits)
        ACK_ADDR   — 地址后的 ACK/NACK
        DATA       — 收集数据字节 (8 bits)
        ACK_DATA   — 数据后的 ACK/NACK
    """
    address_bits = config.get("address_bits", 7)

    sda_vals = _get_signal_values(signals, "sda")
    scl_vals = _get_signal_values(signals, "scl")

    if not sda_vals or not scl_vals:
        return {"success": False, "error": "未找到 I2C 信号 (sda/scl)"}

    # 状态常量
    state_idle = "idle"
    state_addr = "addr"
    state_ack_addr = "ack_addr"
    state_data = "data"
    state_ack_data = "ack_data"

    state = state_idle
    current_byte = 0
    bit_count = 0
    addr_byte = 0
    data_bytes = []
    acks = []  # 记录每个字节的 ACK 状态
    errors = []
    frames = []
    transaction_start_time = 0

    last_sda = "1"
    last_scl = "1"

    def _finish_frame(time, reason="stop"):
        """完成当前帧并添加到结果"""
        nonlocal addr_byte, data_bytes, acks, errors

        if not data_bytes and not addr_byte:
            return

        # 解析地址
        if address_bits == 10 and len(data_bytes) >= 1:
            addr = ((addr_byte & 0x06) << 7) | data_bytes[0]
            rw = "W" if (addr_byte & 1) == 0 else "R"
            payload = data_bytes[1:]
        else:
            addr = addr_byte >> 1
            rw = "W" if (addr_byte & 1) == 0 else "R"
            payload = data_bytes

        frame = {
            "address": f"0x{addr:02X}",
            "rw": rw,
            "data": [f"0x{d:02X}" for d in payload],
            "acks": acks,
            "start_time": transaction_start_time,
            "stop_time": time,
            "end_reason": reason,
        }
        if errors:
            frame["errors"] = errors
        frames.append(frame)

    def _reset_transaction():
        """重置事务状态"""
        nonlocal state, current_byte, bit_count, addr_byte
        nonlocal data_bytes, acks, errors, transaction_start_time
        state = state_idle
        current_byte = 0
        bit_count = 0
        addr_byte = 0
        data_bytes = []
        acks = []
        errors = []
        transaction_start_time = 0

    # 使用 SCL 作为主时间轴，通过时间戳查找 SDA 值
    # 这样即使 SDA 和 SCL 的采样时间不完全对齐也能正确解码
    for scl_entry in scl_vals:
        scl = str(scl_entry["value"])
        time = scl_entry["time"]
        sda = _lookup_value_at_time(sda_vals, len(sda_vals), time)

        # 检测 START / Repeated START 条件: SDA 下降沿 while SCL 高
        if sda == "0" and last_sda == "1" and scl == "1":
            if state != state_idle:
                # Repeated START: 保存当前帧（如果有数据）
                _finish_frame(time, reason="repeated_start")
            # 开始新事务
            _reset_transaction()
            state = state_addr
            transaction_start_time = time

        # 检测 STOP 条件: SDA 上升沿 while SCL 高
        elif sda == "1" and last_sda == "0" and scl == "1":
            if state != state_idle:
                _finish_frame(time, reason="stop")
            _reset_transaction()

        # 数据采样: SCL 上升沿 (只在活跃状态下采样)
        elif scl == "1" and last_scl == "0" and state in (
            state_addr,
            state_data,
        ):
            bit = 1 if sda == "1" else 0
            current_byte = (current_byte << 1) | bit
            bit_count += 1

            if bit_count == 8:
                if state == state_addr:
                    addr_byte = current_byte
                    state = state_ack_addr
                elif state == state_data:
                    data_bytes.append(current_byte)
                    state = state_ack_data
                current_byte = 0
                bit_count = 0

        # ACK/NACK 采样: SCL 上升沿 (在 ACK 状态下)
        elif scl == "1" and last_scl == "0" and state in (
            state_ack_addr,
            state_ack_data,
        ):
            ack = sda == "0"  # ACK = SDA low, NACK = SDA high
            acks.append(ack)

            if not ack:
                if state == state_ack_addr:
                    errors.append(f"地址字节 0x{addr_byte:02X} NACK")
                else:
                    byte_val = data_bytes[-1] if data_bytes else 0
                    errors.append(f"数据字节 0x{byte_val:02X} NACK")

            # ACK 后继续等待数据或停止条件
            state = state_data

        last_sda = sda
        last_scl = scl

    # 处理未结束的事务（VCD 截断）
    if state != state_idle:
        _finish_frame(sda_vals[-1]["time"] if sda_vals else 0, reason="truncated")

    return {
        "success": True,
        "protocol": "i2c",
        "config": {"address_bits": address_bits},
        "frames": frames,
        "frame_count": len(frames),
        "error_count": sum(1 for f in frames if f.get("errors")),
    }


def _lookup_value_at_time(vals: list, current_idx: int, target_time: float) -> str:
    """查找指定时间点的信号值

    在 VCD 中，信号值在条目时间变化，整个期间保持不变。
    所以 target_time 的值 = 最近的 <= target_time 的条目的值。

    Args:
        vals: 信号值列表 [{"time": t, "value": v}, ...]
        current_idx: 当前条目索引 (优化：从这里开始搜索)
        target_time: 目标时间

    Returns:
        信号值字符串
    """
    # 从当前条目向前搜索
    best_val = "1"  # 默认空闲状态
    for i in range(min(current_idx + 1, len(vals))):
        if vals[i]["time"] <= target_time:
            best_val = str(vals[i]["value"])
        else:
            break
    return best_val


def _decode_uart(signals: dict, config: dict) -> dict:
    """解码 UART 协议

    配置参数：
        baud: 波特率 (用于位时间计算，可选)
        bits: 数据位 (默认 8)
        parity: 校验 (none/odd/even, 默认 none)
        stop: 停止位 (1/2, 默认 1)

    解码策略:
        1. 检测起始位 (下降沿)
        2. 使用位时间估算确定采样点
        3. 在每个位的中点采样
        4. 验证奇偶校验和停止位
    """
    bits = config.get("bits", 8)
    parity = config.get("parity", "none")
    stop_bits = config.get("stop", 1)
    baud = config.get("baud")

    tx_vals = _get_signal_values(signals, "tx") or _get_signal_values(signals, "uart_tx")
    rx_vals = _get_signal_values(signals, "rx") or _get_signal_values(signals, "uart_rx")

    if not tx_vals and not rx_vals:
        return {"success": False, "error": "未找到 UART 信号 (tx/rx)"}

    frames = []
    errors_summary = {"parity_errors": 0, "frame_errors": 0, "break_conditions": 0}

    for channel, vals in [("TX", tx_vals), ("RX", rx_vals)]:
        if not vals:
            continue

        # 估算位时间
        bit_time = _estimate_bit_time(vals) if not baud else (1.0 / baud)
        if bit_time <= 0:
            bit_time = 1.0

        # 帧参数
        total_bits = 1 + bits + (1 if parity != "none" else 0) + stop_bits
        # 起始位 + 数据位 + 校验位 + 停止位

        in_frame = False
        frame_start_time = 0
        next_sample_time = 0
        current_bits = []
        last_val = "1"  # 空闲状态
        entry_idx = 0  # 当前条目索引

        for entry in vals:
            val = str(entry["value"])
            t = entry["time"]

            # 起始位检测: 下降沿 (1→0)
            if val == "0" and last_val == "1" and not in_frame:
                in_frame = True
                frame_start_time = t
                current_bits = []
                # 第一个采样点: 当前时间 (起始位已在此处)
                # 后续采样点: 每隔 bit_time
                next_sample_time = t

            elif in_frame:
                # 检查是否到达或超过采样点
                while next_sample_time <= t and len(current_bits) < total_bits:
                    # 查找采样时间点的值
                    # 在 VCD 中，信号值在条目时间变化，整个期间保持不变
                    # 所以采样时间点的值 = 最近的 <= 采样时间的条目的值
                    sample_val = _lookup_value_at_time(vals, entry_idx, next_sample_time)
                    bit_val = 1 if sample_val == "1" else 0
                    current_bits.append(bit_val)
                    next_sample_time += bit_time

                # 检查帧是否完成
                if len(current_bits) >= total_bits:
                    # 解析数据位 (跳过起始位，取数据位)
                    # UART 发送 LSB first，所以第一个数据位是 bit 0
                    data_bits = current_bits[1 : 1 + bits]
                    data_byte = 0
                    for i, b in enumerate(data_bits):
                        data_byte |= b << i  # LSB first

                    frame_errors = []

                    # 奇偶校验验证
                    if parity != "none" and len(current_bits) > 1 + bits:
                        parity_bit = current_bits[1 + bits]
                        data_ones = sum(data_bits)
                        if parity == "even":
                            expected_parity = data_ones % 2
                        else:  # odd
                            expected_parity = (data_ones + 1) % 2
                        if parity_bit != expected_parity:
                            frame_errors.append("parity_error")
                            errors_summary["parity_errors"] += 1

                    # Stop bit 检测
                    stop_start = 1 + bits + (1 if parity != "none" else 0)
                    stop_bits_data = current_bits[stop_start:]
                    for sb in stop_bits_data:
                        if sb != 1:
                            frame_errors.append("frame_error")
                            errors_summary["frame_errors"] += 1
                            break

                    # Break condition: 数据全 0 且无停止位
                    if data_byte == 0 and all(b == 0 for b in current_bits):
                        frame_errors.append("break")
                        errors_summary["break_conditions"] += 1

                    frame = {
                        "channel": channel,
                        "data": f"0x{data_byte:02X}",
                        "char": chr(data_byte) if 32 <= data_byte < 127 else ".",
                        "time": frame_start_time,
                        "bit_time": round(bit_time, 2),
                    }
                    if frame_errors:
                        frame["errors"] = frame_errors
                    frames.append(frame)
                    in_frame = False

            last_val = val
            entry_idx += 1

    return {
        "success": True,
        "protocol": "uart",
        "config": {"bits": bits, "parity": parity, "stop": stop_bits},
        "frames": frames,
        "frame_count": len(frames),
        "errors_summary": errors_summary,
    }


def _estimate_bit_time(vals: list) -> float:
    """从信号变化中估算位时间

    策略:
    1. 首先尝试找连续同值采样的间隔 (最可靠)
    2. 回退: 使用所有相邻采样的间隔中位数
    """
    if len(vals) < 2:
        return 1.0  # 默认值

    # 策略 1: 连续同值间隔
    same_val_intervals = []
    for i in range(1, len(vals)):
        if vals[i]["value"] == vals[i - 1]["value"]:
            interval = abs(vals[i]["time"] - vals[i - 1]["time"])
            if interval > 0:
                same_val_intervals.append(interval)

    if same_val_intervals:
        same_val_intervals.sort()
        return same_val_intervals[len(same_val_intervals) // 2]

    # 策略 2: 所有间隔的中位数
    all_intervals = []
    for i in range(1, len(vals)):
        interval = abs(vals[i]["time"] - vals[i - 1]["time"])
        if interval > 0:
            all_intervals.append(interval)

    if not all_intervals:
        return 1.0

    all_intervals.sort()
    return all_intervals[len(all_intervals) // 2]


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
