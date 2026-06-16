# 发布流程

## 版本号管理

版本号从 git tag 自动派生，**无需手动修改任何文件**。

```bash
# 自动递增版本号并创建 tag
python scripts/bump_version.py patch    # v0.5.0 -> v0.5.1
python scripts/bump_version.py minor    # v0.5.0 -> v0.6.0
python scripts/bump_version.py major    # v0.5.0 -> v1.0.0

# 创建 tag 并推送（触发自动发布）
python scripts/bump_version.py patch -p
```

## 发布步骤

```bash
# 1. 更新 CHANGELOG.md（手动）
#    添加新版本条目和底部比较链接

# 2. 提交
git add -A
git commit -m "docs: update changelog for v0.5.1"

# 3. 创建 tag 并推送
python scripts/bump_version.py patch -p
```

推送 tag 后，GitHub Actions 自动执行：

1. **测试** — 运行 pytest
2. **发布 PyPI** — 构建 wheel 并上传
3. **创建 GitHub Release** — 从 CHANGELOG.md 提取更新说明

## 工作原理

- `pyproject.toml` 使用 `hatch-vcs` 从 git tag 动态获取版本号
- `src/superrtl/__init__.py` 使用 `importlib.metadata.version()` 读取版本
- CI 构建时自动从最近的 tag 派生版本号
- 不需要手动修改任何版本文件

## Tag 规则

- 格式：`v{major}.{minor}.{patch}`（如 `v0.5.0`）
- 必须以 `v` 开头才能触发 release workflow
- 推送后不可撤销（PyPI 不允许重新上传同版本号）

## 版本号规范

遵循 [Semantic Versioning](https://semver.org/)：

- **MAJOR** (x.0.0): 不兼容的 API 变更
- **MINOR** (0.x.0): 新增功能，向后兼容
- **PATCH** (0.0.x): Bug 修复，向后兼容

## 发布前检查清单

- [ ] 所有测试通过：`pytest tests/ -v`
- [ ] Ruff 检查通过：`ruff check src/ tests/ && ruff format --check src/ tests/`
- [ ] CHANGELOG.md 已更新
- [ ] 文档已更新（如需要）

## 手动发布（备用）

```bash
python -m build
twine upload dist/*
```
