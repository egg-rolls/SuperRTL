---
name: "verilog-fifo-async"
version: "1.0.0"
description: "异步 FIFO 设计 - 格雷码同步、跨时钟域数据传输"
author: "SuperRTL Team"
tags: ["fifo", "asynchronous", "cdc", "gray-code", "cross-clock"]
triggers: ["async fifo", "asynchronous fifo", "异步fifo", "跨时钟fifo"]
---

# 异步 FIFO 设计

## 概述

异步 FIFO 用于跨时钟域数据传输，读写时钟不同。使用格雷码同步指针，避免亚稳态导致的数据错误。

## 设计要点

### 1. 核心挑战
- 读写时钟不同域
- 指针需要跨时钟域同步
- 使用格雷码避免同步错误

### 2. 格雷码优势
- 相邻编码只变化 1 位
- 同步器采样错误时只错 1 位
- 错误可检测

### 3. 空满判断
- 写指针同步到读时钟域判断空
- 读指针同步到写时钟域判断满

### 4. 架构
```
wr_clk ---> | Write   | ---> |  RAM    | ---> | Read   | ---> rd_clk
           | Pointer  |     | (async) |     | Pointer|
              |                            ^
              v                            |
        +---------+                   +---------+
        | Gray    |                   | Gray    |
        | Encode  |                   | Decode  |
        +---------+                   +---------+
              |                            ^
              v                            |
        +---------+                   +---------+
        | 2FF     |                   | 2FF     |
        | Sync    |                   | Sync    |
        +---------+                   +---------+
```

## 代码模板

### 标准异步 FIFO
```verilog
module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH    = 16
)(
    input                    wr_clk,
    input                    wr_rst_n,
    input                    rd_clk,
    input                    rd_rst_n,
    input                    wr_en,
    input  [DATA_WIDTH-1:0]  wdata,
    input                    rd_en,
    output [DATA_WIDTH-1:0]  rdata,
    output                   full,
    output                   empty
);
    localparam PTR_WIDTH = $clog2(DEPTH) + 1;

    // RAM
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // 写指针 (二进制)
    reg [PTR_WIDTH-1:0] wr_ptr_bin;
    reg [PTR_WIDTH-1:0] wr_ptr_gray;

    // 读指针 (二进制)
    reg [PTR_WIDTH-1:0] rd_ptr_bin;
    reg [PTR_WIDTH-1:0] rd_ptr_gray;

    // 同步后的指针
    reg [PTR_WIDTH-1:0] wr_ptr_sync;
    reg [PTR_WIDTH-1:0] rd_ptr_sync;

    // 指针同步 (2 级触发器)
    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n)
            wr_ptr_sync <= 0;
        else
            wr_ptr_sync <= wr_ptr_gray;
    end

    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n)
            rd_ptr_sync <= 0;
        else
            rd_ptr_sync <= rd_ptr_gray;
    end

    // 空满判断
    assign full  = (wr_ptr_gray[PTR_WIDTH-1] != rd_ptr_sync[PTR_WIDTH-1]) &&
                   (wr_ptr_gray[PTR_WIDTH-2:0] == rd_ptr_sync[PTR_WIDTH-2:0]);
    assign empty = (wr_ptr_sync == rd_ptr_gray);

    // 写指针更新
    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            wr_ptr_bin <= 0;
            wr_ptr_gray <= 0;
        end else if (wr_en && !full) begin
            mem[wr_ptr_bin[PTR_WIDTH-2:0]] <= wdata;
            wr_ptr_bin <= wr_ptr_bin + 1;
            wr_ptr_gray <= bin2gray(wr_ptr_bin + 1);
        end
    end

    // 读指针更新
    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            rd_ptr_bin <= 0;
            rd_ptr_gray <= 0;
        end else if (rd_en && !empty) begin
            rd_ptr_bin <= rd_ptr_bin + 1;
            rd_ptr_gray <= bin2gray(rd_ptr_bin + 1);
        end
    end

    // 读数据
    reg [DATA_WIDTH-1:0] rdata_reg;
    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n)
            rdata_reg <= 0;
        else if (rd_en && !empty)
            rdata_reg <= mem[rd_ptr_bin[PTR_WIDTH-2:0]];
    end
    assign rdata = rdata_reg;

    // 二进制转格雷码函数
    function [PTR_WIDTH-1:0] bin2gray;
        input [PTR_WIDTH-1:0] bin;
        begin
            bin2gray = (bin >> 1) ^ bin;
        end
    endfunction
endmodule
```

### 异步 FIFO (简化版)
```verilog
module async_fifo_simple #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH    = 16
)(
    input                    wr_clk,
    input                    wr_rst_n,
    input                    rd_clk,
    input                    rd_rst_n,
    input                    wr_en,
    input  [DATA_WIDTH-1:0]  wdata,
    input                    rd_en,
    output [DATA_WIDTH-1:0]  rdata,
    output                   full,
    output                   empty
);
    localparam ADDR_WIDTH = $clog2(DEPTH);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [ADDR_WIDTH:0] wr_ptr;
    reg [ADDR_WIDTH:0] rd_ptr;

    reg [ADDR_WIDTH:0] wr_ptr_sync1, wr_ptr_sync2;
    reg [ADDR_WIDTH:0] rd_ptr_sync1, rd_ptr_sync2;

    // 指针同步
    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n) begin
            rd_ptr_sync1 <= 0;
            rd_ptr_sync2 <= 0;
        end else begin
            rd_ptr_sync1 <= rd_ptr;
            rd_ptr_sync2 <= rd_ptr_sync1;
        end
    end

    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n) begin
            wr_ptr_sync1 <= 0;
            wr_ptr_sync2 <= 0;
        end else begin
            wr_ptr_sync1 <= wr_ptr;
            wr_ptr_sync2 <= wr_ptr_sync1;
        end
    end

    assign full  = (wr_ptr[ADDR_WIDTH] != rd_ptr_sync2[ADDR_WIDTH]) &&
                   (wr_ptr[ADDR_WIDTH-1:0] == rd_ptr_sync2[ADDR_WIDTH-1:0]);
    assign empty = (wr_ptr_sync2 == rd_ptr);

    always @(posedge wr_clk or negedge wr_rst_n) begin
        if (!wr_rst_n)
            wr_ptr <= 0;
        else if (wr_en && !full) begin
            mem[wr_ptr[ADDR_WIDTH-1:0]] <= wdata;
            wr_ptr <= wr_ptr + 1;
        end
    end

    always @(posedge rd_clk or negedge rd_rst_n) begin
        if (!rd_rst_n)
            rd_ptr <= 0;
        else if (rd_en && !empty) begin
            rd_ptr <= rd_ptr + 1;
        end
    end

    assign rdata = mem[rd_ptr[ADDR_WIDTH-1:0]];
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 二进制指针跨 CDC | 亚稳态、数据错误 | 使用格雷码 |
| 同步级数不足 | 亚稳态 | 至少 2 级 |
| 满判断错误 | 数据覆盖 | 指针同步到写时钟 |
| 空判断错误 | 读空数据 | 指针同步到读时钟 |
| 深度非 2^n | 满空判断复杂 | 建议使用 2^n 深度 |

## 验证检查清单

- [ ] 跨时钟域数据不丢失
- [ ] 满/空标志正确
- [ ] 无数据错位
- [ ] 亚稳态处理
- [ ] 背靠背读写
