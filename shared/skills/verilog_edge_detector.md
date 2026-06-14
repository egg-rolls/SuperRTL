---
name: "verilog-edge-detector"
version: "1.0.0"
description: "边沿检测设计 - 上升沿、下降沿、双沿检测"
author: "SuperRTL Team"
tags: ["edge", "detector", "trigger", "interrupt"]
triggers: ["edge", "detector", "边沿", "检测", "trigger"]
---

# 边沿检测设计

## 概述

边沿检测用于检测信号的上升沿或下降沿，常用于中断触发、使能信号生成等场景。

## 代码模板

### 上升沿检测
```verilog
module rising_edge_detector (
    input  clk,
    input  rst_n,
    input  signal_in,
    output rising_edge
);

    reg signal_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            signal_prev <= 0;
        else
            signal_prev <= signal_in;
    end

    assign rising_edge = (signal_in && !signal_prev);

endmodule
```

### 下降沿检测
```verilog
module falling_edge_detector (
    input  clk,
    input  rst_n,
    input  signal_in,
    output falling_edge
);

    reg signal_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            signal_prev <= 1;
        else
            signal_prev <= signal_in;
    end

    assign falling_edge = (!signal_in && signal_prev);

endmodule
```

### 双沿检测
```verilog
module dual_edge_detector (
    input  clk,
    input  rst_n,
    input  signal_in,
    output any_edge
);

    reg signal_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            signal_prev <= 0;
        else
            signal_prev <= signal_in;
    end

    assign any_edge = (signal_in != signal_prev);

endmodule
```

### 可配置边沿检测
```verilog
module edge_detector #(
    parameter WIDTH = 1
)(
    input              clk,
    input              rst_n,
    input  [WIDTH-1:0] signal_in,
    output [WIDTH-1:0] rising_edge,
    output [WIDTH-1:0] falling_edge,
    output [WIDTH-1:0] any_edge
);

    reg [WIDTH-1:0] signal_prev;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            signal_prev <= 0;
        else
            signal_prev <= signal_in;
    end

    assign rising_edge = (signal_in & ~signal_prev);
    assign falling_edge = (~signal_in & signal_prev);
    assign any_edge = (signal_in ^ signal_prev);

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 信号未同步 | 亚稳态 | 先用同步器 |
| 毛刺触发 | 误触发 | 先消抖再检测 |
| 脉冲太窄 | 下游漏检 | 确保脉冲宽度 >= 1 时钟 |

## 验证检查清单

- [ ] 上升沿正确检测
- [ ] 下降沿正确检测
- [ ] 无毛刺误触发
- [ ] 脉冲宽度足够
