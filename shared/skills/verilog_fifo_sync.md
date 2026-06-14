---
name: "verilog-fifo-sync"
version: "1.0.0"
description: "同步 FIFO 设计 - 标准同步 FIFO、带计数器 FIFO"
author: "SuperRTL Team"
tags: ["fifo", "synchronous", "buffer", "queue"]
triggers: ["sync fifo", "synchronous fifo", "同步fifo", "同步缓冲"]
---

# 同步 FIFO 设计

## 概述

同步 FIFO 是数据缓冲的基本结构，读写时钟相同，用于数据跨周期传递和模块间数据缓冲。

## 设计要点

### 1. 核心概念
- 读写时钟相同 (同步)
- 读写指针比较判断空满
- 指针宽度 = log2(深度) + 1 (需要额外 1 位判断回绕)

### 2. 空满判断
- 空：读写指针相等
- 满：高位不同，其余位相等

### 3. 架构
```
        +---------+     +---------+     +---------+
   ---> |  RAM    | ---> |  Read   | ---> |  Output |
        |  (sync) |     |  Logic  |     | Register|
        +---------+     +---------+     +---------+
             ^
             |
   +--------+--------+
   |  Write Logic    |
   |  Write Pointer  |
   +-----------------+
```

## 代码模板

### 标准同步 FIFO
```verilog
module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH     = 16,
    parameter PTR_WIDTH = 5  // log2(DEPTH) + 1
)(
    input                    clk,
    input                    rst_n,
    input                    wr_en,
    input  [DATA_WIDTH-1:0]  wdata,
    input                    rd_en,
    output [DATA_WIDTH-1:0]  rdata,
    output                   full,
    output                   empty
);
    // RAM
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // 指针
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;

    // 空满信号
    assign full  = (wr_ptr[PTR_WIDTH-1] != rd_ptr[PTR_WIDTH-1]) &&
                   (wr_ptr[PTR_WIDTH-2:0] == rd_ptr[PTR_WIDTH-2:0]);
    assign empty = (wr_ptr == rd_ptr);

    // 写逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= {PTR_WIDTH{1'b0}};
        end else if (wr_en && !full) begin
            mem[wr_ptr[PTR_WIDTH-2:0]] <= wdata;
            wr_ptr <= wr_ptr + 1'b1;
        end
    end

    // 读逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rd_ptr <= {PTR_WIDTH{1'b0}};
        end else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 1'b1;
        end
    end

    // 读数据
    assign rdata = mem[rd_ptr[PTR_WIDTH-2:0]];
endmodule
```

### 带计数器的 FIFO
```verilog
module sync_fifo_with_count #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH     = 16
)(
    input                    clk,
    input                    rst_n,
    input                    wr_en,
    input  [DATA_WIDTH-1:0]  wdata,
    input                    rd_en,
    output [DATA_WIDTH-1:0]  rdata,
    output                   full,
    output                   empty,
    output [$clog2(DEPTH):0] count
);
    localparam PTR_WIDTH = $clog2(DEPTH) + 1;

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;

    assign full  = (wr_ptr[PTR_WIDTH-1] != rd_ptr[PTR_WIDTH-1]) &&
                   (wr_ptr[PTR_WIDTH-2:0] == rd_ptr[PTR_WIDTH-2:0]);
    assign empty = (wr_ptr == rd_ptr);
    assign count = wr_ptr - rd_ptr;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            wr_ptr <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr[PTR_WIDTH-2:0]] <= wdata;
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

    assign rdata = mem[rd_ptr[PTR_WIDTH-2:0]];
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
