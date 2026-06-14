---
name: "verilog-fsm-design"
version: "1.0.0"
description: "FSM 设计详解 - 两段式、One-Hot、序列检测器、UART 状态机"
author: "SuperRTL Team"
tags: ["fsm", "state-machine", "one-hot", "sequence-detector", "uart"]
triggers: ["fsm", "state machine", "sequence", "protocol", "状态机", "序列检测"]
---

# FSM 设计详解

## 概述

有限状态机 (FSM) 是数字电路设计中最常用的模式之一。本文档详细介绍两段式 FSM 设计、One-Hot 编码、序列检测器和 UART 状态机等实际应用。

## 设计要点

### 1. 编码风格 (两段式推荐)
- 第一段：状态寄存器 (时序逻辑)
- 第二段：下一状态和输出 (组合逻辑)

### 2. 状态编码
- 二进制编码：节省资源，适合状态少
- 格雷码：相邻状态只变化 1 位
- One-Hot：每个状态 1 位，FPGA 高效

### 3. 模板结构
```verilog
// 状态定义
localparam IDLE = 3'b001;
localparam S1   = 3'b010;
localparam S2   = 3'b100;

// 状态寄存器
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end

// 下一状态逻辑 (组合)
always @(*) begin
    next_state = state;
    case (state)
        IDLE: if (start) next_state = S1;
        S1:   if (done)  next_state = S2;
        S2:   if (finish) next_state = IDLE;
        default: next_state = IDLE;
    endcase
end

// 输出逻辑 (组合或时序)
always @(*) begin
    out_valid = (state == S2);
end
```

## 代码模板

### 序列检测器 (检测 1011)
```verilog
module sequence_detector (
    input      clk,
    input      rst_n,
    input      in,
    output reg detect
);
    localparam IDLE = 3'b000;
    localparam S1   = 3'b001;
    localparam S2   = 3'b010;
    localparam S3   = 3'b011;
    localparam S4   = 3'b100;

    reg [2:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE: next_state = in ? S1 : IDLE;
            S1:   next_state = in ? S2 : IDLE;
            S2:   next_state = in ? S2 : S3;
            S3:   next_state = in ? S4 : IDLE;
            S4:   next_state = in ? S1 : IDLE;
            default: next_state = IDLE;
        endcase
    end

    assign detect = (state == S4);
endmodule
```

### UART 接收状态机
```verilog
module uart_rx_fsm (
    input            clk,
    input            rst_n,
    input            rx,
    output reg [7:0] data,
    output reg       done
);
    localparam IDLE  = 3'b000;
    localparam START = 3'b001;
    localparam DATA  = 3'b010;
    localparam STOP  = 3'b011;

    reg [2:0] state, next_state;
    reg [3:0] bit_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            bit_cnt <= 4'b0;
        end else begin
            state <= next_state;
            if (state == DATA)
                bit_cnt <= bit_cnt + 1'b1;
            else
                bit_cnt <= 4'b0;
        end
    end

    always @(*) begin
        next_state = state;
        case (state)
            IDLE:  if (!rx) next_state = START;
            START: next_state = DATA;
            DATA:  if (bit_cnt == 7) next_state = STOP;
            STOP:  next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    always @(*) begin
        done = (state == STOP);
    end
endmodule
```

### One-Hot 状态机模板
```verilog
module fsm_onehot (
    input      clk,
    input      rst_n,
    input      req,
    output     grant
);
    localparam [3:0] IDLE = 4'b0001;
    localparam [3:0] REQ  = 4'b0010;
    localparam [3:0] ACK  = 4'b0100;
    localparam [3:0] DONE = 4'b1000;

    reg [3:0] state, next_state;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end

    always @(*) begin
        next_state = IDLE;
        case (1'b1)
            state[IDLE]: next_state = req ? REQ : IDLE;
            state[REQ]:  next_state = ACK;
            state[ACK]:  next_state = DONE;
            state[DONE]: next_state = IDLE;
            default:     next_state = IDLE;
        endcase
    end

    assign grant = state[ACK];
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 缺少 default | Latch/综合警告 | 始终添加 default |
| 状态不全 | Latch | case 覆盖所有状态 |
| 组合输出无寄存器 | 输出毛刺 | 输出用寄存器 |
| 异步复位冲突 | 状态不确定 | 统一复位策略 |

## 验证检查清单

- [ ] 所有状态转换正确
- [ ] 复位回到初始状态
- [ ] 死循环检测
- [ ] 输出时序正确
