// 时钟分频器模板
// 参数化分频系数，支持偶数和奇数分频

module clk_div #(
    parameter DIV = 4  // 分频系数
)(
    input      clk,
    input      rst_n,
    output reg clk_out
);

    // 计数器位宽
    localparam CNT_WIDTH = $clog2(DIV);

    reg [CNT_WIDTH-1:0] cnt;

    generate
        if (DIV % 2 == 0) begin : gen_even
            // 偶数分频
            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    cnt <= {CNT_WIDTH{1'b0}};
                    clk_out <= 1'b0;
                end else begin
                    if (cnt == DIV / 2 - 1) begin
                        cnt <= {CNT_WIDTH{1'b0}};
                        clk_out <= ~clk_out;
                    end else begin
                        cnt <= cnt + 1'b1;
                    end
                end
            end
        end else begin : gen_odd
            // 奇数分频 (占空比 50%)
            reg clk_pos, clk_neg;

            always @(posedge clk or negedge rst_n) begin
                if (!rst_n) begin
                    cnt <= {CNT_WIDTH{1'b0}};
                    clk_pos <= 1'b0;
                end else begin
                    if (cnt == DIV - 1) begin
                        cnt <= {CNT_WIDTH{1'b0}};
                    end else begin
                        cnt <= cnt + 1'b1;
                    end
                    clk_pos <= (cnt < (DIV - 1) / 2) ? 1'b1 : 1'b0;
                end
            end

            always @(negedge clk or negedge rst_n) begin
                if (!rst_n)
                    clk_neg <= 1'b0;
                else
                    clk_neg <= (cnt < (DIV - 1) / 2) ? 1'b1 : 1'b0;
            end

            always @(*) begin
                clk_out = clk_pos & clk_neg;
            end
        end
    endgenerate

endmodule
