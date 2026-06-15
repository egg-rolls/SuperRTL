// AXI-Lite Slave - 参数化寄存器接口
// 支持 N 个 32 位读写寄存器

module axi_lite_slave #(
    parameter ADDR_WIDTH = 8,
    parameter REG_COUNT = 16
)(
    // AXI-Lite 接口
    input  wire                  aclk,
    input  wire                  aresetn,

    // 写地址通道
    input  wire [ADDR_WIDTH-1:0] s_axi_awaddr,
    input  wire                  s_axi_awvalid,
    output reg                   s_axi_awready,

    // 写数据通道
    input  wire [31:0]           s_axi_wdata,
    input  wire [3:0]            s_axi_wstrb,
    input  wire                  s_axi_wvalid,
    output reg                   s_axi_wready,

    // 写响应通道
    output reg  [1:0]            s_axi_bresp,
    output reg                   s_axi_bvalid,
    input  wire                  s_axi_bready,

    // 读地址通道
    input  wire [ADDR_WIDTH-1:0] s_axi_araddr,
    input  wire                  s_axi_arvalid,
    output reg                   s_axi_arready,

    // 读数据通道
    output reg  [31:0]           s_axi_rdata,
    output reg  [1:0]            s_axi_rresp,
    output reg                   s_axi_rvalid,
    input  wire                  s_axi_rready
);

    // 寄存器文件
    reg [31:0] regs [0:REG_COUNT-1];

    // 写状态机
    localparam WR_IDLE = 0, WR_DATA = 1, WR_RESP = 2;
    reg [1:0] wr_state;
    reg [ADDR_WIDTH-1:0] wr_addr;

    // 读状态机
    localparam RD_IDLE = 0, RD_DATA = 1;
    reg [1:0] rd_state;
    reg [ADDR_WIDTH-1:0] rd_addr;

    integer i;

    // 写状态机
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            wr_state <= WR_IDLE;
            wr_addr <= 0;
            s_axi_awready <= 0;
            s_axi_wready <= 0;
            s_axi_bvalid <= 0;
            s_axi_bresp <= 0;
            for (i = 0; i < REG_COUNT; i = i + 1)
                regs[i] <= 0;
        end else begin
            case (wr_state)
                WR_IDLE: begin
                    if (s_axi_awvalid) begin
                        wr_addr <= s_axi_awaddr;
                        s_axi_awready <= 1;
                        wr_state <= WR_DATA;
                    end
                end

                WR_DATA: begin
                    s_axi_awready <= 0;
                    if (s_axi_wvalid) begin
                        s_axi_wready <= 1;
                        // 写入寄存器（按字节使能）
                        if (wr_addr[ADDR_WIDTH-1:2] < REG_COUNT) begin
                            if (s_axi_wstrb[0]) regs[wr_addr[ADDR_WIDTH-1:2]][7:0]   <= s_axi_wdata[7:0];
                            if (s_axi_wstrb[1]) regs[wr_addr[ADDR_WIDTH-1:2]][15:8]  <= s_axi_wdata[15:8];
                            if (s_axi_wstrb[2]) regs[wr_addr[ADDR_WIDTH-1:2]][23:16] <= s_axi_wdata[23:16];
                            if (s_axi_wstrb[3]) regs[wr_addr[ADDR_WIDTH-1:2]][31:24] <= s_axi_wdata[31:24];
                        end
                        s_axi_bresp <= 2'b00; // OKAY
                        s_axi_bvalid <= 1;
                        wr_state <= WR_RESP;
                    end
                end

                WR_RESP: begin
                    s_axi_wready <= 0;
                    if (s_axi_bready) begin
                        s_axi_bvalid <= 0;
                        wr_state <= WR_IDLE;
                    end
                end

                default: wr_state <= WR_IDLE;
            endcase
        end
    end

    // 读状态机
    always @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            rd_state <= RD_IDLE;
            rd_addr <= 0;
            s_axi_arready <= 0;
            s_axi_rvalid <= 0;
            s_axi_rdata <= 0;
            s_axi_rresp <= 0;
        end else begin
            case (rd_state)
                RD_IDLE: begin
                    if (s_axi_arvalid) begin
                        rd_addr <= s_axi_araddr;
                        s_axi_arready <= 1;
                        rd_state <= RD_DATA;
                    end
                end

                RD_DATA: begin
                    s_axi_arready <= 0;
                    if (rd_addr[ADDR_WIDTH-1:2] < REG_COUNT)
                        s_axi_rdata <= regs[rd_addr[ADDR_WIDTH-1:2]];
                    else
                        s_axi_rdata <= 32'hDEAD_BEEF;
                    s_axi_rresp <= 2'b00; // OKAY
                    s_axi_rvalid <= 1;
                    if (s_axi_rready) begin
                        s_axi_rvalid <= 0;
                        rd_state <= RD_IDLE;
                    end
                end

                default: rd_state <= RD_IDLE;
            endcase
        end
    end

endmodule
