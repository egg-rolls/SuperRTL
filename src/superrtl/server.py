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


# ============ Prompts 定义 ============


# Skills 作为 Prompts 暴露
SKILL_PROMPTS = {
    "design-fsm": {
        "description": "FSM 设计助手 - 帮助设计有限状态机",
        "arguments": [
            {"name": "spec", "description": "状态机规格描述", "required": True},
            {"name": "style", "description": "编码风格 (one-hot, binary, gray)", "required": False},
        ],
    },
    "design-fifo": {
        "description": "FIFO 设计助手 - 帮助设计同步/异步 FIFO",
        "arguments": [
            {"name": "type", "description": "FIFO 类型 (sync, async)", "required": True},
            {"name": "width", "description": "数据宽度", "required": True},
            {"name": "depth", "description": "深度", "required": True},
        ],
    },
    "design-uart": {
        "description": "UART 设计助手 - 帮助设计串口通信模块",
        "arguments": [
            {"name": "baud_rate", "description": "波特率", "required": True},
            {"name": "clk_freq", "description": "时钟频率", "required": True},
        ],
    },
    "design-cdc": {
        "description": "CDC 设计助手 - 帮助解决跨时钟域问题",
        "arguments": [
            {
                "name": "signal_type",
                "description": "信号类型 (single, multi, bus)",
                "required": True,
            },
        ],
    },
    "review-code": {
        "description": "代码审查助手 - 审查 Verilog 代码质量",
        "arguments": [
            {"name": "code", "description": "要审查的代码", "required": True},
            {
                "name": "focus",
                "description": "关注点 (timing, area, power, all)",
                "required": False,
            },
        ],
    },
    "generate-testbench": {
        "description": "Testbench 生成助手 - 自动生成测试平台",
        "arguments": [
            {"name": "code", "description": "设计代码", "required": True},
            {"name": "style", "description": "测试风格 (basic, comprehensive)", "required": False},
        ],
    },
}


@app.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    """列出所有可用的 Prompts"""
    prompts = []

    for name, config in SKILL_PROMPTS.items():
        arguments = []
        for arg in config.get("arguments", []):
            arguments.append(
                types.PromptArgument(
                    name=arg["name"],
                    description=arg["description"],
                    required=arg.get("required", False),
                )
            )

        prompts.append(
            types.Prompt(
                name=name,
                description=config["description"],
                arguments=arguments,
            )
        )

    return prompts


@app.get_prompt()
async def get_prompt(name: str, arguments: dict) -> types.GetPromptResult:
    """获取 Prompt 内容"""
    try:
        if name not in SKILL_PROMPTS:
            return types.GetPromptResult(
                description=f"未知 Prompt: {name}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"错误: 未知的 Prompt '{name}'",
                        ),
                    )
                ],
            )

        config = SKILL_PROMPTS[name]

        # 根据 Prompt 类型生成内容
        if name == "design-fsm":
            skill_content = await get_skill("fsm")
            prompt_text = f"""你是一个 Verilog FSM 设计专家。

用户需求: {arguments.get("spec", "未指定")}
编码风格: {arguments.get("style", "one-hot")}

参考以下设计模式:
{skill_content}

请根据用户需求设计一个 FSM，包含：
1. 状态定义
2. 状态转换图
3. 完整的 Verilog 代码
4. Testbench"""

        elif name == "design-fifo":
            fifo_type = arguments.get("type", "sync")
            skill_name = f"fifo_{fifo_type}" if fifo_type == "async" else "fifo_sync"
            skill_content = await get_skill(skill_name)
            prompt_text = f"""你是一个 Verilog FIFO 设计专家。

FIFO 类型: {arguments.get("type", "sync")}
数据宽度: {arguments.get("width", "8")}
深度: {arguments.get("depth", "16")}

参考以下设计模式:
{skill_content}

请设计一个满足要求的 FIFO，包含：
1. 参数化设计
2. 满/空标志
3. 完整的 Verilog 代码
4. Testbench"""

        elif name == "design-uart":
            skill_content = await get_skill("uart")
            prompt_text = f"""你是一个 Verilog UART 设计专家。

波特率: {arguments.get("baud_rate", "115200")}
时钟频率: {arguments.get("clk_freq", "50000000")}

参考以下设计模式:
{skill_content}

请设计一个完整的 UART 模块，包含：
1. 波特率发生器
2. TX 发送器
3. RX 接收器
4. 顶层模块
5. Testbench"""

        elif name == "design-cdc":
            skill_content = await get_skill("cdc")
            prompt_text = f"""你是一个 CDC (Clock Domain Crossing) 设计专家。

信号类型: {arguments.get("signal_type", "single")}

参考以下设计模式:
{skill_content}

请提供 CDC 解决方案，包含：
1. 同步器设计
2. 握手协议（如需要）
3. 异步 FIFO（如需要）
4. 完整的 Verilog 代码"""

        elif name == "review-code":
            prompt_text = f"""你是一个 Verilog 代码审查专家。

请审查以下代码:
```
{arguments.get("code", "")}
```

关注点: {arguments.get("focus", "all")}

请检查：
1. 语法错误
2. 可综合性问题
3. 时序问题
4. 面积优化
5. 功耗优化
6. 编码规范
7. 潜在的 Bug"""

        elif name == "generate-testbench":
            prompt_text = f"""你是一个 Verilog Testbench 生成专家。

请为以下代码生成 Testbench:
```
{arguments.get("code", "")}
```

测试风格: {arguments.get("style", "basic")}

请生成：
1. 时钟和复位生成
2. 测试激励
3. 自检查逻辑
4. 波形输出配置
5. 超时保护"""

        else:
            prompt_text = f"未知 Prompt: {name}"

        return types.GetPromptResult(
            description=config["description"],
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=prompt_text),
                )
            ],
        )

    except Exception as e:
        return types.GetPromptResult(
            description=f"错误: {str(e)}",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(type="text", text=f"获取 Prompt 失败: {str(e)}"),
                )
            ],
        )


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
