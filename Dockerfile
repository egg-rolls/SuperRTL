# SuperRTL Docker 镜像
# 包含完整的 EDA 工具链（Icarus Verilog、Yosys、Verilator）

FROM python:3.12-slim AS base

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 OSS CAD Suite
FROM base AS eda-tools

# 设置工具安装目录
ENV EDA_TOOLS_DIR=/opt/eda-tools
RUN mkdir -p ${EDA_TOOLS_DIR}

# 下载并安装 OSS CAD Suite
# 使用缓存层以加速构建
RUN cd ${EDA_TOOLS_DIR} && \
    wget -q --no-check-certificate \
    https://github.com/YosysHQ/oss-cad-suite-build/releases/latest/download/oss-cad-suite-linux-x64-20260613.tgz \
    -O oss-cad-suite.tgz && \
    tar xzf oss-cad-suite.tgz && \
    rm oss-cad-suite.tgz

# 设置 PATH
ENV PATH="${EDA_TOOLS_DIR}/oss-cad-suite/bin:${PATH}"

# 验证工具安装
RUN iverilog -V && yosys -V && verilator --version

# 最终镜像
FROM eda-tools AS final

# 安装 Python 依赖
WORKDIR /app

# 复制项目文件
COPY pyproject.toml .
COPY src/ src/
COPY shared/ shared/
COPY examples/ examples/
COPY docs/ docs/

# 安装 SuperRTL
RUN pip install --no-cache-dir -e .

# 验证安装
RUN superrtl --version && superrtl check-tools

# 创建工作目录
WORKDIR /workspace

# 暴露端口（用于 SSE 模式）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD superrtl check-tools || exit 1

# 默认命令：启动 MCP Server
CMD ["superrtl", "mcp"]
