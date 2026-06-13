# FIFO 设计模式

## 概述

FIFO (First In First Out) 是数据缓冲的基本结构，广泛用于跨时钟域数据传输。

## 同步 FIFO

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

## 设计要点

1. 使用额外一位指针判断满/空状态
2. 深度应为 2 的幂次便于综合优化
3. 异步 FIFO 需要格雷码同步指针
