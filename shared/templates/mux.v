// 4-1 多路选择器模板
// 参数化数据宽度

module mux_4to1 #(
    parameter DATA_WIDTH = 8
)(
    input  [DATA_WIDTH-1:0] d0,
    input  [DATA_WIDTH-1:0] d1,
    input  [DATA_WIDTH-1:0] d2,
    input  [DATA_WIDTH-1:0] d3,
    input  [1:0]            sel,
    output reg [DATA_WIDTH-1:0] y
);

    always @(*) begin
        case (sel)
            2'b00:   y = d0;
            2'b01:   y = d1;
            2'b10:   y = d2;
            2'b11:   y = d3;
            default: y = {DATA_WIDTH{1'b0}};
        endcase
    end

endmodule
