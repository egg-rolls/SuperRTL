"""
波形分析测试
"""

import pytest

from superrtl.tools.waveform import analyze_waveform

# 测试用 VCD 内容
SAMPLE_VCD = """$timescale 1ns $end
$scope module top $end
$var wire 1 ! clk $end
$var reg 4 " count $end
$upscope $end
$enddefinitions $end
#0
0!
b0000 "
#5
1!
#10
0!
b0001 "
#15
1!
#20
0!
b0010 "
"""


class TestAnalyzeWaveform:
    """analyze_waveform 测试"""

    @pytest.mark.asyncio
    async def test_parse_vcd_content(self):
        """测试解析 VCD 内容"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        assert result["success"] is True
        assert "signals" in result
        assert "clk" in result["signals"]
        assert "count" in result["signals"]

    @pytest.mark.asyncio
    async def test_signal_width(self):
        """测试信号宽度解析"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        assert result["signals"]["clk"]["width"] == 1
        assert result["signals"]["count"]["width"] == 4

    @pytest.mark.asyncio
    async def test_time_range(self):
        """测试时间范围解析"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        assert result["time_range"]["start"] == 0
        assert result["time_range"]["end"] == 20

    @pytest.mark.asyncio
    async def test_signal_values(self):
        """测试信号值解析"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        clk_values = result["signals"]["clk"]["values"]
        # VCD 中有 5 个时钟变化: 0, 5, 10, 15, 20
        assert len(clk_values) == 5
        assert clk_values[0] == {"time": 0, "value": "0"}
        assert clk_values[1] == {"time": 5, "value": "1"}

    @pytest.mark.asyncio
    async def test_filter_signals(self):
        """测试信号过滤"""
        result = await analyze_waveform(
            vcd_content=SAMPLE_VCD,
            signals=["clk"]
        )

        assert "clk" in result["signals"]
        assert "count" not in result["signals"]

    @pytest.mark.asyncio
    async def test_partial_signal_match(self):
        """测试部分信号名匹配"""
        result = await analyze_waveform(
            vcd_content=SAMPLE_VCD,
            signals=["cl"]  # 部分匹配 "clk"
        )

        assert "clk" in result["signals"]

    @pytest.mark.asyncio
    async def test_ascii_waveform(self):
        """测试 ASCII 波形生成"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        assert "ascii_waveform" in result
        assert "clk" in result["ascii_waveform"]
        assert "count" in result["ascii_waveform"]

    @pytest.mark.asyncio
    async def test_no_input(self):
        """测试无输入时返回错误"""
        result = await analyze_waveform()

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """测试不存在的文件"""
        result = await analyze_waveform(vcd_file="nonexistent.vcd")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_timescale(self):
        """测试时间刻度解析"""
        result = await analyze_waveform(vcd_content=SAMPLE_VCD)

        assert result["timescale"] == "1ns"
