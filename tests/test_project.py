"""
项目配置模块测试
"""

import tempfile
from pathlib import Path

from superrtl.project import (
    DEFAULT_CONFIG,
    _deep_merge,
    get_project_info,
    init_project,
    load_config,
    resolve_sources,
    resolve_testbenches,
    save_config,
)


class TestDeepMerge:
    """深度合并测试"""

    def test_merge_flat(self):
        """测试扁平字典合并"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        _deep_merge(base, override)
        assert base == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested(self):
        """测试嵌套字典合并"""
        base = {"a": {"x": 1, "y": 2}, "b": 1}
        override = {"a": {"y": 3, "z": 4}}
        _deep_merge(base, override)
        assert base == {"a": {"x": 1, "y": 3, "z": 4}, "b": 1}

    def test_merge_override_dict_with_value(self):
        """测试用值覆盖字典"""
        base = {"a": {"x": 1}}
        override = {"a": "string"}
        _deep_merge(base, override)
        assert base == {"a": "string"}


class TestLoadConfig:
    """加载配置测试"""

    def test_load_default_when_no_config(self):
        """没有配置文件时返回默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = load_config(Path(tmpdir) / "nonexistent.yaml")
            assert config == DEFAULT_CONFIG

    def test_load_valid_config(self):
        """加载有效配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".superrtl.yaml"
            config_path.write_text(
                "project:\n  name: test\n  top: top_mod\nsources:\n- src/*.v\n",
                encoding="utf-8",
            )
            config = load_config(config_path)
            assert config["project"]["name"] == "test"
            assert config["project"]["top"] == "top_mod"
            assert config["sources"] == ["src/*.v"]
            # 默认值应该保留
            assert config["sim"]["timeout"] == 30

    def test_load_invalid_yaml(self):
        """加载无效 YAML 返回默认配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".superrtl.yaml"
            config_path.write_text("{{invalid yaml", encoding="utf-8")
            config = load_config(config_path)
            assert config == DEFAULT_CONFIG


class TestSaveConfig:
    """保存配置测试"""

    def test_save_and_load(self):
        """保存后加载应该一致"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".superrtl.yaml"
            config = {"project": {"name": "test", "top": "mod"}, "sources": ["*.v"]}
            save_config(config, config_path)
            assert config_path.exists()

            loaded = load_config(config_path)
            assert loaded["project"]["name"] == "test"
            assert loaded["sources"] == ["*.v"]


class TestInitProject:
    """初始化项目测试"""

    def test_init_default(self):
        """默认初始化"""
        config = init_project()
        assert config["project"]["name"] == "my_project"
        assert config["sim"]["timeout"] == 30

    def test_init_with_params(self):
        """带参数初始化"""
        config = init_project(name="test_proj", top="top_mod")
        assert config["project"]["name"] == "test_proj"
        assert config["project"]["top"] == "top_mod"


class TestResolveSources:
    """解析源文件测试"""

    def test_resolve_glob(self):
        """解析 glob 模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "a.v").write_text("module a; endmodule")
            (tmpdir_path / "b.v").write_text("module b; endmodule")
            (tmpdir_path / "c.txt").write_text("not verilog")

            config = {"sources": ["*.v"]}
            files = resolve_sources(config, tmpdir_path)
            assert len(files) == 2
            assert all(str(f).endswith(".v") for f in files)

    def test_resolve_empty(self):
        """空配置返回空列表"""
        config = {"sources": []}
        files = resolve_sources(config)
        assert files == []

    def test_resolve_no_match(self):
        """无匹配返回空列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {"sources": ["nonexistent/*.v"]}
            files = resolve_sources(config, Path(tmpdir))
            assert files == []


class TestResolveTestbenches:
    """解析测试平台测试"""

    def test_resolve_testbenches(self):
        """解析测试平台文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            (tmpdir_path / "tb_top.v").write_text("module tb_top; endmodule")
            (tmpdir_path / "top.v").write_text("module top; endmodule")

            config = {"testbenches": ["tb_*.v"]}
            files = resolve_testbenches(config, tmpdir_path)
            assert len(files) == 1
            assert "tb_top" in str(files[0])


class TestGetProjectInfo:
    """项目信息测试"""

    def test_get_info(self):
        """获取项目信息"""
        config = {
            "project": {"name": "test", "top": "mod"},
            "sources": ["*.v"],
            "testbenches": ["tb.v"],
            "sim": {"timeout": 60},
            "lint": {"style": "strict"},
            "build": {"target": "xilinx"},
        }
        info = get_project_info(config)
        assert info["name"] == "test"
        assert info["top"] == "mod"
        assert info["sim_timeout"] == 60
        assert info["lint_style"] == "strict"
        assert info["build_target"] == "xilinx"
