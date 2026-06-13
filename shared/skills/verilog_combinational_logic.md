# Verilog Combinational Logic Design Skill

## 触发条件
- 用户请求设计组合逻辑
- 包含译码器、多路选择器、编码器、比较器等
- 关键词：decoder, multiplexer, encoder, comparator, combinational

## 设计要点

### 1. 编码规范
- 使用 `always @(*)` 或 `always_comb` (SystemVerilog)
- 使用阻塞赋值 `=`
- 一个 always 块驱动一个信号
- 一个信号只在一个 always 块中赋值

### 2. 敏感列表
- 组合逻辑必须包含所有输入信号
- 使用 `*` 或 `*` 自动捕获
- 禁止不完整的敏感列表

### 3. 避免Latch
- 所有 if/case 必须覆盖所有情况
- default 分支必须赋值
- 避免遗漏信号赋值

## 代码模板

### 多路选择器 (Mux)
```verilog
module mux_4to1 #(
    parameter WIDTH = 8
)(
    input  [WIDTH-1:0] d0, d1, d2, d3,
    input  [1:0]       sel,
    output [WIDTH-1:0] y
);
    always @(*) begin
        case (sel)
            2'b00:   y = d0;
            2'b01:   y = d1;
            2'b10:   y = d2;
            2'b11:   y = d3;
            default: y = {WIDTH{1'b0}};  // 必须
        endcase
    end
endmodule
```

### 译码器 (Decoder)
```verilog
module decoder_3to8 (
    input  [2:0]  in,
    input         en,
    output [7:0] out
);
    always @(*) begin
        if (!en) begin
            out = 8'b0;
        end else begin
            case (in)
                3'b000: out = 8'b00000001;
                3'b001: out = 8'b00000010;
                3'b010: out = 8'b00000100;
                3'b011: out = 8'b00001000;
                3'b100: out = 8'b00010000;
                3'b101: out = 8'b00100000;
                3'b110: out = 8'b01000000;
                3'b111: out = 8'b10000000;
                default: out = 8'b0;
            endcase
        end
    end
endmodule
```

### 比较器 (Comparator)
```verilog
module comparator (
    input  [7:0] a, b,
    output       eq,
    output       lt,
    output       gt
);
    assign eq = (a == b);
    assign lt = (a < b);
    assign gt = (a > b);
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 敏感列表不完整 | 仿真与综合不一致 | 使用 `always @(*)` |
| 忘记default | 产生Latch | 始终添加default |
| 阻塞/非阻塞混用 | 产生Latch | 组合逻辑用 `=` |
| 同一个信号多次赋值 | 冲突 | 一个always一个信号 |

## 验证要点
1. 所有输入变化时输出立即变化
2. 无毛刺
3. case覆盖完整
