"""
依赖解析模块测试
"""

import tempfile
from pathlib import Path

import pytest

from superrtl.deps import (
    analyze_file,
    build_dependency_graph,
    detect_cycles,
    find_unused_modules,
    get_compilation_order,
    parse_includes,
    parse_modules,
    topological_sort,
)


class TestParseIncludes:
    """解析 include 指令测试"""

    def test_single_include(self):
        """单个 include"""
        content = '`include "defines.v"\nmodule top; endmodule'
        assert parse_includes(content) == ["defines.v"]

    def test_multiple_includes(self):
        """多个 include"""
        content = '`include "a.v"\n`include "b.v"\nmodule top; endmodule'
        assert parse_includes(content) == ["a.v", "b.v"]

    def test_no_includes(self):
        """无 include"""
        content = "module top; endmodule"
        assert parse_includes(content) == []


class TestParseModules:
    """解析模块测试"""

    def test_module_definition(self):
        """模块定义"""
        content = "module counter(clk, rst_n, count); endmodule"
        modules = parse_modules(content)
        defs = [m for m in modules if m["type"] == "definition"]
        assert len(defs) == 1
        assert defs[0]["name"] == "counter"

    def test_module_instantiation(self):
        """模块实例化"""
        content = "module top;\n  counter uut (.clk(clk));\nendmodule"
        modules = parse_modules(content)
        insts = [m for m in modules if m["type"] == "instance"]
        assert len(insts) == 1
        assert insts[0]["module"] == "counter"
        assert insts[0]["instance"] == "uut"

    def test_parameterized_instantiation(self):
        """带参数的实例化"""
        content = "module top;\n  alu #(.WIDTH(8)) uut (.a(a));\nendmodule"
        modules = parse_modules(content)
        insts = [m for m in modules if m["type"] == "instance"]
        assert len(insts) == 1
        assert insts[0]["module"] == "alu"

    def test_multiple_modules(self):
        """多个模块"""
        content = """
module alu(a, b, result);
endmodule
module top;
  alu u1 (.a(a));
  counter u2 (.clk(clk));
endmodule
"""
        modules = parse_modules(content)
        defs = [m for m in modules if m["type"] == "definition"]
        insts = [m for m in modules if m["type"] == "instance"]
        assert len(defs) == 2
        assert len(insts) == 2

    def test_ignore_keywords(self):
        """忽略关键字"""
        content = "module top;\n  input a;\n  output b;\n  wire c;\nendmodule"
        modules = parse_modules(content)
        insts = [m for m in modules if m["type"] == "instance"]
        assert len(insts) == 0


class TestAnalyzeFile:
    """文件分析测试"""

    def test_analyze_simple_file(self):
        """分析简单文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".v", delete=False, encoding="utf-8"
        ) as f:
            f.write("module counter(clk, rst_n);\nendmodule\n")
            f.flush()
            result = analyze_file(Path(f.name))
            assert "counter" in result["defines"]
            assert result["instances"] == []

    def test_analyze_with_instances(self):
        """分析带实例化的文件"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".v", delete=False, encoding="utf-8"
        ) as f:
            f.write("module top;\n  counter uut (.clk(clk));\nendmodule\n")
            f.flush()
            result = analyze_file(Path(f.name))
            assert "top" in result["defines"]
            assert "counter" in result["instances"]

    def test_analyze_nonexistent(self):
        """分析不存在的文件"""
        result = analyze_file(Path("/nonexistent/file.v"))
        assert result["defines"] == []
        assert result["instances"] == []


class TestBuildDependencyGraph:
    """依赖图测试"""

    def test_simple_graph(self):
        """简单依赖图"""
        analysis = {
            "top.v": {"defines": ["top"], "instances": ["counter"], "includes": []},
            "counter.v": {"defines": ["counter"], "instances": [], "includes": []},
        }
        graph = build_dependency_graph(analysis)
        assert graph["module_to_file"]["top"] == "top.v"
        assert graph["module_to_file"]["counter"] == "counter.v"
        assert "counter" in graph["dependencies"]["top"]
        assert graph["dependencies"]["counter"] == []

    def test_chain_dependency(self):
        """链式依赖"""
        analysis = {
            "top.v": {"defines": ["top"], "instances": ["alu"], "includes": []},
            "alu.v": {"defines": ["alu"], "instances": ["adder"], "includes": []},
            "adder.v": {"defines": ["adder"], "instances": [], "includes": []},
        }
        graph = build_dependency_graph(analysis)
        assert "alu" in graph["dependencies"]["top"]
        assert "adder" in graph["dependencies"]["alu"]


class TestTopologicalSort:
    """拓扑排序测试"""

    def test_simple_sort(self):
        """简单排序"""
        graph = {
            "module_to_file": {"top": "top.v", "counter": "counter.v"},
            "dependencies": {"top": ["counter"], "counter": []},
            "files": {},
        }
        order = topological_sort(graph)
        assert order.index("counter") < order.index("top")

    def test_no_dependencies(self):
        """无依赖"""
        graph = {
            "module_to_file": {"a": "a.v", "b": "b.v"},
            "dependencies": {"a": [], "b": []},
            "files": {},
        }
        order = topological_sort(graph)
        assert len(order) == 2

    def test_cycle_detection(self):
        """循环依赖检测"""
        graph = {
            "module_to_file": {"a": "a.v", "b": "b.v"},
            "dependencies": {"a": ["b"], "b": ["a"]},
            "files": {},
        }
        with pytest.raises(ValueError, match="循环依赖"):
            topological_sort(graph)


class TestDetectCycles:
    """循环检测测试"""

    def test_no_cycles(self):
        """无循环"""
        graph = {
            "module_to_file": {},
            "dependencies": {"a": ["b"], "b": []},
            "files": {},
        }
        cycles = detect_cycles(graph)
        assert len(cycles) == 0

    def test_simple_cycle(self):
        """简单循环"""
        graph = {
            "module_to_file": {},
            "dependencies": {"a": ["b"], "b": ["a"]},
            "files": {},
        }
        cycles = detect_cycles(graph)
        assert len(cycles) > 0


class TestFindUnusedModules:
    """未使用模块测试"""

    def test_find_unused(self):
        """查找未使用模块（未被任何模块实例化的模块）"""
        analysis = {
            "top.v": {"defines": ["top"], "instances": ["counter"], "includes": []},
            "counter.v": {"defines": ["counter"], "instances": [], "includes": []},
            "unused.v": {"defines": ["unused"], "instances": [], "includes": []},
        }
        unused = find_unused_modules(analysis)
        assert "unused" in unused
        assert "counter" not in unused  # 被 top 使用
        # 注意：top 也会被标记为未使用，因为没有其他模块实例化它
        # 这是正确的行为 - 需要用户指定顶层模块来排除

    def test_all_used(self):
        """所有模块都被使用"""
        analysis = {
            "top.v": {"defines": ["top"], "instances": ["alu"], "includes": []},
            "alu.v": {"defines": ["alu"], "instances": ["adder"], "includes": []},
            "adder.v": {"defines": ["adder"], "instances": [], "includes": []},
        }
        unused = find_unused_modules(analysis)
        # 只有 top 未被实例化（它是顶层模块）
        assert "alu" not in unused
        assert "adder" not in unused


class TestGetCompilationOrder:
    """编译顺序测试"""

    def test_order(self):
        """测试编译顺序"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # 创建测试文件
            (tmpdir_path / "top.v").write_text(
                "module top;\n  counter uut (.clk(clk));\nendmodule",
                encoding="utf-8",
            )
            (tmpdir_path / "counter.v").write_text(
                "module counter(clk);\nendmodule",
                encoding="utf-8",
            )

            files = [tmpdir_path / "top.v", tmpdir_path / "counter.v"]
            order = get_compilation_order(files)

            # counter 应该在 top 之前
            counter_idx = next(i for i, f in enumerate(order) if f.name == "counter.v")
            top_idx = next(i for i, f in enumerate(order) if f.name == "top.v")
            assert counter_idx < top_idx
