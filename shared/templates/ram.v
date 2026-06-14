// 简单双端口 RAM 模板
// 参数化宽度和深度，支持同时读写

module ram #(
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

    // 存储器
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
