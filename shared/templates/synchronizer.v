// 2 级同步器模板
// 用于跨时钟域单 bit 信号同步

module synchronizer #(
    parameter WIDTH = 1
)(
    input                  clk,
    input                  rst_n,
    input  [WIDTH-1:0]     data_in,
    output [WIDTH-1:0]     data_out
);

    reg [WIDTH-1:0] sync_reg1;
    reg [WIDTH-1:0] sync_reg2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync_reg1 <= {WIDTH{1'b0}};
            sync_reg2 <= {WIDTH{1'b0}};
        end else begin
            sync_reg1 <= data_in;
            sync_reg2 <= sync_reg1;
        end
    end

    assign data_out = sync_reg2;

endmodule
