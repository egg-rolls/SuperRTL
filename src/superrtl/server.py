"""
SuperRTL MCP Server

提供 Verilog EDA 工具的 MCP 接口
"""

import asyncio
import json

from mcp import types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .resources import get_skill, get_template, list_skills, list_templates
from .tools import (
    analyze_waveform,
    compile_verilog,
    generate_testbench,
    lint_verilog,
    simulate_verilog,
    synthesize_verilog,
)

# 创建 MCP Server 实例
app = Server("superrtl")


# ============ Tools 定义 ============

TOOLS = [
    types.Tool(
        name="compile_verilog",
        description="使用 Icarus Verilog 编译 Verilog 代码（支持单文件或多文件）",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码（单文件模式）"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "多个设计文件代码列表（多文件模式）",
                },
                "top_module": {"type": "string", "description": "顶层模块名 (可选)", "default": ""},
            },
        },
    ),
    types.Tool(
        name="simulate_verilog",
        description="使用 Icarus Verilog 运行仿真（支持单文件或多文件）",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "设计文件代码（单文件模式）"},
                "design_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "多个设计文件代码列表（多文件模式）",
                },
                "testbench": {"type": "string", "description": "测试平台代码"},
                "timeout": {"type": "integer", "description": "仿真超时时间 (秒)", "default": 30},
            },
            "required": ["testbench"],
        },
    ),
    types.Tool(
        name="lint_verilog",
        description="使用 Verilator 进行 Lint 检查",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "style": {
                    "type": "string",
                    "description": "检查风格",
                    "enum": ["default", "strict", "relaxed"],
                    "default": "default",
                },
            },
            "required": ["code"],
        },
    ),
    types.Tool(
        name="synthesize_verilog",
        description="使用 Yosys 进行综合检查",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "top_module": {"type": "string", "description": "顶层模块名", "default": ""},
                "target": {
                    "type": "string",
                    "description": "目标工艺库",
                    "enum": ["generic", "xilinx", "ice40"],
                    "default": "generic",
                },
            },
            "required": ["code"],
        },
    ),
    types.Tool(
        name="generate_testbench",
        description="自动生成 Testbench",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "style": {
                    "type": "string",
                    "description": "测试风格",
                    "enum": ["basic", "comprehensive"],
                    "default": "basic",
                },
                "test_cases": {"type": "integer", "description": "测试用例数量", "default": 3},
            },
            "required": ["code"],
        },
    ),
    types.Tool(
        name="analyze_waveform",
        description="分析 VCD 波形文件",
        inputSchema={
            "type": "object",
            "properties": {
                "vcd_file": {"type": "string", "description": "VCD 文件路径"},
                "vcd_content": {"type": "string", "description": "VCD 内容 (直接传入)"},
                "signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "要分析的信号列表",
                },
            },
        },
    ),
]


# ============ 注册处理器 ============


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    """列出所有可用的工具"""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """处理工具调用"""
    try:
        if name == "compile_verilog":
            # 支持 code（单文件）或 files（多文件）
            files = arguments.get("files")
            code = arguments.get("code")
            result = await compile_verilog(
                code=code, files=files, top_module=arguments.get("top_module", "")
            )
        elif name == "simulate_verilog":
            # 支持 code（单文件）或 design_files（多文件）
            code = arguments.get("code")
            design_files = arguments.get("design_files")
            result = await simulate_verilog(
                code=code,
                testbench=arguments["testbench"],
                timeout=arguments.get("timeout", 30),
                design_files=design_files,
            )
        elif name == "lint_verilog":
            result = await lint_verilog(arguments["code"], arguments.get("style", "default"))
        elif name == "synthesize_verilog":
            result = await synthesize_verilog(
                arguments["code"],
                arguments.get("top_module", ""),
                arguments.get("target", "generic"),
            )
        elif name == "generate_testbench":
            result = await generate_testbench(
                arguments["code"], arguments.get("style", "basic"), arguments.get("test_cases", 3)
            )
        elif name == "analyze_waveform":
            result = await analyze_waveform(
                arguments.get("vcd_file"), arguments.get("vcd_content"), arguments.get("signals")
            )
        else:
            result = {"success": False, "error": f"未知工具: {name}"}

        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, ensure_ascii=False),
            )
        ]


# ============ Resources 定义 ============


@app.list_resources()
async def list_resources() -> list[types.Resource]:
    """列出所有可用的资源"""
    resources = []

    # Skills
    skills_data = json.loads(await list_skills())
    for skill in skills_data.get("skills", []):
        skill_name = skill.get("display_name", skill.get("name", ""))
        description = skill.get("description", f"Verilog 设计模式: {skill_name}")
        resources.append(
            types.Resource(
                uri=f"skills://{skill_name}",
                name=f"Skill: {skill_name}",
                description=description,
                mimeType="text/markdown",
            )
        )

    # Templates
    templates_data = json.loads(await list_templates())
    for template in templates_data.get("templates", []):
        resources.append(
            types.Resource(
                uri=f"templates://{template}",
                name=f"Template: {template}",
                description=f"Verilog 代码模板: {template}",
                mimeType="text/plain",
            )
        )

    return resources


@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    try:
        if uri.startswith("skills://"):
            skill_name = uri.replace("skills://", "")
            return await get_skill(skill_name)
        elif uri.startswith("templates://"):
            template_name = uri.replace("templates://", "")
            return await get_template(template_name)
        else:
            return json.dumps({"error": f"未知资源 URI: {uri}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ============ 启动函数 ============


async def run_stdio():
    """以 stdio 模式运行 (用于 MCP Host 连接)"""
    async with stdio_server() as (read, write):
        await app.run(read, write)


def main():
    """主入口"""
    asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
