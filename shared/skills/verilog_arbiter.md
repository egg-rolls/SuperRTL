---
name: "verilog-arbiter"
version: "1.0.0"
description: "仲裁器设计 - 固定优先级、轮询仲裁"
author: "SuperRTL Team"
tags: ["arbiter", "priority", "round-robin", "bus"]
triggers: ["arbiter", "仲裁", "优先级", "round-robin"]
---

# 仲裁器设计

## 概述

仲裁器用于多个请求者竞争共享资源时的调度。常见策略有固定优先级和轮询 (Round-Robin)。

## 设计要点

### 1. 仲裁策略
| 策略 | 特点 | 适用场景 |
|------|------|----------|
| 固定优先级 | 简单，高优先级饿死低优先级 | 中断控制器 |
| 轮询 | 公平，无饿死 | 总线仲裁 |
| 加权轮询 | 按权重分配 | QoS 场景 |

## 代码模板

### 固定优先级仲裁器
```verilog
module priority_arbiter #(
    parameter WIDTH = 4
)(
    input  [WIDTH-1:0] request,
    output [WIDTH-1:0] grant
);

    // 固定优先级：bit 0 最高
    assign grant = request & (~request + 1);

endmodule
```

### 轮询仲裁器
```verilog
module round_robin_arbiter #(
    parameter WIDTH = 4
)(
    input                   clk,
    input                   rst_n,
    input  [WIDTH-1:0]      request,
    output reg [WIDTH-1:0]  grant
);

    reg [WIDTH-1:0] mask;
    wire [WIDTH-1:0] masked_req = request & mask;

    // 优先级编码
    function [WIDTH-1:0] priority_encode;
        input [WIDTH-1:0] req;
        begin
            priority_encode = req & (~req + 1);
        end
    endfunction

    wire [WIDTH-1:0] masked_grant = priority_encode(masked_req);
    wire [WIDTH-1:0] raw_grant = priority_encode(request);
    wire use_masked = |masked_req;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            grant <= 0;
            mask <= {WIDTH{1'b1}};
        end else begin
            if (use_masked) begin
                grant <= masked_grant;
                // 更新 mask：屏蔽当前及更高优先级
                mask <= ~(masked_grant | (masked_grant - 1));
            end else begin
                grant <= raw_grant;
                mask <= ~(raw_grant | (raw_grant - 1));
            end
        end
    end

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 优先级饿死 | 低优先级永远等待 | 使用轮询 |
| 无请求时输出 | 无效授权 | 检查 request != 0 |
| mask 更新错误 | 轮询不公平 | 正确计算 mask |

## 验证检查清单

- [ ] 单请求正确授权
- [ ] 多请求按策略授权
- [ ] 轮询公平性
- [ ] 无请求时无输出
