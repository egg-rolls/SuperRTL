// 4位计数器示例
module counter (
    input clk,
    input rst_n,
    output reg [3:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 4'b0;
        else
            count <= count + 1'b1;
    end

endmodule
