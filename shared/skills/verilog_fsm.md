# FSM 设计模式

## 概述

有限状态机 (Finite State Machine) 是数字电路设计中最常用的模式之一。

## 三段式 FSM 写法

```verilog
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
```

## 注意事项

1. 使用 `parameter` 或 `localparam` 定义状态编码
2. 推荐使用三段式写法，便于维护和综合
3. 状态机要有 `default` 分支处理异常情况
4. 复位后进入明确的初始状态
