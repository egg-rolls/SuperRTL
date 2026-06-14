---
name: "verilog-fsm"
version: "1.0.0"
description: "FSM 三段式设计模式 - 状态机设计指南"
author: "SuperRTL Team"
tags: ["fsm", "state-machine", "sequential", "design-pattern"]
triggers: ["fsm", "state machine", "状态机", "有限状态机", "finite state machine"]
---

# FSM 设计模式

## 概述

有限状态机 (Finite State Machine) 是数字电路设计中最常用的模式之一。三段式写法将状态机分为状态寄存器、次态逻辑和输出逻辑三部分，便于维护和综合。

## 设计要点

### 1. 三段式结构
- **第一段**：状态寄存器 (时序逻辑) - 存储当前状态
- **第二段**：次态逻辑 (组合逻辑) - 计算下一状态
- **第三段**：输出逻辑 (时序或组合) - 生成输出信号

### 2. 状态编码
- 使用 `parameter` 或 `localparam` 定义状态编码
- 推荐使用 One-Hot 编码 (FPGA) 或二进制编码 (ASIC)

### 3. 设计规范
- 状态机要有 `default` 分支处理异常情况
- 复位后进入明确的初始状态
- 使用 `always @(*)` 或 `always_comb` 编写组合逻辑

## 代码模板

### 三段式 FSM 模板
```verilog
module fsm_template (
    input        clk,
    input        rst_n,
    input        start,
    input        done,
    input  [7:0] data_in,
    output reg [7:0] out
);
    // 状态定义
    localparam IDLE = 2'b00;
    localparam RUN  = 2'b01;
    localparam DONE = 2'b10;

    reg [1:0] current_state, next_state;

    // 1. 状态寄存器 (时序逻辑)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= IDLE;
        else
            current_state <= next_state;
    end

    // 2. 次态逻辑 (组合逻辑)
    always @(*) begin
        case (current_state)
            IDLE: begin
                if (start)
                    next_state = RUN;
                else
                    next_state = IDLE;
            end
            RUN: begin
                if (done)
                    next_state = DONE;
                else
                    next_state = RUN;
            end
            DONE: begin
                next_state = IDLE;
            end
            default: next_state = IDLE;
        endcase
    end

    // 3. 输出逻辑 (时序或组合)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            out <= 0;
        else if (current_state == RUN)
            out <= data_in;
    end
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
