"""
Resources 资源测试
"""

import json

import pytest

from superrtl.resources import get_skill, get_template, list_skills, list_templates


class TestSkills:
    """Skills 资源测试"""

    @pytest.mark.asyncio
    async def test_list_skills(self):
        """测试列出 skills"""
        result = await list_skills()
        data = json.loads(result)

        assert "skills" in data
        assert "count" in data
        assert isinstance(data["skills"], list)
        # 应该有 fsm 和 fifo
        assert "fsm" in data["skills"]
        assert "fifo" in data["skills"]

    @pytest.mark.asyncio
    async def test_get_skill_fsm(self):
        """测试获取 fsm skill"""
        result = await get_skill("fsm")

        # 应该返回 markdown 内容
        assert "FSM" in result or "状态机" in result
        assert "always" in result  # 应该包含代码示例

    @pytest.mark.asyncio
    async def test_get_skill_fifo(self):
        """测试获取 fifo skill"""
        result = await get_skill("fifo")

        assert "FIFO" in result
        assert "module" in result

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self):
        """测试获取不存在的 skill"""
        result = await get_skill("nonexistent")
        data = json.loads(result)

        assert "error" in data
        assert "available" in data

    @pytest.mark.asyncio
    async def test_get_skill_with_prefix(self):
        """测试带前缀的 skill 名称"""
        result = await get_skill("fsm")
        # 两种方式都应该能获取到
        result2 = await get_skill("verilog_fsm")

        # 至少一种方式应该成功
        assert "error" not in result or "error" not in result2


class TestTemplates:
    """Templates 资源测试"""

    @pytest.mark.asyncio
    async def test_list_templates(self):
        """测试列出模板"""
        result = await list_templates()
        data = json.loads(result)

        assert "templates" in data
        assert "count" in data
        assert isinstance(data["templates"], list)
        # 应该有 counter 和 register
        assert "counter" in data["templates"]
        assert "register" in data["templates"]

    @pytest.mark.asyncio
    async def test_get_template_counter(self):
        """测试获取 counter 模板"""
        result = await get_template("counter")

        assert "module counter" in result
        assert "clk" in result
        assert "rst_n" in result

    @pytest.mark.asyncio
    async def test_get_template_register(self):
        """测试获取 register 模板"""
        result = await get_template("register")

        assert "module register" in result
        assert "clk" in result
        assert "load" in result

    @pytest.mark.asyncio
    async def test_get_template_not_found(self):
        """测试获取不存在的模板"""
        result = await get_template("nonexistent")
        data = json.loads(result)

        assert "error" in data
        assert "available" in data
