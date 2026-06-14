// FSM 三段式模板
// 支持 IDLE/RUN/DONE 三状态，参数化设计

module fsm_template #(
    parameter DATA_WIDTH = 8
)(
    input                    clk,
    input                    rst_n,
    input                    start,
    input                    done,
    input  [DATA_WIDTH-1:0]  data_in,
    output reg [DATA_WIDTH-1:0] data_out,
    output reg               busy
);

    // 状态定义
    localparam IDLE = 2'b00;
    localparam RUN  = 2'b01;
    localparam DONE = 2'b10;

    reg [1:0] current_state, next_state;

    // 第一段：状态寄存器 (时序逻辑)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            current_state <= IDLE;
        else
            current_state <= next_state;
    end

    // 第二段：次态逻辑 (组合逻辑)
    always @(*) begin
        case (current_state)
            IDLE: next_state = start ? RUN : IDLE;
            RUN:  next_state = done ? DONE : RUN;
            DONE: next_state = IDLE;
            default: next_state = IDLE;
        endcase
    end

    // 第三段：输出逻辑 (时序逻辑)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            data_out <= {DATA_WIDTH{1'b0}};
            busy <= 1'b0;
        end else begin
            case (current_state)
                IDLE: begin
                    busy <= 1'b0;
                end
                RUN: begin
                    busy <= 1'b1;
                    data_out <= data_in;
                end
                DONE: begin
                    busy <= 1'b0;
                end
                default: begin
                    busy <= 1'b0;
                end
            endcase
        end
    end

endmodule
