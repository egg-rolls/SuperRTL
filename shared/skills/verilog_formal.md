---
name: "verilog-formal"
version: "1.0.0"
description: "形式验证设计指南 - SymbiYosys 属性检查、BMC、覆盖验证"
author: "SuperRTL Team"
tags: ["formal", "verification", "bmc", "assert", "symbiyosys", "property"]
triggers: ["formal", "形式验证", "assert", "property", "BMC", "model checking"]
---

# Verilog 形式验证设计指南

## 概述

形式验证使用数学方法证明设计的正确性，而非依赖仿真激励。SymbiYosys 集成了 SMT 求解器，支持：
- **BMC (有界模型检查)**：检查 N 个时钟周期内属性是否成立
- **k-induction**：证明属性在所有可能的执行路径上成立
- **覆盖验证**：检查设计状态空间的可达性

## 设计要点

### 1. 属性声明 (Properties)

使用 `assert`、`assume`、`cover` 三种语句：

| 语句 | 含义 | 用途 |
|------|------|------|
| `assert` | 断言条件必须为真 | 验证设计正确性 |
| `assume` | 假设条件为真 | 约束输入环境 |
| `cover` | 检查条件可达 | 验证测试覆盖率 |

```verilog
// 断言：计数器不会溢出
always @(posedge clk) begin
    assert (count <= 4'hF);
end

// 假设：输入在有效范围内
always @(*) begin
    assume (data_in < 256);
end

// 覆盖：检查所有状态可达
always @(posedge clk) begin
    cover (state == IDLE);
    cover (state == RUNNING);
end
```

### 2. 时序属性

使用 `|=>` (下一个周期) 和 `|->` (当前周期)：

```verilog
// 请求后应答必须在 3 个周期内到来
property req_ack;
    @(posedge clk) req |-> ##[1:3] ack;
endproperty

assert property (req_ack);
```

### 3. 复位属性

```verilog
// 复位后计数器为 0
always @(posedge clk) begin
    if (rst_n == 0) begin
        assert (count == 0);
    end
end
```

### 4. 不变量 (Invariants)

```verilog
// FIFO 满时写指针等于读指针
always @(posedge clk) begin
    if (full)
        assert (wr_ptr == rd_ptr);
end
```

## 代码模板

### 基础 BMC 验证模板

```verilog
module counter_bmc (
    input clk,
    input rst_n,
    input en,
    output reg [3:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 0;
        else if (en)
            count <= count + 1;
    end

    // 形式验证属性
    always @(posedge clk) begin
        // 复位后计数器为 0
        if (!rst_n)
            assert (count == 0);

        // 计数器不会溢出
        assert (count <= 15);

        // 使能时计数器递增
        if (rst_n && en)
            assert (count == $past(count) + 1);
    end
endmodule
```

### FSM 安全性验证

```verilog
module fsm_safety (
    input clk,
    input rst_n,
    input start,
    input done,
    output reg [1:0] state
);
    localparam IDLE = 0, RUN = 1, DONE = 2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else case (state)
            IDLE: if (start) state <= RUN;
            RUN:  if (done)  state <= DONE;
            DONE:            state <= IDLE;
            default:         state <= IDLE;
        endcase
    end

    // 安全性：状态必须是有效值
    always @(posedge clk) begin
        assert (state <= DONE);
    end

    // 活性：DONE 状态可达
    always @(posedge clk) begin
        cover (state == DONE);
    end
endmodule
```

### FIFO 正确性验证

```verilog
module fifo_verify #(
    parameter DEPTH = 8,
    parameter WIDTH = 8
)(
    input clk,
    input rst_n,
    input wr_en,
    input rd_en,
    input [WIDTH-1:0] wr_data,
    output [WIDTH-1:0] rd_data,
    output full,
    output empty
);
    // ... FIFO 实现 ...

    // 属性：满和空不能同时为真
    always @(posedge clk) begin
        assert (!(full && empty));
    end

    // 属性：写入后非空
    always @(posedge clk) begin
        if (wr_en && !full)
            assert (!empty);
    end
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|------|------|----------|
| 只用 `assert` 不用 `assume` | 输入约束不足，产生虚假反例 | 为输入添加合理的 `assume` |
| BMC 深度不足 | 遗漏深层 bug | 增加 depth 或使用 k-induction |
| 组合逻辑中的 `assert` | 无法捕获时序违规 | 使用 `always @(posedge clk)` 包裹 |
| 未处理 `X` 状态 | 仿真和形式验证结果不一致 | 使用 `default` 分支处理所有状态 |
| 过于复杂的属性 | 求解器超时 | 简化属性或分段验证 |

## 验证检查清单

- [ ] 所有输出端口有范围断言
- [ ] FSM 状态值有有效性断言
- [ ] 复位后所有寄存器有初始值断言
- [ ] 关键协议有时序属性覆盖
- [ ] 输入环境有合理的 `assume` 约束
- [ ] 关键状态有 `cover` 覆盖验证
- [ ] BMC 深度足够覆盖最长路径
- [ ] 属性不含组合逻辑回环
