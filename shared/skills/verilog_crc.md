---
name: "verilog-crc"
version: "1.0.0"
description: "CRC 校验设计 - CRC-8/16/32，可配置多项式"
author: "SuperRTL Team"
tags: ["crc", "checksum", "error-detection", "communication"]
triggers: ["crc", "checksum", "校验", "error detection"]
---

# CRC 校验设计

## 概述

CRC (Cyclic Redundancy Check) 是常用的数据完整性校验方法。通过多项式除法生成校验码。

## 常用 CRC 多项式

| CRC 类型 | 多项式 | 应用 |
|----------|--------|------|
| CRC-8 | x^8 + x^2 + x + 1 | SMBus |
| CRC-16 | x^16 + x^15 + x^2 + 1 | Modbus |
| CRC-32 | 0x04C11DB7 | Ethernet |

## 代码模板

### CRC-8 计算
```verilog
module crc8 #(
    parameter POLY = 8'h07  // x^8 + x^2 + x + 1
)(
    input        clk,
    input        rst_n,
    input        valid,
    input  [7:0] data_in,
    output reg [7:0] crc_out
);

    wire [7:0] crc_next;
    wire [7:0] crc_xor = crc_out ^ data_in;

    assign crc_next[0] = crc_xor[0] ^ crc_xor[3] ^ crc_xor[5] ^ crc_xor[6];
    assign crc_next[1] = crc_xor[1] ^ crc_xor[4] ^ crc_xor[6] ^ crc_xor[7];
    assign crc_next[2] = crc_xor[0] ^ crc_xor[2] ^ crc_xor[3] ^ crc_xor[5] ^ crc_xor[6];
    assign crc_next[3] = crc_xor[1] ^ crc_xor[3] ^ crc_xor[4] ^ crc_xor[6] ^ crc_xor[7];
    assign crc_next[4] = crc_xor[2] ^ crc_xor[4] ^ crc_xor[5] ^ crc_xor[7];
    assign crc_next[5] = crc_xor[0] ^ crc_xor[3] ^ crc_xor[5] ^ crc_xor[6];
    assign crc_next[6] = crc_xor[1] ^ crc_xor[4] ^ crc_xor[6] ^ crc_xor[7];
    assign crc_next[7] = crc_xor[2] ^ crc_xor[5] ^ crc_xor[7];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            crc_out <= 8'hFF;
        else if (valid)
            crc_out <= crc_next;
    end

endmodule
```

### 可配置 CRC
```verilog
module crc_configurable #(
    parameter WIDTH = 8,
    parameter POLY = 8'h07,
    parameter INIT = 8'hFF,
    parameter REFLECT = 0
)(
    input              clk,
    input              rst_n,
    input              valid,
    input  [WIDTH-1:0] data_in,
    output [WIDTH-1:0] crc_out
);

    reg [WIDTH-1:0] crc_reg;
    wire [WIDTH-1:0] data_reflected;
    wire [WIDTH-1:0] crc_xor;

    // 数据反射
    generate
        if (REFLECT) begin : gen_reflect
            integer i;
            always @(*) begin
                for (i = 0; i < WIDTH; i = i + 1)
                    data_reflected[i] = data_in[WIDTH-1-i];
            end
        end else begin : gen_no_reflect
            assign data_reflected = data_in;
        end
    endgenerate

    assign crc_xor = crc_reg ^ data_reflected;

    // LFSR 计算
    wire [WIDTH-1:0] crc_next;
    integer j;
    always @(*) begin
        crc_next = crc_xor;
        for (j = WIDTH-1; j > 0; j = j - 1) begin
            if (crc_next[WIDTH-1])
                crc_next = (crc_next << 1) ^ POLY;
            else
                crc_next = crc_next << 1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            crc_reg <= INIT;
        else if (valid)
            crc_reg <= crc_next;
    end

    assign crc_out = crc_reg;

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 初始值错误 | CRC 不匹配 | 使用标准初始值 |
| 多项式错误 | CRC 不匹配 | 使用标准多项式 |
| 数据顺序错误 | CRC 不匹配 | 确认 MSB/LSB 顺序 |

## 验证检查清单

- [ ] 已知数据 CRC 正确
- [ ] 多字节 CRC 正确
- [ ] 错误数据能检测
