# 发布流程

## 自动发布（推荐）

以 `v0.5.0` 为例：

```bash
# 1. 更新版本号
# pyproject.toml: version = "0.5.0"
# src/superrtl/__init__.py: __version__ = "0.5.0"

# 2. 更新 CHANGELOG.md
# 添加 [0.5.0] 条目和底部比较链接

# 3. 提交
git add -A
git commit -m "chore: bump version to 0.5.0"

# 4. 打 tag（必须以 v 开头）
git tag v0.5.0

# 5. 推送
git push origin main
git push origin v0.5.0
```

推送 tag 后，GitHub Actions 自动执行：

1. **测试** — 运行 pytest
2. **发布 PyPI** — 构建 wheel 并上传（需要 PyPI trusted publishing 配置）
3. **创建 GitHub Release** — 从 CHANGELOG.md 提取对应版本的更新说明

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
- [ ] 版本号已更新：`pyproject.toml` + `__init__.py`
- [ ] CHANGELOG.md 已更新（新增版本条目 + 底部比较链接）
- [ ] 文档已更新（如 README.md 有新功能说明）

## 手动发布（备用）

如果 GitHub Actions 失败，可以手动发布：

```bash
# 构建
python -m build

# 上传到 PyPI
twine upload dist/*
```

## PyPI 配置

项目使用 [Trusted Publishing](https://docs.pypi.org/trusted-publishers/)，无需 API token。

配置位置：PyPI 项目设置 → Publishing → GitHub Actions
