"""
形式验证工具测试
"""

import pytest
from conftest import requires_sby

from superrtl.tools.formal import formal_verify


class TestFormalVerify:
    """形式验证测试"""

    @pytest.mark.asyncio
    async def test_result_has_success_field(self):
        """测试结果包含 success 字段"""
        result = await formal_verify("module test; endmodule")
        assert "success" in result
        assert isinstance(result["success"], bool)

    @pytest.mark.asyncio
    async def test_empty_code_returns_error(self):
        """测试空代码返回错误"""
        result = await formal_verify("")
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_invalid_code_returns_error(self):
        """测试无效代码返回错误"""
        result = await formal_verify(123)
        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_valid_module_structure(self):
        """测试有效模块的结果结构"""
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

    always @(posedge clk) begin
        assert (count <= 15);
    end
endmodule
"""
        result = await formal_verify(code)

        if result.get("success"):
            assert "passed" in result
            assert "top_module" in result
            assert "depth" in result
            assert "duration" in result
            assert "properties" in result
            assert result["top_module"] == "counter"

    @pytest.mark.asyncio
    async def test_custom_top_module(self):
        """测试自定义顶层模块名"""
        code = """\
module my_mod (
    input clk,
    input rst_n,
    output reg [3:0] val
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) val <= 0;
        else val <= val + 1;
    end

    always @(posedge clk) begin
        assert (val <= 15);
    end
endmodule
"""
        result = await formal_verify(code, top_module="my_mod")

        if result.get("success"):
            assert result["top_module"] == "my_mod"

    @pytest.mark.asyncio
    async def test_custom_depth(self):
        """测试自定义 BMC 深度"""
        result = await formal_verify(
            "module test; endmodule",
            depth=10,
        )

        if result.get("success"):
            assert result["depth"] == 10

    @requires_sby
    @pytest.mark.asyncio
    async def test_counter_bmc_pass(self):
        """测试计数器 BMC 验证通过 (需要 sby)"""
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

    always @(posedge clk) begin
        assert (count <= 15);
    end
endmodule
"""
        result = await formal_verify(code, depth=20)
        assert result["success"] is True
        assert result["passed"] is True
        assert len(result["properties"]) > 0

    @requires_sby
    @pytest.mark.asyncio
    async def test_assert_failure_detected(self):
        """测试断言失败检测 (需要 sby)"""
        code = """\
module bad_counter (
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

    // 这个断言会在 count > 7 时失败
    always @(posedge clk) begin
        assert (count <= 7);
    end
endmodule
"""
        result = await formal_verify(code, depth=20)
        assert result["success"] is True
        # BMC 应该发现反例
        assert result["passed"] is False
