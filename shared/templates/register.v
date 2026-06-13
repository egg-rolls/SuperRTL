// 带使能的寄存器模板
module register #(
    parameter WIDTH = 8
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             load,
    input  wire [WIDTH-1:0] d,
    output reg  [WIDTH-1:0] q
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            q <= {WIDTH{1'b0}};
        else if (load)
            q <= d;
    end

endmodule
