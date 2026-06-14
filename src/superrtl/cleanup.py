"""
资源清理模块

提供临时文件清理、上下文管理器和信号处理。
"""

import atexit
import signal
import tempfile
from pathlib import Path


class TempDirManager:
    """临时目录管理器"""

    def __init__(self):
        self._temp_dirs: list[Path] = []
        self._registered = False

    def create(self, suffix: str = None) -> Path:
        """创建临时目录

        Args:
            suffix: 目录名后缀

        Returns:
            临时目录路径
        """
        tmpdir = Path(tempfile.mkdtemp(suffix=suffix))
        self._temp_dirs.append(tmpdir)

        # 注册清理回调
        if not self._registered:
            atexit.register(self.cleanup_all)
            self._register_signal_handlers()
            self._registered = True

        return tmpdir

    def cleanup(self, path: Path):
        """清理指定目录

        Args:
            path: 要清理的目录路径
        """
        import shutil

        try:
            if path.exists():
                shutil.rmtree(path)
            if path in self._temp_dirs:
                self._temp_dirs.remove(path)
        except Exception:
            pass  # 清理失败不影响主流程

    def cleanup_all(self):
        """清理所有临时目录"""
        for tmpdir in self._temp_dirs[:]:
            self.cleanup(tmpdir)

    def _register_signal_handlers(self):
        """注册信号处理器"""
        try:
            # SIGINT (Ctrl+C)
            original_sigint = signal.getsignal(signal.SIGINT)

            def handler(signum, frame):
                self.cleanup_all()
                if callable(original_sigint):
                    original_sigint(signum, frame)
                else:
                    raise KeyboardInterrupt()

            signal.signal(signal.SIGINT, handler)

            # SIGTERM
            original_sigterm = signal.getsignal(signal.SIGTERM)

            def term_handler(signum, frame):
                self.cleanup_all()
                if callable(original_sigterm):
                    original_sigterm(signum, frame)

            signal.signal(signal.SIGTERM, term_handler)

        except (OSError, ValueError):
            # 某些平台可能不支持某些信号
            pass


# 全局实例
_temp_manager = TempDirManager()


def get_temp_manager() -> TempDirManager:
    """获取全局临时目录管理器"""
    return _temp_manager


def create_temp_dir(suffix: str = None) -> Path:
    """创建临时目录（使用全局管理器）

    Args:
        suffix: 目录名后缀

    Returns:
        临时目录路径
    """
    return _temp_manager.create(suffix)


def cleanup_temp_dir(path: Path):
    """清理临时目录（使用全局管理器）

    Args:
        path: 要清理的目录路径
    """
    _temp_manager.cleanup(path)


class ManagedTempDir:
    """临时目录上下文管理器

    Usage:
        with ManagedTempDir() as tmpdir:
            # 使用 tmpdir
            pass
        # 退出时自动清理
    """

    def __init__(self, suffix: str = None):
        self.suffix = suffix
        self.path: Path | None = None

    def __enter__(self) -> Path:
        self.path = create_temp_dir(self.suffix)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path:
            cleanup_temp_dir(self.path)
        return False


class ManagedFile:
    """文件上下文管理器

    Usage:
        with ManagedFile("output.v", content) as path:
            # 使用 path
            pass
        # 退出时自动清理
    """

    def __init__(self, filename: str, content: str, dir: Path = None):
        self.filename = filename
        self.content = content
        self.dir = dir
        self.path: Path | None = None

    def __enter__(self) -> Path:
        if self.dir:
            self.path = self.dir / self.filename
        else:
            tmpdir = create_temp_dir()
            self.path = tmpdir / self.filename

        self.path.write_text(self.content, encoding="utf-8")
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.path and self.path.exists():
            try:
                self.path.unlink()
            except Exception:
                pass
        return False
