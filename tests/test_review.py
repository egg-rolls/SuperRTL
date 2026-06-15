"""
代码审查工具测试
"""

import pytest

from superrtl.tools.review import review_verilog


class TestReviewVerilog:
    """review_verilog 测试"""

    @pytest.mark.asyncio
    async def test_result_structure(self):
        """测试结果结构"""
        code = "module test (input a, output b); assign b = a; endmodule"
        result = await review_verilog(code)

        assert result["success"] is True
        assert "issues" in result
        assert "summary" in result
        assert "synthesizable" in result
        assert "checks_run" in result

    @pytest.mark.asyncio
    async def test_empty_code_returns_error(self):
        """测试空代码返回错误"""
        result = await review_verilog("")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_synthesizable_code(self):
        """测试可综合代码"""
        code = """\
module counter (
    input clk,
    input rst_n,
    output reg [3:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 0;
        else
            count <= count + 1;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        assert result["synthesizable"] is True

    @pytest.mark.asyncio
    async def test_detects_delay(self):
        """测试检测 # 延迟"""
        code = """\
module test (
    input clk,
    output reg out
);
    always @(posedge clk) begin
        #10 out = 1;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        errors = [i for i in result["issues"] if i["category"] == "synthesizability"]
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_detects_system_task(self):
        """测试检测系统任务"""
        code = """\
module test;
    initial begin
        $display("Hello");
        $finish;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        synth_issues = [i for i in result["issues"] if i["category"] == "synthesizability"]
        assert len(synth_issues) > 0

    @pytest.mark.asyncio
    async def test_detects_missing_else(self):
        """测试检测缺少 else 的 if"""
        code = """\
module test (
    input sel,
    input [7:0] a, b,
    output reg [7:0] out
);
    always @(*) begin
        if (sel)
            out = a;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        latch_issues = [i for i in result["issues"] if i["category"] == "latch"]
        # 应该检测到潜在的锁存器
        assert len(latch_issues) > 0

    @pytest.mark.asyncio
    async def test_detects_missing_case_default(self):
        """测试检测缺少 default 的 case"""
        code = """\
module test (
    input [1:0] sel,
    input [7:0] a, b, c, d,
    output reg [7:0] out
);
    always @(*) begin
        case (sel)
            0: out = a;
            1: out = b;
            2: out = c;
        endcase
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        latch_issues = [i for i in result["issues"] if i["category"] == "latch"]
        assert len(latch_issues) > 0

    @pytest.mark.asyncio
    async def test_detects_missing_reset(self):
        """测试检测缺少复位信号"""
        code = """\
module test (
    input clk,
    input d,
    output reg q
);
    always @(posedge clk) begin
        q <= d;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        reset_issues = [i for i in result["issues"] if i["category"] == "reset"]
        assert len(reset_issues) > 0

    @pytest.mark.asyncio
    async def test_specific_checks(self):
        """测试指定检查类别"""
        code = """\
module test (
    input clk,
    input rst_n,
    output reg [3:0] count
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 0;
        else
            count <= count + 1;
    end
endmodule
"""
        result = await review_verilog(code, checks=["synthesizability"])
        assert result["success"] is True
        assert result["checks_run"] == ["synthesizability"]

    @pytest.mark.asyncio
    async def test_summary_counts(self):
        """测试问题统计"""
        code = """\
module test;
    initial begin
        #10;
        $display("test");
        $finish;
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        summary = result["summary"]
        assert summary["errors"] > 0 or summary["warnings"] > 0

    @pytest.mark.asyncio
    async def test_casex_warning(self):
        """测试 casex 警告"""
        code = """\
module test (
    input [1:0] sel,
    output reg out
);
    always @(*) begin
        casex (sel)
            2'b0?: out = 0;
            2'b1?: out = 1;
            default: out = 0;
        endcase
    end
endmodule
"""
        result = await review_verilog(code)
        assert result["success"] is True
        case_issues = [i for i in result["issues"] if i["category"] == "case"]
        assert len(case_issues) > 0
