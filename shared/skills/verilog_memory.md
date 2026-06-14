---
name: "verilog-memory"
version: "1.0.0"
description: "存储器设计 - RAM/ROM/BRAM 推断模式"
author: "SuperRTL Team"
tags: ["memory", "ram", "rom", "bram", "fpga"]
triggers: ["ram", "rom", "memory", "存储器", "bram", "块RAM"]
---

# 存储器设计

## 概述

存储器是数字系统的核心组件。本文档介绍单端口/双端口 RAM、ROM 以及 FPGA BRAM 推断模式。

## 设计要点

### 1. 存储器类型
| 类型 | 端口 | 特点 | 应用 |
|-----|------|------|-----|
| 单端口 RAM | 1 | 读写共用地址 | 缓冲区 |
| 双端口 RAM | 2 | 独立读写 | FIFO |
| ROM | 1 | 只读 | 查找表 |
| True Dual Port | 2 | 两个独立读写端口 | 共享内存 |

### 2. FPGA BRAM 推断
- 使用 `reg` 数组声明
- 读写在同一 always 块
- 综合工具自动推断为 BRAM

### 3. 初始化
- 使用 `initial` 块 (FPGA)
- 使用 `$readmemh` / `$readmemb` (仿真)

## 代码模板

### 单端口同步 RAM
```verilog
module ram_single_port #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4,
    parameter DEPTH      = 1 << ADDR_WIDTH
)(
    input                    clk,
    input                    wr_en,
    input  [ADDR_WIDTH-1:0]  addr,
    input  [DATA_WIDTH-1:0]  wr_data,
    output reg [DATA_WIDTH-1:0] rd_data
);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    always @(posedge clk) begin
        if (wr_en) begin
            mem[addr] <= wr_data;
        end
        rd_data <= mem[addr];
    end

endmodule
```

### 双端口 RAM (独立读写)
```verilog
module ram_dual_port #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4,
    parameter DEPTH      = 1 << ADDR_WIDTH
)(
    input                    clk,
    // 写端口
    input                    wr_en,
    input  [ADDR_WIDTH-1:0]  wr_addr,
    input  [DATA_WIDTH-1:0]  wr_data,
    // 读端口
    input  [ADDR_WIDTH-1:0]  rd_addr,
    output reg [DATA_WIDTH-1:0] rd_data
);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // 写逻辑
    always @(posedge clk) begin
        if (wr_en) begin
            mem[wr_addr] <= wr_data;
        end
    end

    // 读逻辑
    always @(posedge clk) begin
        rd_data <= mem[rd_addr];
    end

endmodule
```

### ROM (只读存储器)
```verilog
module rom #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4,
    parameter DEPTH      = 1 << ADDR_WIDTH
)(
    input                    clk,
    input  [ADDR_WIDTH-1:0]  addr,
    output reg [DATA_WIDTH-1:0] data
);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // 初始化
    initial begin
        $readmemh("rom_data.hex", mem);
    end

    always @(posedge clk) begin
        data <= mem[addr];
    end

endmodule
```

### 带使能的 BRAM 推断模板
```verilog
module bram_infer #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 10,
    parameter DEPTH      = 1 << ADDR_WIDTH
)(
    input                    clk,
    input                    en,
    input                    wr_en,
    input  [ADDR_WIDTH-1:0]  addr,
    input  [DATA_WIDTH-1:0]  wr_data,
    output reg [DATA_WIDTH-1:0] rd_data
);

    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    always @(posedge clk) begin
        if (en) begin
            if (wr_en) begin
                mem[addr] <= wr_data;
            end
            rd_data <= mem[addr];
        end
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 同一地址读写冲突 | 数据不确定 | 使用读优先/写优先模式 |
| 未初始化 | 随机值 | 使用 initial 或复位 |
| 深度非 2^n | 地址映射复杂 | 建议使用 2^n |
| 异步读写 | 时序问题 | 使用同步设计 |

## 验证检查清单

- [ ] 读写数据正确
- [ ] 地址边界处理
- [ ] 同时读写同地址行为正确
- [ ] 初始化数据正确
