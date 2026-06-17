"""
MCP Prompts 测试 - 测试 prompts 列表和获取
"""

from superrtl.server import SKILL_PROMPTS


class TestMcpPrompts:
    """MCP Prompts 定义测试"""

    def test_prompts_defined(self):
        """测试 prompts 已定义"""
        assert len(SKILL_PROMPTS) > 0

    def test_all_prompts_have_required_fields(self):
        """测试所有 prompts 都有必要字段"""
        for name, config in SKILL_PROMPTS.items():
            assert "description" in config, f"Prompt '{name}' 缺少 description"
            assert isinstance(config["description"], str), f"Prompt '{name}' description 应为字符串"
            assert len(config["description"]) > 0, f"Prompt '{name}' description 不能为空"

    def test_all_prompts_have_arguments(self):
        """测试所有 prompts 都有 arguments 列表"""
        for name, config in SKILL_PROMPTS.items():
            assert "arguments" in config, f"Prompt '{name}' 缺少 arguments"
            assert isinstance(config["arguments"], list), f"Prompt '{name}' arguments 应为列表"

    def test_argument_fields(self):
        """测试参数字段完整性"""
        for name, config in SKILL_PROMPTS.items():
            for arg in config["arguments"]:
                assert "name" in arg, f"Prompt '{name}' 参数缺少 name"
                assert "description" in arg, f"Prompt '{name}' 参数缺少 description"
                assert isinstance(arg["name"], str), f"Prompt '{name}' 参数 name 应为字符串"
                desc = arg["description"]
                assert isinstance(desc, str), f"Prompt '{name}' 参数 description 应为字符串"

    def test_prompt_names(self):
        """测试 prompt 名称列表"""
        expected_prompts = [
            "design-fsm",
            "design-fifo",
            "design-uart",
            "design-cdc",
            "review-code",
            "generate-testbench",
        ]
        for name in expected_prompts:
            assert name in SKILL_PROMPTS, f"缺少预期的 prompt: {name}"

    def test_design_fsm_prompt(self):
        """测试 FSM 设计 prompt"""
        prompt = SKILL_PROMPTS["design-fsm"]
        assert "FSM" in prompt["description"]
        arg_names = [a["name"] for a in prompt["arguments"]]
        assert "spec" in arg_names

    def test_design_fifo_prompt(self):
        """测试 FIFO 设计 prompt"""
        prompt = SKILL_PROMPTS["design-fifo"]
        assert "FIFO" in prompt["description"]
        arg_names = [a["name"] for a in prompt["arguments"]]
        assert "type" in arg_names
        assert "width" in arg_names
        assert "depth" in arg_names

    def test_generate_testbench_prompt(self):
        """测试 testbench 生成 prompt"""
        prompt = SKILL_PROMPTS["generate-testbench"]
        assert "Testbench" in prompt["description"]
        arg_names = [a["name"] for a in prompt["arguments"]]
        assert "code" in arg_names
        assert "style" in arg_names

    def test_review_code_prompt(self):
        """测试代码审查 prompt"""
        prompt = SKILL_PROMPTS["review-code"]
        assert "审查" in prompt["description"]
        arg_names = [a["name"] for a in prompt["arguments"]]
        assert "code" in arg_names
