---
name: "verilog-i2c"
version: "1.0.0"
description: "I2C 通信接口设计 - 主机、从机、多主机仲裁"
author: "SuperRTL Team"
tags: ["i2c", "serial", "communication", "protocol"]
triggers: ["i2c", "i2c master", "i2c slave", "twi"]
---

# I2C 通信接口设计

## 概述

I2C (Inter-Integrated Circuit) 是两线式串行通信协议，支持多主机多从机。SCL 为时钟线，SDA 为数据线，均为开漏输出需上拉电阻。

## 设计要点

### 1. I2C 信号
| 信号 | 说明 |
|------|------|
| SCL | 时钟线 (主机驱动) |
| SDA | 数据线 (双向，开漏) |

### 2. 传输格式
```
[S] [7-bit地址] [R/W] [ACK] [8-bit数据] [ACK] [P]
起始  从机地址   读/写  应答    数据      应答  停止
```

### 3. 关键时序
- 起始条件：SCL 高时 SDA 下降沿
- 停止条件：SCL 高时 SDA 上升沿
- 数据变化：SCL 低时 SDA 变化
- 数据采样：SCL 高时 SDA 稳定

## 代码模板

### I2C 主机
```verilog
module i2c_master #(
    parameter CLK_FREQ = 50_000_000,
    parameter I2C_FREQ = 100_000
)(
    input        clk,
    input        rst_n,
    // 用户接口
    input        start,
    input        rw,         // 0=写, 1=读
    input  [6:0] addr,
    input  [7:0] wr_data,
    output reg [7:0] rd_data,
    output reg   done,
    output reg   ack_error,
    // I2C 接口
    output reg   scl,
    inout        sda
);

    localparam HALF_PERIOD = CLK_FREQ / (2 * I2C_FREQ);

    reg sda_out;
    reg sda_oe;  // 输出使能
    assign sda = sda_oe ? sda_out : 1'bz;

    reg [15:0] clk_cnt;
    reg [3:0] bit_cnt;
    reg [7:0] shift_reg;

    // 状态机
    localparam IDLE     = 4'd0;
    localparam START    = 4'd1;
    localparam ADDR     = 4'd2;
    localparam RW_BIT   = 4'd3;
    localparam ACK1     = 4'd4;
    localparam DATA     = 4'd5;
    localparam ACK2     = 4'd6;
    localparam STOP     = 4'd7;

    reg [3:0] state;

    // SCL 生成
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            clk_cnt <= 0;
            scl <= 1;
        end else if (state != IDLE) begin
            if (clk_cnt == HALF_PERIOD - 1) begin
                clk_cnt <= 0;
                scl <= ~scl;
            end else begin
                clk_cnt <= clk_cnt + 1;
            end
        end else begin
            clk_cnt <= 0;
            scl <= 1;
        end
    end

    // 主状态机
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            sda_out <= 1;
            sda_oe <= 1;
            done <= 0;
            ack_error <= 0;
        end else begin
            case (state)
                IDLE: begin
                    done <= 0;
                    sda_out <= 1;
                    sda_oe <= 1;
                    if (start) begin
                        state <= START;
                        shift_reg <= {addr, rw};
                    end
                end
                START: begin
                    sda_out <= 0;  // SDA 下降沿
                    sda_oe <= 1;
                    if (scl) state <= ADDR;
                end
                ADDR: begin
                    // 在 SCL 低时移位
                    if (!scl && clk_cnt == 0) begin
                        sda_out <= shift_reg[7];
                        shift_reg <= {shift_reg[6:0], 1'b0};
                        bit_cnt <= bit_cnt + 1;
                        if (bit_cnt == 7) state <= ACK1;
                    end
                end
                ACK1: begin
                    sda_oe <= 0;  // 释放 SDA
                    if (scl && clk_cnt == 0) begin
                        ack_error <= sda;  // 0=ACK, 1=NACK
                        state <= DATA;
                        bit_cnt <= 0;
                    end
                end
                DATA: begin
                    if (!scl && clk_cnt == 0) begin
                        if (rw) begin
                            // 读：采样 SDA
                            sda_oe <= 0;
                        end else begin
                            // 写：驱动 SDA
                            sda_oe <= 1;
                            sda_out <= shift_reg[7];
                        end
                        shift_reg <= {shift_reg[6:0], sda};
                        bit_cnt <= bit_cnt + 1;
                        if (bit_cnt == 7) state <= ACK2;
                    end
                end
                ACK2: begin
                    if (rw) begin
                        sda_oe <= 1;
                        sda_out <= 1;  // NACK
                    end else begin
                        sda_oe <= 0;
                    end
                    if (scl && clk_cnt == 0) begin
                        rd_data <= shift_reg;
                        state <= STOP;
                    end
                end
                STOP: begin
                    sda_oe <= 1;
                    sda_out <= 0;
                    if (!scl && clk_cnt == 0) begin
                        sda_out <= 1;  // SDA 上升沿
                        done <= 1;
                        state <= IDLE;
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
| 无上拉电阻 | SDA/SCL 无法拉高 | 添加 4.7K 上拉 |
| 时钟频率超限 | 通信失败 | 标准模式 100KHz |
| ACK 检测错误 | 数据丢失 | 检查 ACK/NACK |
| 多主机冲突 | 总线冲突 | 实现仲裁逻辑 |

## 验证检查清单

- [ ] 单字节读写正确
- [ ] 连续传输正确
- [ ] ACK/NACK 处理正确
- [ ] 起始/停止时序正确
