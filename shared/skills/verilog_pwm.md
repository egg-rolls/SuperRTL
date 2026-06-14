---
name: "verilog-pwm"
version: "1.0.0"
description: "PWM 生成器设计 - 占空比可调、多通道"
author: "SuperRTL Team"
tags: ["pwm", "timer", "analog", "control"]
triggers: ["pwm", "pulse width", "占空比", "脉宽调制"]
---

# PWM 生成器设计

## 概述

PWM (Pulse Width Modulation) 通过调节脉冲占空比来控制输出功率，广泛用于电机控制、LED 调光、DAC 等场景。

## 设计要点

### 1. PWM 参数
- **频率**：PWM 输出频率
- **占空比**：高电平时间 / 周期时间
- **分辨率**：占空比调节精度 (位数)

### 2. 计数方式
- **向上计数**：0 → MAX → 0
- **中心对齐**：0 → MAX → 0 (对称，EMI 更低)

## 代码模板

### 基础 PWM
```verilog
module pwm #(
    parameter WIDTH = 8
)(
    input              clk,
    input              rst_n,
    input  [WIDTH-1:0] duty,    // 占空比
    output reg         pwm_out
);

    reg [WIDTH-1:0] cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 0;
        else
            cnt <= cnt + 1;
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pwm_out <= 0;
        else
            pwm_out <= (cnt < duty);
    end

endmodule
```

### 多通道 PWM
```verilog
module pwm_multi_channel #(
    parameter WIDTH = 8,
    parameter CHANNELS = 4
)(
    input                       clk,
    input                       rst_n,
    input  [WIDTH-1:0]          duty [0:CHANNELS-1],
    output reg [CHANNELS-1:0]   pwm_out
);

    reg [WIDTH-1:0] cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            cnt <= 0;
        else
            cnt <= cnt + 1;
    end

    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pwm_out <= 0;
        end else begin
            for (i = 0; i < CHANNELS; i = i + 1)
                pwm_out[i] <= (cnt < duty[i]);
        end
    end

endmodule
```

### 中心对齐 PWM
```verilog
module pwm_center_aligned #(
    parameter WIDTH = 8
)(
    input              clk,
    input              rst_n,
    input  [WIDTH-1:0] duty,
    output reg         pwm_out
);

    reg [WIDTH-1:0] cnt;
    reg direction;  // 0=上, 1=下

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 0;
            direction <= 0;
        end else begin
            if (!direction) begin
                if (cnt == {WIDTH{1'b1}})
                    direction <= 1;
                else
                    cnt <= cnt + 1;
            end else begin
                if (cnt == 0)
                    direction <= 0;
                else
                    cnt <= cnt - 1;
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pwm_out <= 0;
        else
            pwm_out <= (cnt < duty);
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 占空比溢出 | 输出恒高 | 限制 duty <= MAX |
| 频率不对 | 控制失效 | 计算正确的计数范围 |
| 毛刺 | 电机抖动 | 输出加寄存器 |

## 验证检查清单

- [ ] 0% 占空比输出恒低
- [ ] 100% 占空比输出恒高
- [ ] 50% 占空比对称
- [ ] 频率正确
