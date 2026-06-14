---
name: "verilog-axi-lite"
version: "1.0.0"
description: "AXI-Lite 接口设计 - 寄存器映射、从机实现"
author: "SuperRTL Team"
tags: ["axi", "axi-lite", "bus", "interface"]
triggers: ["axi", "axi-lite", "axilite", "bus interface"]
---

# AXI-Lite 接口设计

## 概述

AXI-Lite 是 AXI4 的简化版本，用于寄存器访问和低带宽外设接口。本文档介绍 AXI-Lite 从机的实现。

## 设计要点

### 1. AXI-Lite 信号
| 通道 | 信号 | 说明 |
|------|------|------|
| 写地址 | AWADDR, AWVALID, AWREADY | 写地址握手 |
| 写数据 | WDATA, WSTRB, WVALID, WREADY | 写数据握手 |
| 写响应 | BRESP, BVALID, BREADY | 写响应握手 |
| 读地址 | ARADDR, ARVALID, ARREADY | 读地址握手 |
| 读数据 | RDATA, RRESP, RVALID, RREADY | 读数据握手 |

### 2. 握手协议
- VALID 和 READY 同时为高时完成传输
- VALID 一旦置高，READY 之前不能撤销
- READY 可以在 VALID 之前或之后置高

### 3. 响应编码
| RRESP/BRESP | 含义 |
|-------------|------|
| 2'b00 | OKAY |
| 2'b01 | EXOKAY |
| 2'b10 | SLVERR |
| 2'b11 | DECERR |

## 代码模板

### AXI-Lite 从机（寄存器文件）
```verilog
module axi_lite_slave #(
    parameter ADDR_WIDTH = 8,
    parameter DATA_WIDTH = 32,
    parameter REG_COUNT = 16
)(
    input                       clk,
    input                       rst_n,
    // AXI-Lite 写地址通道
    input  [ADDR_WIDTH-1:0]     s_axi_awaddr,
    input                       s_axi_awvalid,
    output reg                  s_axi_awready,
    // AXI-Lite 写数据通道
    input  [DATA_WIDTH-1:0]     s_axi_wdata,
    input  [DATA_WIDTH/8-1:0]   s_axi_wstrb,
    input                       s_axi_wvalid,
    output reg                  s_axi_wready,
    // AXI-Lite 写响应通道
    output reg [1:0]            s_axi_bresp,
    output reg                  s_axi_bvalid,
    input                       s_axi_bready,
    // AXI-Lite 读地址通道
    input  [ADDR_WIDTH-1:0]     s_axi_araddr,
    input                       s_axi_arvalid,
    output reg                  s_axi_arready,
    // AXI-Lite 读数据通道
    output reg [DATA_WIDTH-1:0] s_axi_rdata,
    output reg [1:0]            s_axi_rresp,
    output reg                  s_axi_rvalid,
    input                       s_axi_rready
);

    // 寄存器文件
    reg [DATA_WIDTH-1:0] regs [0:REG_COUNT-1];

    // 写地址锁存
    reg [ADDR_WIDTH-1:0] aw_addr;
    reg aw_valid;

    // 写地址通道
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_awready <= 0;
            aw_valid <= 0;
        end else begin
            if (s_axi_awvalid && !aw_valid) begin
                s_axi_awready <= 1;
                aw_addr <= s_axi_awaddr;
                aw_valid <= 1;
            end else begin
                s_axi_awready <= 0;
                if (s_axi_wvalid && s_axi_wready)
                    aw_valid <= 0;
            end
        end
    end

    // 写数据通道
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_wready <= 0;
        end else begin
            if (s_axi_wvalid && aw_valid) begin
                s_axi_wready <= 1;
            end else begin
                s_axi_wready <= 0;
            end
        end
    end

    // 写寄存器
    wire wr_en = s_axi_wvalid && s_axi_wready;
    integer i;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < REG_COUNT; i = i + 1)
                regs[i] <= 0;
        end else if (wr_en) begin
            for (i = 0; i < DATA_WIDTH/8; i = i + 1) begin
                if (s_axi_wstrb[i])
                    regs[aw_addr[ADDR_WIDTH-1:2]][i*8 +: 8] <= s_axi_wdata[i*8 +: 8];
            end
        end
    end

    // 写响应通道
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_bvalid <= 0;
            s_axi_bresp <= 0;
        end else begin
            if (wr_en) begin
                s_axi_bvalid <= 1;
                s_axi_bresp <= 2'b00;  // OKAY
            end else if (s_axi_bready) begin
                s_axi_bvalid <= 0;
            end
        end
    end

    // 读地址通道
    reg [ADDR_WIDTH-1:0] ar_addr;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_arready <= 0;
        end else begin
            if (s_axi_arvalid && !s_axi_rvalid) begin
                s_axi_arready <= 1;
                ar_addr <= s_axi_araddr;
            end else begin
                s_axi_arready <= 0;
            end
        end
    end

    // 读数据通道
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            s_axi_rvalid <= 0;
            s_axi_rdata <= 0;
            s_axi_rresp <= 0;
        end else begin
            if (s_axi_arvalid && s_axi_arready) begin
                s_axi_rvalid <= 1;
                s_axi_rdata <= regs[ar_addr[ADDR_WIDTH-1:2]];
                s_axi_rresp <= 2'b00;  // OKAY
            end else if (s_axi_rready) begin
                s_axi_rvalid <= 0;
            end
        end
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| VALID/READY 死锁 | 总线挂起 | 确保无循环依赖 |
| 地址对齐错误 | 数据错误 | 地址按 4 字节对齐 |
| WSTRB 未处理 | 部分写失败 | 按字节使能写入 |
| 响应超时 | 主机卡死 | 添加超时机制 |

## 验证检查清单

- [ ] 单次读写正确
- [ ] 连续读写正确
- [ ] 字节使能正确
- [ ] 响应信号正确
