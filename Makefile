.PHONY: help install dev test lint format build clean bump-version

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装包
	pip install -e .

dev: ## 安装开发依赖
	pip install -e ".[dev]"

test: ## 运行测试
	pytest tests/ -v

test-cov: ## 运行测试并生成覆盖率报告
	pytest tests/ -v --cov=superrtl --cov-report=term-missing --cov-report=html

lint: ## 运行 linter
	ruff check src/ tests/

format: ## 格式化代码
	ruff format src/ tests/

build: ## 构建包
	python -m build

clean: ## 清理构建文件
	rm -rf build/ dist/ *.egg-info .pytest_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

bump-patch: ## 递增补丁版本号 (0.2.0 -> 0.2.1)
	python scripts/bump_version.py patch

bump-minor: ## 递增次版本号 (0.2.0 -> 0.3.0)
	python scripts/bump_version.py minor

bump-major: ## 递增主版本号 (0.2.0 -> 1.0.0)
	python scripts/bump_version.py major

setup: ## 安装 EDA 工具
	superrtl setup

check-tools: ## 检查 EDA 工具
	superrtl check-tools
