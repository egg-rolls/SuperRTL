---
name: "verilog-spi"
version: "1.0.0"
description: "SPI 通信接口设计 - 主从模式、CPOL/CPHA 配置"
author: "SuperRTL Team"
tags: ["spi", "serial", "communication", "protocol"]
triggers: ["spi", "serial peripheral", "spi master", "spi slave"]
---

# SPI 通信接口设计

## 概述

SPI (Serial Peripheral Interface) 是常用的同步串行通信接口，支持全双工通信。本文档介绍 SPI 主机和从机的设计。

## 设计要点

### 1. SPI 信号
| 信号 | 方向 | 说明 |
|------|------|------|
| SCLK | 主→从 | 时钟 |
| MOSI | 主→从 | 主出从入 |
| MISO | 从→主 | 主入从出 |
| CS_N | 主→从 | 片选 (低有效) |

### 2. SPI 模式
| 模式 | CPOL | CPHA | 空闲时钟 | 采样边沿 |
|------|------|------|----------|----------|
| 0 | 0 | 0 | 低 | 上升沿采样 |
| 1 | 0 | 1 | 低 | 下降沿采样 |
| 2 | 1 | 0 | 高 | 下降沿采样 |
| 3 | 1 | 1 | 高 | 上升沿采样 |

### 3. 时序要求
- 数据在采样边沿前必须稳定
- CS_N 在传输期间保持低电平
- MSB 先传或 LSB 先传可配置

## 代码模板

### SPI 主机
```verilog
module spi_master #(
    parameter CLK_DIV = 4,      // 时钟分频
    parameter CPOL = 0,         // 时钟极性
    parameter CPHA = 0,         // 时钟相位
    parameter DATA_WIDTH = 8    // 数据宽度
)(
    input                       clk,
    input                       rst_n,
    // 用户接口
    input                       start,
    input  [DATA_WIDTH-1:0]     tx_data,
    output reg [DATA_WIDTH-1:0] rx_data,
    output reg                  done,
    // SPI 接口
    output reg                  sclk,
    output                      mosi,
    input                       miso,
    output reg                  cs_n
);

    localparam HALF_DIV = CLK_DIV / 2;

    reg [3:0] bit_cnt;
    reg [DATA_WIDTH-1:0] tx_reg;
    reg [DATA_WIDTH-1:0] rx_reg;
    reg [15:0] clk_cnt;
    reg active;

    assign mosi = tx_reg[DATA_WIDTH-1];

    // SPI 时钟生成
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_cnt <= 0;
            sclk <= CPOL;
        end else if (active) begin
            if (clk_cnt == HALF_DIV - 1) begin
                clk_cnt <= 0;
                sclk <= ~sclk;
            end else begin
                clk_cnt <= clk_cnt + 1;
            end
        end else begin
            clk_cnt <= 0;
            sclk <= CPOL;
        end
    end

    // 主状态机
    localparam IDLE = 2'b00;
    localparam TRANSFER = 2'b01;
    localparam DONE_ST = 2'b10;

    reg [1:0] state;
    wire sclk_edge = (clk_cnt == HALF_DIV - 1);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            cs_n <= 1'b1;
            active <= 1'b0;
            done <= 1'b0;
            bit_cnt <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 1'b0;
                    if (start) begin
                        state <= TRANSFER;
                        cs_n <= 1'b0;
                        active <= 1'b1;
                        tx_reg <= tx_data;
                        bit_cnt <= DATA_WIDTH;
                    end
                end
                TRANSFER: begin
                    if (sclk_edge) begin
                        if (!sclk) begin
                            // 下降沿：采样 MISO
                            rx_reg <= {rx_reg[DATA_WIDTH-2:0], miso};
                            bit_cnt <= bit_cnt - 1;
                            if (bit_cnt == 1) begin
                                state <= DONE_ST;
                                active <= 1'b0;
                            end
                        end else begin
                            // 上升沿：移位 MOSI
                            tx_reg <= {tx_reg[DATA_WIDTH-2:0], 1'b0};
                        end
                    end
                end
                DONE_ST: begin
                    cs_n <= 1'b1;
                    rx_data <= rx_reg;
                    done <= 1'b1;
                    state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end

endmodule
```

### SPI 从机
```verilog
module spi_slave #(
    parameter CPOL = 0,
    parameter CPHA = 0,
    parameter DATA_WIDTH = 8
)(
    input                       clk,
    input                       rst_n,
    // 用户接口
    input  [DATA_WIDTH-1:0]     tx_data,
    output reg [DATA_WIDTH-1:0] rx_data,
    output reg                  rx_valid,
    // SPI 接口
    input                       sclk,
    input                       mosi,
    output reg                  miso,
    input                       cs_n
);

    reg [DATA_WIDTH-1:0] tx_reg;
    reg [DATA_WIDTH-1:0] rx_reg;
    reg [3:0] bit_cnt;
    reg sclk_prev;

    wire sclk_rising = (sclk && !sclk_prev);
    wire sclk_falling = (!sclk && sclk_prev);

    // 时钟边沿检测
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            sclk_prev <= CPOL;
        else
            sclk_prev <= sclk;
    end

    // 数据传输
    wire sample_edge = CPHA ? (CPOL ? sclk_falling : sclk_rising)
                            : (CPOL ? sclk_rising : sclk_falling);
    wire shift_edge = CPHA ? (CPOL ? sclk_rising : sclk_falling)
                           : (CPOL ? sclk_falling : sclk_rising);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_reg <= 0;
            rx_reg <= 0;
            bit_cnt <= 0;
            rx_valid <= 0;
            miso <= 0;
        end else begin
            rx_valid <= 0;

            if (cs_n) begin
                tx_reg <= tx_data;
                bit_cnt <= 0;
            end else begin
                if (sample_edge) begin
                    rx_reg <= {rx_reg[DATA_WIDTH-2:0], mosi};
                    bit_cnt <= bit_cnt + 1;
                    if (bit_cnt == DATA_WIDTH - 1) begin
                        rx_data <= {rx_reg[DATA_WIDTH-2:0], mosi};
                        rx_valid <= 1;
                    end
                end
                if (shift_edge) begin
                    miso <= tx_reg[DATA_WIDTH-1];
                    tx_reg <= {tx_reg[DATA_WIDTH-2:0], 1'b0};
                end
            end
        end
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| CPOL/CPHA 不匹配 | 数据错误 | 主从模式一致 |
| CS_N 未同步 | 亚稳态 | CS_N 同步到本地时钟 |
| 时钟分频不足 | 数据不稳定 | 确保建立/保持时间 |
| MSB/LSB 顺序不一致 | 数据错位 | 统一传输顺序 |

## 验证检查清单

- [ ] 主从 CPOL/CPHA 一致
- [ ] 数据正确传输 (环回测试)
- [ ] CS_N 时序正确
- [ ] 连续传输不丢数据
