---
name: "verilog-fir-filter"
version: "1.0.0"
description: "FIR 滤波器设计 - 流水线结构、加法树、饱和处理"
author: "SuperRTL Team"
tags: ["fir", "filter", "dsp", "pipeline", "signal-processing"]
triggers: ["fir", "filter", "滤波器", "卷积", "抽头", "信号处理"]
---

# FIR 滤波器设计

## 概述

FIR (有限脉冲响应) 滤波器是数字信号处理的基础模块。本文档介绍流水线结构、加法树优化和饱和处理等关键设计技术。

## 设计要点

### 1. FIR 滤波器基本原理
- N 阶 FIR 有 N+1 个系数
- 输出 y[n] = Σ(h[i] * x[n-i]), i=0~N-1
- 直接型结构：移位寄存器 + 乘法器阵列 + 加法器树

### 2. 位宽计算
- 输入 x[n]: DATA_WIDTH 位 (有符号)
- 系数 h[i]: COEF_WIDTH 位 (有符号)
- 乘积: DATA_WIDTH + COEF_WIDTH 位
- 累加和: DATA_WIDTH + COEF_WIDTH + log2(N) 位
- 输出: OUT_WIDTH 位 (需饱和或截断)

### 3. 流水线结构

**最低要求：2 级流水线**
- 第 1 级：乘法 (输入与系数相乘，结果寄存)
- 第 2 级：累加 (乘法结果相加，结果寄存)

**优化结构：4 级流水线**
- 第 1 级：移位寄存器更新 + 乘法
- 第 2 级：第 1 级加法树 (两两相加)
- 第 3 级：第 2 级加法树
- 第 4 级：最终累加 + 饱和处理

### 4. 加法树 vs 串行累加

**串行累加 (不推荐):**
```verilog
// 8 个乘积串行相加，延迟太大
reg signed [18:0] acc;
always @(*) begin
    acc = 0;
    for(i=0; i<8; i=i+1)
        acc = acc + mult[i];
end
```

**加法树 (推荐):**
```verilog
// 第 1 级：4 个加法 (17 位)
add1[0] = mult[0] + mult[1];
add1[1] = mult[2] + mult[3];
add1[2] = mult[4] + mult[5];
add1[3] = mult[6] + mult[7];

// 第 2 级：2 个加法 (18 位)
add2[0] = add1[0] + add1[1];
add2[1] = add1[2] + add1[3];

// 第 3 级：1 个加法 (19 位)
sum = add2[0] + add2[1];
```

### 5. 饱和处理

```verilog
function signed [OUT_WIDTH-1:0] saturate;
    input signed [DATA_WIDTH+COEF_WIDTH+log2(N)-1:0] value;
    localparam MAX = (1 << (OUT_WIDTH-1)) - 1;
    localparam MIN = -(1 << (OUT_WIDTH-1));
begin
    if (value > MAX) saturate = MAX;
    else if (value < MIN) saturate = MIN;
    else saturate = value[OUT_WIDTH-1:0];
end
endfunction
```

### 6. 有效信号流水线

```verilog
reg [PIPELINE_DEPTH-1:0] valid_dly;
// 移位使能
valid_dly <= {valid_dly[PIPELINE_DEPTH-2:0], valid_in};

// 每级使用 valid_dly[i] 作为使能
```

## 代码模板

### 完整 FIR 代码结构
```verilog
module fir_8tap #(
    parameter DATA_WIDTH = 8,
    parameter COEF_WIDTH = 8,
    parameter OUT_WIDTH = 16,
    parameter H0 = 1, H1 = 2, H2 = 3, H3 = 4,
    H4 = 4, H5 = 3, H6 = 2, H7 = 1
)(
    input                        clk,
    input                        rst_n,
    input                        valid_in,
    input  signed [DATA_WIDTH-1:0] din,
    output                       valid_out,
    output signed [OUT_WIDTH-1:0] dout
);

    // === 系数定义 ===
    wire signed [COEF_WIDTH-1:0] coeff [0:7];
    assign coeff[0] = H0;
    assign coeff[1] = H1;
    assign coeff[2] = H2;
    assign coeff[3] = H3;
    assign coeff[4] = H4;
    assign coeff[5] = H5;
    assign coeff[6] = H6;
    assign coeff[7] = H7;

    // === 移位寄存器 (第 1 级) ===
    reg signed [DATA_WIDTH-1:0] shift_reg [0:7];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integer i;
            for (i = 0; i < 8; i = i + 1)
                shift_reg[i] <= 0;
        end else if (valid_in) begin
            shift_reg[0] <= din;
            shift_reg[1] <= shift_reg[0];
            shift_reg[2] <= shift_reg[1];
            shift_reg[3] <= shift_reg[2];
            shift_reg[4] <= shift_reg[3];
            shift_reg[5] <= shift_reg[4];
            shift_reg[6] <= shift_reg[5];
            shift_reg[7] <= shift_reg[6];
        end
    end

    // === 乘法结果寄存 (第 2 级) ===
    reg signed [DATA_WIDTH+COEF_WIDTH-1:0] mult_reg [0:7];
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            integer i;
            for (i = 0; i < 8; i = i + 1)
                mult_reg[i] <= 0;
        end else begin
            mult_reg[0] <= shift_reg[0] * coeff[0];
            mult_reg[1] <= shift_reg[1] * coeff[1];
            mult_reg[2] <= shift_reg[2] * coeff[2];
            mult_reg[3] <= shift_reg[3] * coeff[3];
            mult_reg[4] <= shift_reg[4] * coeff[4];
            mult_reg[5] <= shift_reg[5] * coeff[5];
            mult_reg[6] <= shift_reg[6] * coeff[6];
            mult_reg[7] <= shift_reg[7] * coeff[7];
        end
    end

    // === 加法树 (第 3-4 级) ===
    reg signed [DATA_WIDTH+COEF_WIDTH:0] add_stage1 [0:3];
    reg signed [DATA_WIDTH+COEF_WIDTH+1:0] add_stage2 [0:1];
    reg signed [DATA_WIDTH+COEF_WIDTH+2:0] sum_stage3;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            add_stage1[0] <= 0; add_stage1[1] <= 0;
            add_stage1[2] <= 0; add_stage1[3] <= 0;
            add_stage2[0] <= 0; add_stage2[1] <= 0;
            sum_stage3 <= 0;
        end else begin
            add_stage1[0] <= mult_reg[0] + mult_reg[1];
            add_stage1[1] <= mult_reg[2] + mult_reg[3];
            add_stage1[2] <= mult_reg[4] + mult_reg[5];
            add_stage1[3] <= mult_reg[6] + mult_reg[7];
            add_stage2[0] <= add_stage1[0] + add_stage1[1];
            add_stage2[1] <= add_stage1[2] + add_stage1[3];
            sum_stage3 <= add_stage2[0] + add_stage2[1];
        end
    end

    // === 有效信号流水线 ===
    reg [3:0] valid_dly;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            valid_dly <= 0;
        else
            valid_dly <= {valid_dly[2:0], valid_in};
    end
    assign valid_out = valid_dly[3];

    // === 饱和处理 ===
    wire signed [OUT_WIDTH-1:0] dout_sat;
    localparam MAX = (1 << (OUT_WIDTH-1)) - 1;
    localparam MIN = -(1 << (OUT_WIDTH-1));
    assign dout_sat = (sum_stage3 > MAX) ? MAX :
                      (sum_stage3 < MIN) ? MIN :
                      sum_stage3[OUT_WIDTH-1:0];
    assign dout = dout_sat;

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 串行累加 | 时序违例 | 用加法树 |
| 位宽不够 | 溢出 | 扩展位宽 + 饱和 |
| 流水线不断开 | 功能错误 | 有效信号使能 |
| 复位不完整 | 初始值不确定 | 所有寄存器复位 |

## 验证检查清单

- [ ] 冲激响应：输入一个脉冲，检查输出是否等于系数
- [ ] 线性叠加：两个输出之和等于和的输出
- [ ] 饱和测试：输入大幅值，检查输出是否饱和
- [ ] 流水线延迟：valid_out 相对于 valid_in 延迟 N 拍
