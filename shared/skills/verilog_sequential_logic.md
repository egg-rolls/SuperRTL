# Verilog Sequential Logic Design Skill

## 触发条件
- 用户请求设计时序逻辑
- 包含寄存器、计数器、移位寄存器、分频器
- 关键词：register, counter, shift, flip-flop, sequential

## 设计要点

### 1. 编码规范
- 使用 `always @(posedge clk or negedge rst_n)`
- 使用非阻塞赋值 `<=`
- 异步复位优先于同步操作
- 一个 always 块驱动一个信号

### 2. 复位策略
- 异步复位：`(posedge clk or negedge rst_n)`
- 同步复位：`(posedge clk) if (rst_n)`
- 建议使用异步复位，响应更快

### 3. 时序逻辑模板
```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        // 复位值
    end else begin
        // 逻辑
    end
end
```

## 代码模板

### D触发器 (D Flip-Flop)
```verilog
module dff #(
    parameter WIDTH = 8
)(
    input                clk,
    input                rst_n,
    input                en,
    input  [WIDTH-1:0]  d,
    output reg [WIDTH-1:0]  q
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            q <= {WIDTH{1'b0}};
        end else if (en) begin
            q <= d;
        end
    end
endmodule
```

### 同步计数器
```verilog
module counter #(
    parameter WIDTH = 4,
    parameter MAX = 15
)(
    input        clk,
    input        rst_n,
    input        en,
    output reg [WIDTH-1:0] count,
    output                  overflow
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else if (en) begin
            if (count >= MAX)
                count <= {WIDTH{1'b0}};
            else
                count <= count + 1'b1;
        end
    end
    
    assign overflow = (count == MAX) && en;
endmodule
```

### 移位寄存器
```verilog
module shift_reg #(
    parameter WIDTH = 8
)(
    input                clk,
    input                rst_n,
    input                en,
    input                serial_in,
    output reg [WIDTH-1:0] data
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data <= {WIDTH{1'b0}};
        end else if (en) begin
            data <= {data[WIDTH-2:0], serial_in};
        end
    end
endmodule
```

### 奇数分频
```verilog
module clk_div_odd #(
    parameter DIV = 3  // 奇数分频
)(
    input  clk,
    input  rst_n,
    output reg clk_out
);
    reg [1:0] cnt;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cnt <= 2'b0;
            clk_out <= 1'b0;
        end else begin
            if (cnt == DIV - 1) begin
                cnt <= 2'b0;
                clk_out <= ~clk_out;
            end else begin
                cnt <= cnt + 1'b1;
            end
        end
    end
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 使用阻塞赋值 | 产生组合逻辑 | 时序逻辑用 `<=` |
| 缺少复位 | 上电不确定 | 始终添加复位 |
| 赋值条件不完整 | 产生Latch | 确保所有情况都赋值 |
| 跨时钟域数据 | CDC问题 | 使用同步器 |

## 验证要点
1. 复位后初始值正确
2. 时钟上升沿触发
3. 使能信号正确
4. 溢出/回绕行为正确
