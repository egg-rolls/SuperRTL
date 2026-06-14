"""
波形查看器 HTTP 服务

提供轻量级 Web 波形查看器，支持 VCD 文件的交互式浏览。
"""

import json
import re
import socket
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread


def _find_free_port(start: int = 8080, max_tries: int = 100) -> int:
    """查找可用端口"""
    for port in range(start, start + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found in range {start}-{start + max_tries}")


def _parse_vcd_to_json(content: str) -> dict:
    """解析 VCD 文件为 JSON 格式（供前端使用）"""
    result = {
        "success": True,
        "timescale": "1ns",
        "signals": {},
        "time_range": {"start": 0, "end": 0},
    }

    current_time = 0
    signal_map = {}  # id -> name
    scope_stack = []  # 层次结构栈

    for line in content.splitlines():
        line = line.strip()

        # 解析时间刻度
        if "$timescale" in line:
            match = re.search(r"\$timescale\s+(.+?)\s+\$end", content)
            if match:
                result["timescale"] = match.group(1).strip()

        # 解析层次
        elif line.startswith("$scope"):
            match = re.match(r"\$scope\s+\w+\s+(\S+)\s+\$end", line)
            if match:
                scope_stack.append(match.group(1))

        elif line.startswith("$upscope"):
            if scope_stack:
                scope_stack.pop()

        # 解析信号定义
        elif line.startswith("$var"):
            match = re.match(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)", line)
            if match:
                width = int(match.group(1))
                sig_id = match.group(2)
                sig_name = match.group(3)
                # 构建完整路径
                full_name = ".".join(scope_stack + [sig_name]) if scope_stack else sig_name
                signal_map[sig_id] = full_name
                result["signals"][full_name] = {"width": width, "values": []}

        # 解析时间
        elif line.startswith("#"):
            try:
                current_time = int(line[1:])
                result["time_range"]["end"] = max(result["time_range"]["end"], current_time)
            except ValueError:
                pass

        # 解析信号值变化
        elif line and line[0] in "01xzXZ":
            value = line[0]
            sig_id = line[1:].strip() if len(line) > 1 else ""
            if sig_id in signal_map:
                sig_name = signal_map[sig_id]
                if sig_name in result["signals"]:
                    result["signals"][sig_name]["values"].append(
                        {"time": current_time, "value": value}
                    )

        # 多位信号
        elif line.startswith("b"):
            parts = line.split()
            if len(parts) >= 2:
                value = parts[0][1:]  # 去掉 'b' 前缀
                sig_id = parts[1]
                if sig_id in signal_map:
                    sig_name = signal_map[sig_id]
                    if sig_name in result["signals"]:
                        result["signals"][sig_name]["values"].append(
                            {"time": current_time, "value": value}
                        )

    return result


class WaveformHandler(SimpleHTTPRequestHandler):
    """波形查看器 HTTP 请求处理器"""

    vcd_data = None  # 类变量，存储解析后的 VCD 数据

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self._serve_viewer()
        elif self.path == "/api/data":
            self._serve_data()
        elif self.path == "/api/signals":
            self._serve_signals()
        else:
            self.send_error(404)

    def _serve_viewer(self):
        """返回波形查看器 HTML 页面"""
        viewer_path = (
            Path(__file__).parent.parent.parent.parent / "shared" / "waveform" / "viewer.html"
        )

        # 开发模式回退
        if not viewer_path.exists():
            viewer_path = (
                Path(__file__).parent.parent.parent / "shared" / "waveform" / "viewer.html"
            )

        if not viewer_path.exists():
            self.send_error(500, "viewer.html not found")
            return

        content = viewer_path.read_text(encoding="utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _serve_data(self):
        """返回 VCD 数据 JSON"""
        if self.vcd_data is None:
            self._send_json({"success": False, "error": "No VCD data loaded"})
            return
        self._send_json(self.vcd_data)

    def _serve_signals(self):
        """返回信号列表（支持搜索）"""
        if self.vcd_data is None:
            self._send_json({"success": False, "error": "No VCD data loaded"})
            return

        # 获取搜索参数
        query = self.path.split("?")[1] if "?" in self.path else ""
        filter_param = ""
        for param in query.split("&"):
            if param.startswith("q="):
                filter_param = param[2:].lower()

        signals = []
        for name, data in self.vcd_data.get("signals", {}).items():
            if filter_param and filter_param not in name.lower():
                continue
            signals.append(
                {
                    "name": name,
                    "width": data["width"],
                    "value_count": len(data["values"]),
                }
            )

        self._send_json({"success": True, "signals": signals})

    def _send_json(self, data: dict):
        """发送 JSON 响应"""
        content = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content.encode("utf-8"))))
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def log_message(self, format, *args):
        """禁用 HTTP 日志"""
        pass


def start_waveform_server(
    vcd_file: str,
    port: int = 0,
    auto_open: bool = True,
) -> dict:
    """
    启动波形查看器 HTTP 服务

    Args:
        vcd_file: VCD 文件路径
        port: HTTP 端口 (0 = 自动选择)
        auto_open: 是否自动打开浏览器

    Returns:
        服务信息字典
    """
    vcd_path = Path(vcd_file)
    if not vcd_path.exists():
        return {"success": False, "error": f"VCD file not found: {vcd_file}"}

    try:
        content = vcd_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": f"Failed to read VCD file: {e}"}

    # 解析 VCD 数据
    vcd_data = _parse_vcd_to_json(content)
    vcd_data["source_file"] = str(vcd_path.absolute())

    # 设置类变量
    WaveformHandler.vcd_data = vcd_data

    # 查找可用端口
    if port == 0:
        port = _find_free_port()

    # 创建服务器
    server = HTTPServer(("127.0.0.1", port), WaveformHandler)

    # 在后台线程运行服务器
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    url = f"http://127.0.0.1:{port}"

    # 自动打开浏览器
    if auto_open:
        webbrowser.open(url)

    signal_count = len(vcd_data.get("signals", {}))

    return {
        "success": True,
        "url": url,
        "port": port,
        "signal_count": signal_count,
        "time_range": vcd_data.get("time_range", {}),
    }
