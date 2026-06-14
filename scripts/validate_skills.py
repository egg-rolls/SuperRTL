#!/usr/bin/env python3
"""
验证 Skills 文件格式

检查所有 shared/skills/*.md 文件是否包含有效的 YAML frontmatter。
"""

import re
import sys
from pathlib import Path


def validate_frontmatter(content: str, filename: str) -> list[str]:
    """验证 frontmatter 格式"""
    errors = []

    # 检查是否以 --- 开头
    if not content.startswith("---"):
        errors.append(f"{filename}: 缺少 YAML frontmatter (应以 --- 开头)")
        return errors

    # 匹配 frontmatter 块
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        errors.append(f"{filename}: frontmatter 格式错误 (未找到结束 ---)")
        return errors

    frontmatter = match.group(1)

    # 必需字段
    required_fields = ["name", "version", "description"]
    for field in required_fields:
        if not re.search(rf"^{field}:", frontmatter, re.MULTILINE):
            errors.append(f"{filename}: 缺少必需字段 '{field}'")

    # 验证 name 格式
    name_match = re.search(r'^name:\s*["\']?([^"\']+)', frontmatter, re.MULTILINE)
    if name_match:
        name = name_match.group(1).strip()
        if not re.match(r"^[a-z0-9-]+$", name):
            errors.append(f"{filename}: name '{name}' 格式错误 (应为小写字母、数字、连字符)")

    # 验证 version 格式
    version_match = re.search(r'^version:\s*["\']?([^"\']+)', frontmatter, re.MULTILINE)
    if version_match:
        version = version_match.group(1).strip()
        if not re.match(r"^\d+\.\d+\.\d+$", version):
            errors.append(f"{filename}: version '{version}' 格式错误 (应为 x.y.z)")

    # 验证 tags 格式
    tags_match = re.search(r"^tags:\s*\[(.+)\]", frontmatter, re.MULTILINE)
    if tags_match:
        tags_str = tags_match.group(1)
        # 简单验证列表格式
        if not re.match(r'^"[^"]+"(\s*,\s*"[^"]+")*$', tags_str):
            errors.append(f"{filename}: tags 格式错误 (应为 [\"tag1\", \"tag2\"])")

    return errors


def validate_skill_file(filepath: Path) -> list[str]:
    """验证单个 skill 文件"""
    errors = []

    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{filepath.name}: 读取失败: {e}")
        return errors

    # 验证 frontmatter
    errors.extend(validate_frontmatter(content, filepath.name))

    # 验证内容不为空
    match = re.match(r"^---\s*\n.*?\n---\s*\n(.*)", content, re.DOTALL)
    if match:
        body = match.group(1).strip()
        if len(body) < 50:
            errors.append(f"{filepath.name}: 内容过短 ({len(body)} 字符)")

    return errors


def main():
    """主函数"""
    # 找到 skills 目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    skills_dir = project_root / "shared" / "skills"

    if not skills_dir.exists():
        print(f"错误: skills 目录不存在: {skills_dir}")
        return 1

    # 验证所有 .md 文件
    all_errors = []
    skill_files = list(skills_dir.glob("*.md"))

    if not skill_files:
        print("警告: 没有找到 skill 文件")
        return 0

    print(f"验证 {len(skill_files)} 个 skill 文件...")

    for filepath in sorted(skill_files):
        errors = validate_skill_file(filepath)
        all_errors.extend(errors)

    # 输出结果
    if all_errors:
        print("\n验证失败:")
        for error in all_errors:
            print(f"  - {error}")
        return 1
    else:
        print("所有 skill 文件验证通过!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
