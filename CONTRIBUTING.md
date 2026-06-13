# 贡献指南

感谢你对 SuperRTL 项目的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 1. Fork 仓库

点击 [SuperRTL](https://github.com/egg-rolls/SuperRTL) 页面右上角的 **Fork** 按钮。

### 2. 克隆你的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/SuperRTL.git
cd SuperRTL
```

### 3. 添加上游仓库

```bash
git remote add upstream https://github.com/egg-rolls/SuperRTL.git
```

### 4. 创建功能分支

```bash
git checkout -b feature/your-feature-name
```

分支命名规范：
- `feature/xxx` - 新功能
- `fix/xxx` - Bug 修复
- `docs/xxx` - 文档更新
- `refactor/xxx` - 代码重构

### 5. 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/ -v

# 代码检查
ruff check src/ tests/
ruff format src/ tests/
```

### 6. 提交更改

```bash
git add -A
git commit -m "feat: add amazing feature"
```

提交信息格式：

```
<type>: <description>

[optional body]

[optional footer]
```

类型说明：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具相关

示例：

```
feat: add waveform export to SVG format

- Add SVG export function in waveform.py
- Add --format option to waveform command
- Update documentation

Closes #123
```

### 7. 推送到你的 Fork

```bash
git push origin feature/your-feature-name
```

### 8. 创建 Pull Request

1. 打开你的 Fork 页面
2. 点击 **Compare & pull request**
3. 填写 PR 描述
4. 点击 **Create pull request**

## 代码规范

### Python 风格

- 使用 Python 3.10+ 语法
- 行长度：100 字符
- 使用 ruff 进行代码检查和格式化

### 类型注解

```python
# ✅ 推荐
def compile_verilog(code: str, top_module: str = "") -> dict:
    ...

# ❌ 避免
def compile_verilog(code, top_module=""):
    ...
```

### 文档字符串

```python
def function_name(param1: str, param2: int) -> dict:
    """
    函数简短描述

    Args:
        param1: 参数1说明
        param2: 参数2说明

    Returns:
        返回值说明

    Raises:
        ValueError: 异常说明
    """
```

### 测试

- 新功能必须包含测试
- Bug 修复必须包含回归测试
- 确保所有测试通过

```bash
# 运行测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_compile.py -v

# 查看覆盖率
pytest tests/ --cov=superrtl --cov-report=term-missing
```

## 报告 Bug

使用 [Bug Report](https://github.com/egg-rolls/SuperRTL/issues/new?template=bug_report.md) 模板。

## 提出功能

使用 [Feature Request](https://github.com/egg-rolls/SuperRTL/issues/new?template=feature_request.md) 模板。

## 行为准则

- 尊重所有参与者
- 接受建设性批评
- 专注于对社区最有利的事情
- 对他人表示同理心

## 问题？

如有疑问，请在 [Discussions](https://github.com/egg-rolls/SuperRTL/discussions) 中提问。
