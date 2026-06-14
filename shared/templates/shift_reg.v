// 移位寄存器模板
// 参数化宽度，支持串行输入输出

module shift_reg #(
    parameter WIDTH = 8
)(
    input                    clk,
    input                    rst_n,
    input                    en,
    input                    serial_in,
    output                   serial_out,
    output reg [WIDTH-1:0]   data
);

    // 串行输出取最高位
    assign serial_out = data[WIDTH-1];

    // 移位逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data <= {WIDTH{1'b0}};
        end else if (en) begin
            data <= {data[WIDTH-2:0], serial_in};
        end
    end

endmodule
