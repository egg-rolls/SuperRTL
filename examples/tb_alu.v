// ALU 测试平台
`timescale 1ns/1ps

module tb_alu;

    parameter WIDTH = 8;

    reg  [WIDTH-1:0] a, b;
    reg  [2:0]       op;
    wire [WIDTH-1:0] result;
    wire             zero;

    // 实例化 ALU
    alu #(.WIDTH(WIDTH)) uut (
        .a(a),
        .b(b),
        .op(op),
        .result(result),
        .zero(zero)
    );

    initial begin
        // 测试加法
        a = 8'd10; b = 8'd5; op = 3'b000;
        #10;
        $display("ADD: %0d + %0d = %0d", a, b, result);

        // 测试减法
        a = 8'd10; b = 8'd10; op = 3'b001;
        #10;
        $display("SUB: %0d - %0d = %0d (zero=%b)", a, b, result, zero);

        // 测试 AND
        a = 8'b1010; b = 8'b1100; op = 3'b010;
        #10;
        $display("AND: %b & %b = %b", a, b, result);

        // 测试完成
        #100;
        $display("PASS");
        $finish;
    end

    // 波形输出
    initial begin
        $dumpfile("tb_alu.vcd");
        $dumpvars(0, tb_alu);
    end

    // 超时保护
    initial begin
        #100000;
        $display("TIMEOUT");
        $finish;
    end

endmodule
