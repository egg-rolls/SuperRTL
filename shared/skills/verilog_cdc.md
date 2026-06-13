# Verilog Clock Domain Crossing (CDC) Design Skill

## 触发条件
- 用户请求处理跨时钟域问题
- 多时钟设计、时钟域交叉
- 关键词：CDC, clock domain, crossing, synchronizer, metastability

## 设计要点

### 1. CDC类型
| 类型 | 方法 | 适用场景 |
|-----|------|---------|
| 单bit控制信号 | 2级同步器 | 使能、复位、标志位 |
| 多bit控制信号 | 握手协议 | 命令、状态 |
| 多bit数据 | 异步FIFO | 数据流传输 |

### 2. 亚稳态
- 触发器输出在时钟采样边沿不确定
- 解决方案：2级或多级同步器

### 3. 同步器规则
- 目标域时钟驱动
- 组合逻辑输出不能直接跨域
- 需要2个目标时钟周期稳定

## 代码模板

### 2级同步器 (单bit)
```verilog
module synchronizer_2ff #(
    parameter WIDTH = 1
)(
    input              clk,
    input              rst_n,
    input  [WIDTH-1:0] data_in,
    output [WIDTH-1:0] data_out
);
    reg [WIDTH-1:0] sync1;
    reg [WIDTH-1:0] sync2;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sync1 <= {WIDTH{1'b0}};
            sync2 <= {WIDTH{1'b0}};
        end else begin
            sync1 <= data_in;
            sync2 <= sync1;
        end
    end
    
    assign data_out = sync2;
endmodule
```

### 脉冲同步器 (快到慢)
```verilog
module pulse_synchronizer (
    input      src_clk,
    input      src_rst_n,
    input      src_pulse,
    input      dst_clk,
    input      dst_rst_n,
    output     dst_pulse
);
    reg src_level;
    reg dst_level;
    reg [2:0] sync_reg;
    
    // 源域：脉冲转电平
    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n)
            src_level <= 1'b0;
        else if (src_pulse)
            src_level <= ~src_level;
    end
    
    // 同步到目标域
    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n)
            sync_reg <= 3'b0;
        else
            sync_reg <= {sync_reg[1:0], src_level};
    end
    
    // 目标域：电平转脉冲
    assign dst_pulse = sync_reg[2] ^ sync_reg[1];
endmodule
```

### 握手协议 (多bit控制)
```verilog
module handshake_cdc #(
    parameter DATA_WIDTH = 8
)(
    input                  src_clk,
    input                  src_rst_n,
    input                  src_valid,
    input  [DATA_WIDTH-1:0] src_data,
    output                 src_ready,
    
    input                  dst_clk,
    input                  dst_rst_n,
    output                 dst_valid,
    output [DATA_WIDTH-1:0] dst_data,
    input                  dst_ready
);
    // 握手信号跨域
    reg src_req, dst_ack;
    reg src_req_sync1, src_req_sync2;
    reg dst_ack_sync1, dst_ack_sync2;
    
    // 同步
    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n) begin
            src_req_sync1 <= 1'b0;
            src_req_sync2 <= 1'b0;
        end else begin
            src_req_sync1 <= src_req;
            src_req_sync2 <= src_req_sync1;
        end
    end
    
    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            dst_ack_sync1 <= 1'b0;
            dst_ack_sync2 <= 1'b0;
        end else begin
            dst_ack_sync1 <= dst_ack;
            dst_ack_sync2 <= dst_ack_sync1;
        end
    end
    
    // 源域控制
    assign src_ready = ~src_req | dst_ack_sync2;
    always @(posedge src_clk or negedge src_rst_n) begin
        if (!src_rst_n)
            src_req <= 1'b0;
        else if (src_valid && src_ready)
            src_req <= 1'b1;
        else if (dst_ack_sync2)
            src_req <= 1'b0;
    end
    
    // 目标域控制
    reg [DATA_WIDTH-1:0] dst_data_reg;
    assign dst_valid = src_req_sync2 && ~dst_ack;
    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            dst_data_reg <= 0;
            dst_ack <= 1'b0;
        end else begin
            if (dst_valid && dst_ready) begin
                dst_data_reg <= src_data;
                dst_ack <= 1'b1;
            end else if (dst_ack) begin
                dst_ack <= 1'b0;
            end
        end
    end
    assign dst_data = dst_data_reg;
endmodule
```

### 多bit数据同步 (Gray编码)
```verilog
module bin2gray_cdc #(
    parameter WIDTH = 4
)(
    input      src_clk,
    input      src_rst_n,
    input  [WIDTH-1:0] bin_data,
    
    input      dst_clk,
    input      dst_rst_n,
    output [WIDTH-1:0] gray_out
);
    // 二进制转格雷码
    wire [WIDTH-1:0] gray_data;
    assign gray_data = (bin_data >> 1) ^ bin_data;
    
    // 同步到目标域
    reg [WIDTH-1:0] sync1, sync2;
    
    always @(posedge dst_clk or negedge dst_rst_n) begin
        if (!dst_rst_n) begin
            sync1 <= 0;
            sync2 <= 0;
        end else begin
            sync1 <= gray_data;
            sync2 <= sync1;
        end
    end
    
    assign gray_out = sync2;
endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 组合逻辑直接跨域 | 亚稳态、数据错误 | 加寄存器 |
| 单bit用同步FIFO | 资源浪费 | 用2级同步器 |
| 多bit直接同步 | 数据错位 | 用握手或FIFO |
| 异步信号无同步 | 亚稳态 | 必须同步 |

## CDC检查清单
- [ ] 所有跨时钟域信号都有同步器
- [ ] 单bit用2级同步器
- [ ] 多bit数据用FIFO
- [ ] 多bit控制用握手协议
- [ ] 无组合逻辑直接跨域
- [ ] 异步复位有同步
