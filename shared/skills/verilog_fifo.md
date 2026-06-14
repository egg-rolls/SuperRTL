---
name: "verilog-fifo"
version: "1.0.0"
description: "FIFO 设计模式 - 同步/异步 FIFO 设计指南"
author: "SuperRTL Team"
tags: ["fifo", "buffer", "cdc", "design-pattern"]
triggers: ["fifo", "buffer", "缓冲", "队列", "first in first out"]
---

# FIFO 设计模式

## 概述

FIFO (First In First Out) 是数据缓冲的基本结构，广泛用于跨时钟域数据传输和模块间数据缓冲。

## 设计要点

### 1. FIFO 类型
- **同步 FIFO**：读写时钟相同，用于数据缓冲
- **异步 FIFO**：读写时钟不同，用于跨时钟域传输

### 2. 核心设计
- 使用额外一位指针判断满/空状态
- 深度应为 2 的幂次便于综合优化
- 异步 FIFO 需要格雷码同步指针

### 3. 空满判断
- **空**：读写指针相等
- **满**：高位不同，其余位相等

## 代码模板

### 同步 FIFO
```verilog
module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4,
    parameter FIFO_DEPTH = 1 << ADDR_WIDTH
)(
    input  wire                  clk,
    input  wire                  rst_n,
    // 写端口
    input  wire                  wr_en,
    input  wire [DATA_WIDTH-1:0] wr_data,
    output wire                  full,
    // 读端口
    input  wire                  rd_en,
    output wire [DATA_WIDTH-1:0] rd_data,
    output wire                  empty
);

    reg [DATA_WIDTH-1:0] mem [0:FIFO_DEPTH-1];
    reg [ADDR_WIDTH:0]   wr_ptr, rd_ptr;

    assign full  = (wr_ptr - rd_ptr) == FIFO_DEPTH;
    assign empty = (wr_ptr == rd_ptr);
    assign rd_data = mem[rd_ptr[ADDR_WIDTH-1:0]];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr[ADDR_WIDTH-1:0]] <= wr_data;
            wr_ptr <= wr_ptr + 1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= 0;
        end else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 1;
        end
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 指针位宽不足 | 满空判断错误 | 宽度 = log2(深度) + 1 |
| 读写同时满 | 数据覆盖 | 检查 full/empty 后再操作 |
| 组合逻辑读 | 毛刺 | 输出加寄存器 |
| 未处理溢出 | 指针错误 | 满时禁止写入 |

## 验证检查清单

- [ ] 写入后 count 增加
- [ ] 读出后 count 减少
- [ ] 满时 wr_en 无效
- [ ] 空时 rd_en 无效
- [ ] 数据顺序正确 (FIFO 顺序)
