---
name: "verilog-debouncer"
version: "1.0.0"
description: "按键消抖设计 - 计数器消抖、边沿检测"
author: "SuperRTL Team"
tags: ["debounce", "button", "switch", "input"]
triggers: ["debounce", "消抖", "按键", "button", "switch"]
---

# 按键消抖设计

## 概述

机械按键在按下/释放时会产生 10-20ms 的抖动，需要消抖处理才能得到稳定的信号。

## 设计要点

### 1. 消抖方法
- **延时采样**：等待抖动结束后再采样
- **计数器消抖**：连续 N 次相同才确认变化
- **边沿检测**：检测信号变化并产生单脉冲

### 2. 消抖时间
- 一般机械按键：10-20ms
- 需根据系统时钟计算计数器值

## 代码模板

### 计数器消抖
```verilog
module debouncer #(
    parameter CLK_FREQ = 50_000_000,
    parameter DEBOUNCE_MS = 20
)(
    input      clk,
    input      rst_n,
    input      btn_in,
    output reg btn_out
);

    localparam MAX_CNT = CLK_FREQ / 1000 * DEBOUNCE_MS;
    localparam CNT_WIDTH = $clog2(MAX_CNT);

    reg [CNT_WIDTH-1:0] cnt;
    reg btn_prev;

    wire btn_changed = (btn_in != btn_prev);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 0;
            btn_prev <= 0;
            btn_out <= 0;
        end else begin
            btn_prev <= btn_in;
            if (btn_changed) begin
                cnt <= 0;
            end else if (cnt < MAX_CNT) begin
                cnt <= cnt + 1;
            end else begin
                btn_out <= btn_in;
            end
        end
    end

endmodule
```

### 带边沿检测的消抖
```verilog
module debouncer_edge #(
    parameter CLK_FREQ = 50_000_000,
    parameter DEBOUNCE_MS = 20
)(
    input      clk,
    input      rst_n,
    input      btn_in,
    output     btn_out,
    output     btn_rising,
    output     btn_falling
);

    // 消抖实例
    wire btn_stable;
    debouncer #(
        .CLK_FREQ(CLK_FREQ),
        .DEBOUNCE_MS(DEBOUNCE_MS)
    ) u_debouncer (
        .clk(clk),
        .rst_n(rst_n),
        .btn_in(btn_in),
        .btn_out(btn_stable)
    );

    assign btn_out = btn_stable;

    // 边沿检测
    reg btn_prev;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            btn_prev <= 0;
        else
            btn_prev <= btn_stable;
    end

    assign btn_rising = (btn_stable && !btn_prev);
    assign btn_falling = (!btn_stable && btn_prev);

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 消抖时间太短 | 仍有抖动 | 至少 10ms |
| 消抖时间太长 | 响应迟钝 | 不超过 50ms |
| 未同步输入 | 亚稳态 | 先同步到本地时钟 |

## 验证检查清单

- [ ] 按下后输出稳定
- [ ] 释放后输出稳定
- [ ] 边沿检测正确
- [ ] 响应时间可接受
