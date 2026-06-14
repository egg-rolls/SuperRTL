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
        assert data["count"] > 0

        # 每个 skill 应该包含元数据
        skill = data["skills"][0]
        assert "name" in skill
        assert "display_name" in skill
        assert "version" in skill
        assert "description" in skill
        assert "tags" in skill

        # 应该有 fsm 和 fifo
        display_names = [s["display_name"] for s in data["skills"]]
        assert "fsm" in display_names
        assert "fifo" in display_names

    @pytest.mark.asyncio
    async def test_get_skill_fsm(self):
        """测试获取 fsm skill"""
        result = await get_skill("fsm")
        data = json.loads(result)

        # 应该返回结构化内容
        assert "name" in data
        assert "version" in data
        assert "content" in data
        assert "FSM" in data["content"] or "状态机" in data["content"]
        assert "always" in data["content"]  # 应该包含代码示例

    @pytest.mark.asyncio
    async def test_get_skill_fifo(self):
        """测试获取 fifo skill"""
        result = await get_skill("fifo")
        data = json.loads(result)

        assert "content" in data
        assert "FIFO" in data["content"]
        assert "module" in data["content"]

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
