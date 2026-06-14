---
name: "verilog-uart"
version: "1.0.0"
description: "UART 串口设计 - TX/RX/波特率发生器完整实现"
author: "SuperRTL Team"
tags: ["uart", "serial", "communication", "peripheral"]
triggers: ["uart", "serial", "串口", "串行通信", "baud"]
---

# UART 串口设计

## 概述

UART (通用异步收发器) 是最常用的串行通信接口。本文档提供完整的 TX、RX 和波特率发生器设计。

## 设计要点

### 1. UART 帧格式
```
空闲(高) | 起始位(低) | D0 D1 D2 D3 D4 D5 D6 D7 | 停止位(高)
```

### 2. 波特率计算
- 波特率分频值 = 系统时钟频率 / 波特率
- 例如：50MHz / 115200 = 434
- 16x 过采样：分频值 = 系统时钟 / (波特率 * 16)

### 3. 常用波特率
| 波特率 | 50MHz 分频值 | 100MHz 分频值 |
|-------|-------------|--------------|
| 9600 | 5208 | 10417 |
| 115200 | 434 | 868 |

## 代码模板

### 波特率发生器
```verilog
module baud_gen #(
    parameter CLK_FREQ  = 50_000_000,
    parameter BAUD_RATE = 115200
)(
    input      clk,
    input      rst_n,
    output reg baud_tick
);
    localparam DIV = CLK_FREQ / BAUD_RATE;
    localparam CNT_WIDTH = $clog2(DIV);

    reg [CNT_WIDTH-1:0] cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 0;
            baud_tick <= 0;
        end else begin
            if (cnt == DIV - 1) begin
                cnt <= 0;
                baud_tick <= 1;
            end else begin
                cnt <= cnt + 1;
                baud_tick <= 0;
            end
        end
    end
endmodule
```

### UART 发送器 (TX)
```verilog
module uart_tx #(
    parameter CLK_FREQ  = 50_000_000,
    parameter BAUD_RATE = 115200
)(
    input        clk,
    input        rst_n,
    input        tx_start,
    input  [7:0] tx_data,
    output reg   tx,
    output       tx_busy
);
    localparam DIV = CLK_FREQ / BAUD_RATE;

    localparam IDLE  = 3'b000;
    localparam START = 3'b001;
    localparam DATA  = 3'b010;
    localparam STOP  = 3'b011;

    reg [2:0] state;
    reg [15:0] baud_cnt;
    reg [3:0] bit_cnt;
    reg [7:0] tx_reg;

    assign tx_busy = (state != IDLE);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            tx <= 1'b1;
            baud_cnt <= 0;
            bit_cnt <= 0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    if (tx_start) begin
                        state <= START;
                        tx_reg <= tx_data;
                        baud_cnt <= 0;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (baud_cnt == DIV - 1) begin
                        state <= DATA;
                        baud_cnt <= 0;
                        bit_cnt <= 0;
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                DATA: begin
                    tx <= tx_reg[bit_cnt];
                    if (baud_cnt == DIV - 1) begin
                        baud_cnt <= 0;
                        if (bit_cnt == 7) begin
                            state <= STOP;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                STOP: begin
                    tx <= 1'b1;
                    if (baud_cnt == DIV - 1) begin
                        state <= IDLE;
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
```

### UART 接收器 (RX)
```verilog
module uart_rx #(
    parameter CLK_FREQ  = 50_000_000,
    parameter BAUD_RATE = 115200
)(
    input        clk,
    input        rst_n,
    input        rx,
    output reg [7:0] rx_data,
    output reg   rx_valid
);
    localparam DIV = CLK_FREQ / BAUD_RATE;
    localparam HALF_DIV = DIV / 2;

    localparam IDLE  = 3'b000;
    localparam START = 3'b001;
    localparam DATA  = 3'b010;
    localparam STOP  = 3'b011;

    reg [2:0] state;
    reg [15:0] baud_cnt;
    reg [3:0] bit_cnt;
    reg [7:0] rx_reg;
    reg rx_sync1, rx_sync2;

    // 同步器
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync1 <= 1'b1;
            rx_sync2 <= 1'b1;
        end else begin
            rx_sync1 <= rx;
            rx_sync2 <= rx_sync1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            rx_valid <= 0;
            baud_cnt <= 0;
            bit_cnt <= 0;
        end else begin
            rx_valid <= 0;
            case (state)
                IDLE: begin
                    if (!rx_sync2) begin
                        state <= START;
                        baud_cnt <= 0;
                    end
                end
                START: begin
                    if (baud_cnt == HALF_DIV) begin
                        if (!rx_sync2) begin
                            state <= DATA;
                            baud_cnt <= 0;
                            bit_cnt <= 0;
                        end else begin
                            state <= IDLE;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                DATA: begin
                    if (baud_cnt == DIV - 1) begin
                        baud_cnt <= 0;
                        rx_reg[bit_cnt] <= rx_sync2;
                        if (bit_cnt == 7) begin
                            state <= STOP;
                        end else begin
                            bit_cnt <= bit_cnt + 1;
                        end
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                STOP: begin
                    if (baud_cnt == DIV - 1) begin
                        state <= IDLE;
                        rx_data <= rx_reg;
                        rx_valid <= 1;
                    end else begin
                        baud_cnt <= baud_cnt + 1;
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 波特率不准 | 通信错误 | 使用精确分频 |
| RX 未同步 | 亚稳态 | 加 2 级同步器 |
| 采样点不在中点 | 数据错误 | 使用半周期采样 |
| 无超时机制 | 死锁 | 添加帧超时 |

## 验证检查清单

- [ ] 波特率误差 < 2%
- [ ] TX/RX 环回测试通过
- [ ] 各种数据模式测试 (0x00, 0xFF, 0x55, 0xAA)
- [ ] 连续发送不丢帧
