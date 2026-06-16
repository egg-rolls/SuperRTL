#!/usr/bin/env python3
"""
版本号管理脚本

版本号从 git tag 自动派生，无需手动修改文件。

用法:
    python scripts/bump_version.py patch      # v0.5.0 -> v0.5.1
    python scripts/bump_version.py minor      # v0.5.0 -> v0.6.0
    python scripts/bump_version.py major      # v0.5.0 -> v1.0.0
    python scripts/bump_version.py 0.5.1      # 指定版本
    python scripts/bump_version.py patch -p   # 创建 tag 并推送
"""

import subprocess
import sys


def get_latest_tag() -> str:
    """获取最新的 git tag"""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "v0.0.0"


def bump_version(current: str, part: str) -> str:
    """递增版本号"""
    version = current.lstrip("v")
    major, minor, patch = map(int, version.split("."))

    if part == "major":
        return f"v{major + 1}.0.0"
    elif part == "minor":
        return f"v{major}.{minor + 1}.0"
    elif part == "patch":
        return f"v{major}.{minor}.{patch + 1}"
    else:
        if not part.startswith("v"):
            part = f"v{part}"
        return part


def tag_exists(tag: str) -> bool:
    """检查 tag 是否存在"""
    result = subprocess.run(
        ["git", "tag", "-l", tag],
        capture_output=True, text=True,
    )
    return bool(result.stdout.strip())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    part = sys.argv[1]
    current = get_latest_tag()
    new_version = bump_version(current, part)

    if tag_exists(new_version):
        print(f"错误: tag {new_version} 已存在")
        sys.exit(1)

    print(f"当前版本: {current}")
    print(f"新版本:   {new_version}")

    subprocess.run(["git", "tag", "-a", new_version, "-m", f"Release {new_version}"], check=True)
    print(f"已创建 tag: {new_version}")

    if "--push" in sys.argv or "-p" in sys.argv:
        subprocess.run(["git", "push", "origin", new_version], check=True)
        print(f"已推送 tag: {new_version}")
        print("GitHub Actions 将自动发布到 PyPI")
    else:
        print(f"\n下一步: git push origin {new_version}")


if __name__ == "__main__":
    main()
