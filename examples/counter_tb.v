// 4位计数器测试平台
`timescale 1ns/1ps

module counter_tb;

    // 时钟和复位
    reg clk;
    reg rst_n;

    // 待测模块信号
    wire [3:0] count;

    // 实例化待测模块
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    // 时钟生成
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // 测试激励
    initial begin
        // 复位
        rst_n = 0;
        #20;
        rst_n = 1;

        // 运行 100 个时钟周期
        #1000;

        // 检查结果
        $display("Test completed. Final count: %d", count);
        $display("PASS");
        $finish;
    end

    // 波形输出
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

    // 超时保护
    initial begin
        #100000;
        $display("TIMEOUT");
        $finish;
    end

endmodule
