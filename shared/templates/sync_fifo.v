// 同步 FIFO 模板
// 参数化宽度和深度，带满/空标志

module sync_fifo #(
    parameter DATA_WIDTH = 8,
    parameter DEPTH      = 16,
    parameter PTR_WIDTH  = 5  // log2(DEPTH) + 1
)(
    input                    clk,
    input                    rst_n,
    // 写端口
    input                    wr_en,
    input  [DATA_WIDTH-1:0]  wdata,
    output                   full,
    // 读端口
    input                    rd_en,
    output [DATA_WIDTH-1:0]  rdata,
    output                   empty
);

    // 存储器
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];

    // 读写指针
    reg [PTR_WIDTH-1:0] wr_ptr;
    reg [PTR_WIDTH-1:0] rd_ptr;

    // 空满判断
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
