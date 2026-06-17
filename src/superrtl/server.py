"""
SuperRTL MCP Server

提供 Verilog EDA 工具的 MCP 接口
"""

import asyncio
import json

from mcp import types
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp.server.stdio import stdio_server

from .resources import get_skill, get_template, list_skills, list_templates
from .tools import (
    analyze_waveform,
    compile_verilog,
    formal_verify,
    lint_verilog,
    review_verilog,
    simulate_parallel,
    simulate_verilog,
    synthesize_verilog,
    verify_design,
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
                "timeout": {
                    "type": "integer",
                    "description": "编译超时时间 (秒)",
                    "default": 30,
                },
            },
        },
    ),
    types.Tool(
        name="simulate_verilog",
        description="运行 Verilog 仿真。支持文件路径或代码字符串，AI 可自行生成文件后传入路径",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "设计文件代码（单文件模式）"},
                "design_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "多个设计文件代码列表（多文件模式）",
                },
                "design_file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "多个设计文件路径列表（文件模式）",
                },
                "testbench": {"type": "string", "description": "测试平台代码字符串"},
                "testbench_file": {
                    "type": "string",
                    "description": "测试平台文件路径（优先于 testbench）",
                },
                "timeout": {"type": "integer", "description": "仿真超时时间 (秒)", "default": 30},
            },
        },
    ),
    types.Tool(
        name="lint_verilog",
        description="使用 Verilator 进行 Lint 检查。支持代码字符串或文件路径。",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "file": {"type": "string", "description": "Verilog 文件路径（优先于 code）"},
                "style": {
                    "type": "string",
                    "description": "检查风格",
                    "enum": ["default", "strict", "relaxed"],
                    "default": "default",
                },
            },
        },
    ),
    types.Tool(
        name="synthesize_verilog",
        description="使用 Yosys 进行综合检查",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "file": {"type": "string", "description": "Verilog 文件路径（优先于 code）"},
                "top_module": {"type": "string", "description": "顶层模块名", "default": ""},
                "target": {
                    "type": "string",
                    "description": "目标工艺库",
                    "enum": ["generic", "xilinx", "ice40"],
                    "default": "generic",
                },
            },
        },
    ),
    types.Tool(
        name="analyze_waveform",
        description="分析 VCD 波形文件（支持协议解码和覆盖率计算）",
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
                "compute_coverage": {
                    "type": "boolean",
                    "description": "是否计算翻转覆盖率",
                    "default": False,
                },
                "protocol": {
                    "type": "string",
                    "enum": ["spi", "i2c", "uart"],
                    "description": "协议解码类型",
                },
                "protocol_config": {
                    "type": "object",
                    "description": "协议配置参数 (如 cpol/cpha/bits/baud 等)",
                },
            },
        },
    ),
    types.Tool(
        name="formal_verify",
        description="使用 SymbiYosys 进行形式验证 (BMC 模型检查)",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Verilog 源代码（需包含 assert/assume/cover）",
                },
                "file": {
                    "type": "string",
                    "description": "Verilog 文件路径（优先于 code）",
                },
                "top_module": {"type": "string", "description": "顶层模块名", "default": ""},
                "depth": {
                    "type": "integer",
                    "description": "BMC 搜索深度",
                    "default": 20,
                },
                "timeout": {
                    "type": "integer",
                    "description": "验证超时时间 (秒)",
                    "default": 300,
                },
                "solver": {
                    "type": "string",
                    "description": "SMT solver 引擎",
                    "enum": ["yices", "boolector", "z3"],
                    "default": "yices",
                },
            },
        },
    ),
    types.Tool(
        name="review_verilog",
        description="审查 Verilog 代码。支持代码字符串或文件路径。",
        inputSchema={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Verilog 源代码"},
                "file": {"type": "string", "description": "Verilog 文件路径（优先于 code）"},
                "checks": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": [
                            "synthesizability",
                            "latch",
                            "naming",
                            "reset",
                            "case",
                        ],
                    },
                    "description": "要执行的检查类别 (默认全部)",
                },
            },
        },
    ),
    types.Tool(
        name="verify_design",
        description="综合验证：一键运行 compile + simulate + lint + review",
        inputSchema={
            "type": "object",
            "properties": {
                "design_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "设计文件路径列表",
                },
                "testbench_file": {
                    "type": "string",
                    "description": "测试平台文件路径",
                },
                "testbench": {
                    "type": "string",
                    "description": "测试平台代码字符串",
                },
                "top_module": {"type": "string", "description": "顶层模块名", "default": ""},
                "timeout": {
                    "type": "integer",
                    "description": "仿真超时 (秒)",
                    "default": 60,
                },
                "skip": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["compile", "simulate", "lint", "review"],
                    },
                    "description": "要跳过的步骤",
                },
            },
            "required": ["design_files"],
        },
    ),
    types.Tool(
        name="simulate_parallel",
        description="并行仿真：多个 testbench 同时运行，加速回归测试",
        inputSchema={
            "type": "object",
            "properties": {
                "design_file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "设计文件路径列表",
                },
                "testbench_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "测试平台文件路径列表",
                },
                "timeout": {
                    "type": "integer",
                    "description": "每个仿真的超时 (秒)",
                    "default": 30,
                },
                "max_concurrent": {
                    "type": "integer",
                    "description": "最大并发数",
                    "default": 4,
                },
            },
            "required": ["design_file_paths", "testbench_files"],
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
                code=code,
                files=files,
                top_module=arguments.get("top_module", ""),
                timeout=arguments.get("timeout", 30),
            )
        elif name == "simulate_verilog":
            # 支持 code（单文件）或 design_files/design_file_paths（多文件）
            result = await simulate_verilog(
                code=arguments.get("code"),
                testbench=arguments.get("testbench"),
                testbench_file=arguments.get("testbench_file"),
                timeout=arguments.get("timeout", 30),
                design_files=arguments.get("design_files"),
                design_file_paths=arguments.get("design_file_paths"),
            )
        elif name == "lint_verilog":
            result = await lint_verilog(
                code=arguments.get("code"),
                style=arguments.get("style", "default"),
                file=arguments.get("file"),
                timeout=arguments.get("timeout", 30),
            )
        elif name == "synthesize_verilog":
            result = await synthesize_verilog(
                code=arguments.get("code"),
                top_module=arguments.get("top_module", ""),
                target=arguments.get("target", "generic"),
                file=arguments.get("file"),
            )
        elif name == "analyze_waveform":
            result = await analyze_waveform(
                arguments.get("vcd_file"),
                arguments.get("vcd_content"),
                arguments.get("signals"),
                compute_coverage=arguments.get("compute_coverage", False),
                protocol=arguments.get("protocol"),
                protocol_config=arguments.get("protocol_config"),
            )
        elif name == "formal_verify":
            result = await formal_verify(
                code=arguments.get("code"),
                top_module=arguments.get("top_module", ""),
                depth=arguments.get("depth", 20),
                timeout=arguments.get("timeout", 300),
                file=arguments.get("file"),
                solver=arguments.get("solver", "yices"),
            )
        elif name == "review_verilog":
            result = await review_verilog(
                code=arguments.get("code"),
                checks=arguments.get("checks"),
                file=arguments.get("file"),
            )
        elif name == "verify_design":
            result = await verify_design(
                design_files=arguments.get("design_files"),
                testbench_file=arguments.get("testbench_file"),
                testbench=arguments.get("testbench"),
                top_module=arguments.get("top_module", ""),
                timeout=arguments.get("timeout", 60),
                skip=arguments.get("skip"),
            )
        elif name == "simulate_parallel":
            result = await simulate_parallel(
                design_file_paths=arguments.get("design_file_paths"),
                testbench_files=arguments.get("testbench_files"),
                timeout=arguments.get("timeout", 30),
                max_concurrent=arguments.get("max_concurrent", 4),
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
async def read_resource(uri) -> str:
    """读取资源内容"""
    try:
        # MCP 库可能传入 AnyUrl 对象，转为字符串处理
        uri_str = str(uri)
        if uri_str.startswith("skills://"):
            skill_name = uri_str.replace("skills://", "")
            return await get_skill(skill_name)
        elif uri_str.startswith("templates://"):
            template_name = uri_str.replace("templates://", "")
            return await get_template(template_name)
        else:
            return json.dumps({"error": f"未知资源 URI: {uri_str}"}, ensure_ascii=False)
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
        "description": "Testbench 编写助手 - 分析设计语义，指导 AI 编写有意义的测试",
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
            prompt_text = f"""你是一个 Verilog 验证专家。请为以下设计编写有意义的 Testbench。

设计代码:
```
{arguments.get("code", "")}
```

测试风格: {arguments.get("style", "basic")}

要求：
1. 分析设计的功能语义（不只是端口列表）
2. 编写有意义的测试场景（不是随机值）
3. 包含自检查断言（assert 或 $display PASS/FAIL）
4. 覆盖正常路径和边界情况
5. 时钟/复位/波形输出/超时保护

写完后，将 testbench 保存为文件，然后调用:
simulate_verilog(design_file_paths=[...], testbench_file=...)
运行验证。"""

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


def _get_init_options():
    """获取服务器初始化选项"""
    from . import __version__

    return InitializationOptions(
        server_name="superrtl",
        server_version=__version__,
        capabilities=app.get_capabilities(
            NotificationOptions(),
            experimental_capabilities={},
        ),
    )


async def run_stdio():
    """以 stdio 模式运行 (用于 MCP Host 连接)"""
    async with stdio_server() as (read, write):
        await app.run(read, write, _get_init_options())


async def run_sse(host: str = "127.0.0.1", port: int = 8000):
    """以 SSE 模式运行 (Server-Sent Events 远程传输)

    端点:
        GET  /sse  — SSE 事件流
        POST /messages — 客户端消息
    """
    try:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Route
    except ImportError:
        raise ImportError(
            "远程 MCP 模式需要安装额外依赖。请运行:\n"
            "  pip install superrtl[remote]\n"
            "或:\n"
            "  pip install starlette uvicorn"
        ) from None

    sse_transport = SseServerTransport("/messages")

    async def handle_sse(request: Request):
        async with sse_transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await app.run(streams[0], streams[1], _get_init_options())

    async def handle_messages(request: Request):
        await sse_transport.handle_post_message(
            request.scope, request.receive, request._send
        )

    async def handle_health(request: Request):
        return Response('{"status":"ok","transport":"sse"}', media_type="application/json")

    starlette_app = Starlette(
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/sse", endpoint=handle_sse),
            Route("/messages", endpoint=handle_messages, methods=["POST"]),
        ],
    )

    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def run_streamable_http(host: str = "127.0.0.1", port: int = 8000):
    """以 Streamable HTTP 模式运行 (推荐的远程传输方式)

    端点:
        POST /mcp — 统一的 MCP 请求端点
    """
    import contextlib
    import uuid

    try:
        import uvicorn
        from mcp.server.streamable_http import StreamableHTTPServerTransport
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Route
    except ImportError:
        raise ImportError(
            "远程 MCP 模式需要安装额外依赖。请运行:\n"
            "  pip install superrtl[remote]\n"
            "或:\n"
            "  pip install starlette uvicorn"
        ) from None

    @contextlib.asynccontextmanager
    async def lifespan(app_ref):
        """管理服务器生命周期"""
        yield

    async def handle_mcp(request: Request):
        transport = StreamableHTTPServerTransport(
            mcp_session_id=str(uuid.uuid4()),
            is_json_response_enabled=True,
        )
        async with transport.connect() as streams:
            run_task = asyncio.create_task(
                app.run(streams[0], streams[1], _get_init_options())
            )
            try:
                await transport.handle_request(
                    request.scope, request.receive, request._send
                )
            finally:
                run_task.cancel()
                try:
                    await run_task
                except asyncio.CancelledError:
                    pass

    async def handle_health(request: Request):
        return Response(
            '{"status":"ok","transport":"streamable-http"}',
            media_type="application/json",
        )

    starlette_app = Starlette(
        lifespan=lifespan,
        routes=[
            Route("/health", endpoint=handle_health),
            Route("/mcp", endpoint=handle_mcp, methods=["POST", "GET", "DELETE"]),
        ],
    )

    config = uvicorn.Config(starlette_app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main(transport: str = "stdio", host: str = "127.0.0.1", port: int = 8000):
    """主入口

    Args:
        transport: 传输模式 (stdio/sse/streamable-http)
        host: 监听地址 (仅远程模式)
        port: 监听端口 (仅远程模式)
    """
    from .logging import setup_logging

    setup_logging(level="info")

    if transport == "stdio":
        asyncio.run(run_stdio())
    elif transport == "sse":
        asyncio.run(run_sse(host, port))
    elif transport == "streamable-http":
        asyncio.run(run_streamable_http(host, port))
    else:
        raise ValueError(f"不支持的传输模式: {transport}")


if __name__ == "__main__":
    main()
