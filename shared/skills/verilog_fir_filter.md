# Verilog FIR滤波器设计Skill

## 触发条件
- 用户请求设计FIR滤波器
- 关键词：FIR、滤波器、卷积、抽头、阶数

## 设计要点

### 1. FIR滤波器基本原理
- N阶FIR有N+1个系数（题目8阶=8个系数）
- 输出 y[n] = Σ(h[i] * x[n-i]), i=0~N-1
- 直接型结构：移位寄存器 + 乘法器阵列 + 加法器树

### 2. 位宽计算
- 输入 x[n]: DATA_WIDTH位（有符号）
- 系数 h[i]: COEF_WIDTH位（有符号）
- 乘积: DATA_WIDTH + COEF_WIDTH 位
- 累加和: DATA_WIDTH + COEF_WIDTH + log2(N) 位
- 输出: OUT_WIDTH位（需饱和或截断）

### 3. 流水线结构（重要！）

**最低要求：2级流水线**
- 第1级：乘法（输入与系数相乘，结果寄存）
- 第2级：累加（乘法结果相加，结果寄存）

**优化结构：4级流水线**
- 第1级：移位寄存器更新 + 乘法
- 第2级：第1级加法树（两两相加）
- 第3级：第2级加法树
- 第4级：最终累加 + 饱和处理

### 4. 加法树 vs 串行累加

**串行累加（不推荐）:**
```verilog
// 8个乘积串行相加，延迟太大
reg signed [18:0] acc;
always @(*) begin
    acc = 0;
    for(i=0; i<8; i=i+1)
        acc = acc + mult[i];
end
```

**加法树（推荐）:**
```verilog
// 第1级：4个加法 (17位)
add1[0] = mult[0] + mult[1];
add1[1] = mult[2] + mult[3];
add1[2] = mult[4] + mult[5];
add1[3] = mult[6] + mult[7];

// 第2级：2个加法 (18位)
add2[0] = add1[0] + add1[1];
add2[1] = add1[2] + add1[3];

// 第3级：1个加法 (19位)
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

// 每级使用valid_dly[i]作为使能
```

## 代码模板

### 完整FIR代码结构
```verilog
module fir_8tap #(
    parameter DATA_WIDTH = 8,
    parameter COEF_WIDTH = 8,
    parameter OUT_WIDTH = 16,
    parameter H0 = 1, H1 = 2, H2 = 3, H3 = 4,
    H4 = 4, H5 = 3, H6 = 2, H7 = 1
)(
    input clk, rst_n, valid_in,
    input signed [DATA_WIDTH-1:0] din,
    output valid_out,
    output signed [OUT_WIDTH-1:0] dout
);

    // === 系数定义 ===
    wire signed [COEF_WIDTH-1:0] coeff [0:7];
    assign coeff[0] = H0; ...

    // === 移位寄存器 (第1级) ===
    reg signed [DATA_WIDTH-1:0] shift_reg [0:7];
    wire signed [DATA_WIDTH-1:0] shift_next [0:7];
    assign shift_next[0] = din;
    assign shift_next[i] = shift_reg[i-1]; ...

    // === 乘法结果寄存 (第2级) ===
    reg signed [DATA_WIDTH+COEF_WIDTH-1:0] mult_reg [0:7];

    // === 加法树 (第3-4级) ===
    reg signed [DATA_WIDTH+COEF_WIDTH:0] add_stage1 [0:3];
    reg signed [DATA_WIDTH+COEF_WIDTH+1:0] add_stage2 [0:1];
    reg signed [DATA_WIDTH+COEF_WIDTH+2:0] sum_stage3;

    // === 有效信号流水线 ===
    reg [3:0] valid_dly;

    // === 饱和处理 ===
    wire signed [OUT_WIDTH-1:0] dout_sat;
    assign dout_sat = ...;

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 串行累加 | 时序违例 | 用加法树 |
| 位宽不够 | 溢出 | 扩展位宽+饱和 |
| 流水线不断开 | 功能错误 | 有效信号使能 |
| 复位不完整 | 初始值不确定 | 所有寄存器复位 |

## 验证要点

1. 冲激响应：输入一个脉冲，检查输出是否等于系数
2. 线性叠加：两个输出之和等于和的输出
3. 饱和测试：输入大幅值，检查输出是否饱和
4. 流水线延迟：valid_out相对于valid_in延迟N拍
