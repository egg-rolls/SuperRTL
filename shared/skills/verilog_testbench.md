---
name: "verilog-testbench"
version: "1.0.0"
description: "Testbench 方法学 - 自检查测试平台设计"
author: "SuperRTL Team"
tags: ["testbench", "verification", "simulation", "testing"]
triggers: ["testbench", "tb", "测试平台", "仿真", "验证"]
---

# Testbench 方法学

## 概述

良好的 Testbench 是验证设计正确性的关键。本文档介绍自检查测试平台、时钟/复位生成、激励生成和结果检查等方法。

## 设计要点

### 1. Testbench 结构
```
+------------------+
|    Testbench     |
|  +------------+  |
|  | Clock Gen  |  |
|  +------------+  |
|  | Reset Gen  |  |
|  +------------+  |
|  | Stimulus   |  |
|  +------------+  |
|  | DUT        |  |
|  +------------+  |
|  | Checker    |  |
|  +------------+  |
|  | Logger     |  |
|  +------------+  |
+------------------+
```

### 2. 自检查原则
- 预期结果与实际结果比较
- 使用 `$display` 输出 PASS/FAIL
- 设置超时机制防止死锁

### 3. 激励生成方法
- 直接赋值 (简单)
- 随机激励 (`$random`)
- 遍历所有输入组合

## 代码模板

### 基础 Testbench 框架
```verilog
`timescale 1ns/1ps

module tb_template;

    // 参数
    parameter CLK_PERIOD = 10;

    // 信号声明
    reg clk;
    reg rst_n;
    // ... DUT 信号

    // 时钟生成
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // 复位生成
    initial begin
        rst_n = 0;
        #(CLK_PERIOD * 5);
        rst_n = 1;
    end

    // DUT 实例化
    dut_module uut (
        .clk(clk),
        .rst_n(rst_n)
        // ... 其他端口
    );

    // 测试激励
    initial begin
        wait(rst_n == 1);
        @(posedge clk);

        // 测试用例 1
        // ...

        // 测试完成
        #100;
        $display("PASS");
        $finish;
    end

    // 超时保护
    initial begin
        #100000;
        $display("TIMEOUT");
        $finish;
    end

    // 波形输出
    initial begin
        $dumpfile("tb_template.vcd");
        $dumpvars(0, tb_template);
    end

endmodule
```

### 自检查 Testbench 示例
```verilog
module tb_self_check;

    parameter CLK_PERIOD = 10;
    parameter DATA_WIDTH = 8;

    reg clk, rst_n;
    reg [DATA_WIDTH-1:0] a, b;
    wire [DATA_WIDTH-1:0] sum;
    wire carry;

    // 期望值
    reg [DATA_WIDTH:0] expected;
    integer test_count = 0;
    integer pass_count = 0;

    // 时钟
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // DUT
    adder #(.WIDTH(DATA_WIDTH)) uut (
        .a(a), .b(b), .sum(sum), .carry(carry)
    );

    // 检查任务
    task check_result;
        input [DATA_WIDTH-1:0] exp_a, exp_b;
        input [DATA_WIDTH:0] exp_result;
        begin
            a = exp_a;
            b = exp_b;
            @(posedge clk);
            @(posedge clk);
            expected = exp_result;
            test_count = test_count + 1;
            if ({carry, sum} == expected) begin
                $display("[PASS] %0d + %0d = %0d", exp_a, exp_b, sum);
                pass_count = pass_count + 1;
            end else begin
                $display("[FAIL] %0d + %0d = %0d (expected %0d)",
                         exp_a, exp_b, {carry, sum}, expected);
            end
        end
    endtask

    // 测试序列
    initial begin
        rst_n = 0;
        a = 0; b = 0;
        #(CLK_PERIOD * 5);
        rst_n = 1;
        @(posedge clk);

        // 测试用例
        check_result(0, 0, 0);
        check_result(1, 1, 2);
        check_result(255, 1, 256);
        check_result(128, 128, 256);

        // 结果统计
        #100;
        $display("Tests: %0d, Passed: %0d, Failed: %0d",
                 test_count, pass_count, test_count - pass_count);
        if (pass_count == test_count)
            $display("PASS");
        else
            $display("FAIL");
        $finish;
    end

    // 超时
    initial begin
        #100000;
        $display("TIMEOUT");
        $finish;
    end

endmodule
```

### 随机激励生成
```verilog
// 在 initial 块中使用
integer i;
initial begin
    for (i = 0; i < 100; i = i + 1) begin
        a = $random;
        b = $random;
        @(posedge clk);
        // 检查结果
    end
end
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 无超时机制 | 仿真死锁 | 添加 initial 超时 |
| 时钟未生成 | 无仿真活动 | 确保 forever 循环 |
| 信号竞争 | 不确定结果 | 使用非阻塞赋值 |
| 未初始化 | X 传播 | 复位所有信号 |

## 验证检查清单

- [ ] 时钟和复位正确生成
- [ ] 所有输入端口有激励
- [ ] 输出有明确检查
- [ ] 有 PASS/FAIL 判定
- [ ] 有超时保护
- [ ] 有波形输出配置
