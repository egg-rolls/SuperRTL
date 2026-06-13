"""
EDA 工具安装管理

支持从 GitHub 下载 OSS CAD Suite（包含 iverilog、yosys、verilator）
"""

import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path
from urllib.request import urlretrieve

import click
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TransferSpeedColumn

from .runtime import get_oss_cad_suite_dir, get_tools_dir, tools_installed

console = Console()

# OSS CAD Suite 下载配置
RELEASE_BASE = "https://github.com/YosysHQ/oss-cad-suite-build/releases/latest/download"

# 平台映射 (platform, machine) -> filename pattern
PLATFORM_MAP = {
    ("win32", "AMD64"): "oss-cad-suite-windows-x64-{version}.exe",
    ("win32", "x86_64"): "oss-cad-suite-windows-x64-{version}.exe",
    ("linux", "x86_64"): "oss-cad-suite-linux-x64-{version}.tgz",
    ("linux", "aarch64"): "oss-cad-suite-linux-arm64-{version}.tgz",
    ("darwin", "x86_64"): "oss-cad-suite-darwin-x64-{version}.tgz",
    ("darwin", "arm64"): "oss-cad-suite-darwin-arm64-{version}.tgz",
}

# 最新版本号（可以通过 API 动态获取）
DEFAULT_VERSION = "20260613"


def get_platform_key() -> tuple:
    """获取平台标识"""
    return (sys.platform, platform.machine())


def get_latest_version() -> str:
    """获取最新版本号"""
    try:
        import json
        from urllib.request import urlopen

        url = "https://api.github.com/repos/YosysHQ/oss-cad-suite-build/releases/latest"
        with urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            tag = data["tag_name"]  # 格式: "2026-06-13"
            return tag.replace("-", "")
    except Exception:
        return DEFAULT_VERSION


def get_download_url(version: str = None) -> tuple:
    """获取下载 URL"""
    if version is None:
        version = get_latest_version()

    key = get_platform_key()
    pattern = PLATFORM_MAP.get(key)

    if not pattern:
        raise click.ClickException(f"不支持的平台: {key[0]} ({key[1]})")

    filename = pattern.format(version=version)
    return f"{RELEASE_BASE}/{filename}", filename


def download_file(url: str, dest: Path) -> None:
    """下载文件（带进度条）"""
    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
    ) as progress:
        task = progress.add_task("下载中...", total=None)

        def hook(count: int, block: int, total: int) -> None:
            if total > 0:
                progress.update(task, total=total, completed=count * block)

        urlretrieve(url, str(dest), reporthook=hook)


def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """解压归档文件"""
    if archive_path.suffix == ".tgz" or archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path=dest_dir)
    elif archive_path.suffix == ".exe":
        # Windows .exe 是自解压文件
        result = subprocess.run(
            [str(archive_path), f"-o{dest_dir}", "-y"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise click.ClickException(f"解压失败: {result.stderr}")
    else:
        raise click.ClickException(f"不支持的归档格式: {archive_path.suffix}")


def install_tools(force: bool = False) -> None:
    """
    安装 EDA 工具

    Args:
        force: 强制重新安装
    """
    tools_dir = get_tools_dir()
    oss_dir = get_oss_cad_suite_dir()

    # 检查是否已安装
    if tools_installed() and not force:
        console.print("[green]EDA 工具已安装[/green]")
        console.print(f"  位置: {oss_dir}")
        return

    # 创建目录
    tools_dir.mkdir(parents=True, exist_ok=True)

    # 获取下载 URL
    try:
        url, filename = get_download_url()
    except click.ClickException as e:
        console.print(f"[red]错误: {e}[/red]")
        return

    archive_path = tools_dir / filename

    console.print("[blue]SuperRTL EDA 工具安装[/blue]")
    console.print(f"  平台: {get_platform_key()[0]} ({get_platform_key()[1]})")
    console.print(f"  目标: {oss_dir}")
    console.print()

    try:
        # 下载
        console.print("[blue]下载中...[/blue]")
        console.print(f"  {url}")
        download_file(url, archive_path)
        console.print("[green]下载完成[/green]")

        # 解压
        console.print("[blue]解压中...[/blue]")
        extract_archive(archive_path, tools_dir)
        console.print("[green]解压完成[/green]")

        # 清理归档文件
        archive_path.unlink(missing_ok=True)

        # 验证安装
        if tools_installed():
            console.print()
            console.print("[green]安装成功！[/green]")
            console.print(f"  工具位置: {oss_dir}/bin/")
            console.print()
            console.print("现在可以使用以下命令：")
            console.print("  superrtl compile design.v")
            console.print("  superrtl simulate design.v testbench.v")
            console.print("  superrtl lint design.v")
            console.print("  superrtl synthesize design.v")
        else:
            console.print("[yellow]安装完成，但工具验证失败[/yellow]")
            console.print("  请检查目录结构是否正确")

    except Exception as e:
        # 清理失败的安装
        if archive_path.exists():
            archive_path.unlink()
        raise click.ClickException(f"安装失败: {e}")


def uninstall_tools() -> None:
    """卸载 EDA 工具"""
    tools_dir = get_tools_dir()

    if not tools_dir.exists():
        console.print("[yellow]工具未安装[/yellow]")
        return

    shutil.rmtree(tools_dir)
    console.print("[green]工具已卸载[/green]")


def check_tools() -> dict:
    """检查工具安装状态"""
    from .runtime import get_tools_status

    status = get_tools_status()

    console.print("[blue]EDA 工具状态[/blue]")
    console.print()

    all_ok = True
    for tool, info in status.items():
        if info["installed"]:
            console.print(f"  [green]+[/green] {tool}: {info['name']}")
        else:
            console.print(f"  [red]-[/red] {tool}: {info['name']}")
            all_ok = False

    console.print()

    if all_ok:
        console.print("[green]所有工具已安装[/green]")
    else:
        console.print("[yellow]部分工具未安装[/yellow]")
        console.print("  运行 [bold]superrtl setup[/bold] 安装")

    return status
