---
name: "verilog-axi-lite-slave"
version: "1.0.0"
description: "AXI-Lite Slave 设计指南 - 参数化寄存器接口、状态机、字节使能"
author: "SuperRTL Team"
tags: ["axi", "axi-lite", "slave", "register", "bus", "interface"]
triggers: ["axi", "AXI-Lite", "slave", "寄存器接口", "总线"]
---

# AXI-Lite Slave 设计指南

## 概述

AXI-Lite 是 AXI4 协议的简化版本，适用于寄存器映射的低速控制接口。典型应用：
- 外设控制寄存器
- 配置空间
- 状态寄存器

## 设计要点

### 1. 通道结构

AXI-Lite 有 5 个独立通道：

| 通道 | 方向 | 用途 |
|------|------|------|
| AW (Write Address) | Master → Slave | 写地址 |
| W (Write Data) | Master → Slave | 写数据 + 字节使能 |
| B (Write Response) | Slave → Master | 写响应 |
| AR (Read Address) | Master → Slave | 读地址 |
| R (Read Data) | Slave → Master | 读数据 + 响应 |

### 2. 握手协议

每个通道使用 valid/ready 握手：
- 发送方拉高 `valid` 表示数据有效
- 接收方拉高 `ready` 表示可以接收
- 两者同时为高时传输完成

**关键规则**：
- `valid` 不能等待 `ready` 才拉高
- `ready` 可以在 `valid` 之前或之后拉高

### 3. 字节使能 (WSTRB)

`wstrb[3:0]` 对应 4 个字节：
- `wstrb[0]` = 写入 `[7:0]`
- `wstrb[1]` = 写入 `[15:8]`
- `wstrb[2]` = 写入 `[23:16]`
- `wstrb[3]` = 写入 `[31:24]`

### 4. 响应码

| BRESP/RRESP | 含义 |
|-------------|------|
| 2'b00 | OKAY - 成功 |
| 2'b01 | EXOKAY - 独占访问成功 |
| 2'b10 | SLVERR - 从机错误 |
| 2'b11 | DECERR - 解码错误 |

## 代码模板

### 基础 Slave（状态机方式）

参见 `shared/templates/axi_lite_slave.v`

### 带中断的 Slave

```verilog
// 在寄存器定义中添加中断状态和使能
reg [31:0] irq_status;  // 中断状态（写1清除）
reg [31:0] irq_enable;  // 中断使能

wire irq = |(irq_status & irq_enable);

// 写逻辑中处理中断清除
if (wr_addr == IRQ_STATUS_OFFSET) begin
    irq_status <= irq_status & ~wdata;  // 写1清除
end
```

### 带 FIFO 的 Slave

```verilog
// TX FIFO 写入
if (wr_addr == TX_FIFO_OFFSET) begin
    tx_fifo[wr_ptr] <= wdata;
    wr_ptr <= wr_ptr + 1;
end

// RX FIFO 读出
if (rd_addr == RX_FIFO_OFFSET) begin
    rdata <= rx_fifo[rd_ptr];
    rd_ptr <= rd_ptr + 1;
end
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|------|------|----------|
| valid 等待 ready | 死锁 | valid 先于或同时于 ready |
| 未处理字节使能 | 部分写入失败 | 逐字节检查 wstrb |
| 读写同时访问 | 数据不一致 | 添加仲裁或互斥逻辑 |
| 地址未对齐 | 访问错误寄存器 | 忽略低 2 位地址 |
| 未初始化寄存器 | 不确定状态 | 复位时清零所有寄存器 |

## 验证检查清单

- [ ] 复位后所有寄存器为 0
- [ ] 写入后读出值一致
- [ ] 字节使能正确生效
- [ ] 无效地址返回 DEAD_BEEF 或 SLVERR
- [ ] 写响应在写数据后返回
- [ ] 读数据在读地址后返回
- [ ] valid/ready 握手无死锁
