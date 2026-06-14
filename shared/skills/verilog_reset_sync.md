---
name: "verilog-reset-sync"
version: "1.0.0"
description: "复位同步器设计 - 异步复位同步释放"
author: "SuperRTL Team"
tags: ["reset", "synchronizer", "clock-domain", "reliability"]
triggers: ["reset", "复位", "reset synchronizer", "复位同步"]
---

# 复位同步器设计

## 概述

复位同步器确保复位信号在时钟域内正确释放，避免亚稳态。推荐使用"异步复位、同步释放"方式。

## 设计要点

### 1. 复位方式对比
| 方式 | 优点 | 缺点 |
|------|------|------|
| 异步复位 | 响应快 | 释放时可能亚稳态 |
| 同步复位 | 安全 | 复位信号需要时钟 |
| 异步复位同步释放 | 两者兼顾 | 需要额外逻辑 |

### 2. 关键原则
- 复位可以异步（立即生效）
- 释放必须同步（在时钟边沿释放）

## 代码模板

### 基础复位同步器
```verilog
module reset_synchronizer (
    input  clk,
    input  async_rst_n,
    output sync_rst_n
);

    reg [1:0] rst_sync;

    always @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            rst_sync <= 2'b00;
        else
            rst_sync <= {rst_sync[0], 1'b1};
    end

    assign sync_rst_n = rst_sync[1];

endmodule
```

### 带使能的复位同步器
```verilog
module reset_synchronizer_en (
    input  clk,
    input  async_rst_n,
    input  enable,
    output sync_rst_n
);

    reg [1:0] rst_sync;

    always @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            rst_sync <= 2'b00;
        else if (enable)
            rst_sync <= {rst_sync[0], 1'b1};
    end

    assign sync_rst_n = rst_sync[1];

endmodule
```

### 多时钟域复位同步
```verilog
module reset_sync_multi_domain (
    input  clk_a,
    input  clk_b,
    input  async_rst_n,
    output sync_rst_n_a,
    output sync_rst_n_b
);

    // 域 A 复位同步
    reset_synchronizer u_rst_sync_a (
        .clk(clk_a),
        .async_rst_n(async_rst_n),
        .sync_rst_n(sync_rst_n_a)
    );

    // 域 B 复位同步
    reset_synchronizer u_rst_sync_b (
        .clk(clk_b),
        .async_rst_n(async_rst_n),
        .sync_rst_n(sync_rst_n_b)
    );

endmodule
```

## 常见错误

| 错误 | 后果 | 解决方案 |
|-----|------|---------|
| 复位不同步释放 | 亚稳态 | 使用复位同步器 |
| 复位链太长 | 释放延迟 | 2 级足够 |
| 跨时钟域复位 | 亚稳态 | 每个时钟域单独同步 |

## 验证检查清单

- [ ] 复位立即生效
- [ ] 释放在时钟边沿
- [ ] 无亚稳态
- [ ] 多时钟域独立同步
