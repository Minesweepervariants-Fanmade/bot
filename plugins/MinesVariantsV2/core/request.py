"""TCP 任务执行器：连接本地 31408 服务，按 LINE/BIN 模式收集输出。"""
import datetime
import os
import socket
import subprocess
import threading
from typing import Literal

from .config import response, config_data, _log, cfg


class Request:
    def __init__(self, max_length=0, _request_id=0, task_type: Literal["MINES", "DEEPSEEK"] = "MINES"):
        self.mode = None
        self.output_buffer = []
        self.max_length = max_length
        self.request_id = _request_id
        self._thread = None
        self._socket = None
        self._should_stop = threading.Event()
        self._lock = threading.Lock()
        self._completed = threading.Event()
        self.pid = -1
        self.task_type = task_type

        timestamp = datetime.datetime.now().timestamp()
        dt_object = datetime.datetime.fromtimestamp(timestamp)
        self.start_time = dt_object.strftime("%m/%d %H:%M")
        self.data = ""
        self.nickname = ""

    def clone(self):
        request = Request(self.max_length, self.request_id)
        request.start_time = self.start_time
        request.data = self.data
        request.nickname = self.nickname
        request.output_buffer = self.output_buffer
        return request

    def run_task(self, args: str, host: str = "local", mode="LINE") -> None:
        """启动新线程运行任务（异步执行）。"""
        self.mode = mode
        self._thread = threading.Thread(target=self._run_task, args=(args,), daemon=True)
        self._thread.start()

    def send_input(self, text: str) -> None:
        """向服务端发送交互输入（自动追加换行符）。"""
        if self._socket:
            try:
                self._socket.sendall((text + "\n").encode("utf-8"))
            except Exception as e:
                _log.warning(f"发送输入失败: {e}")

    def _run_task(self, args: str, host: str = None, port: int = None) -> None:
        """实际执行任务的线程函数（按行接收）。"""
        host = host or cfg("socket", "host", default="localhost")
        port = port or cfg("socket", "port", default=31408)
        recv_size = cfg("socket", "recv_size", default=4096)
        line_buffer = ""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            self._socket = client

            init_data = client.recv(4)
            if init_data != b"14mv":
                raise ConnectionError("无效的服务器握手信号")

            client.sendall(args.encode("utf-8"))

            while not self._should_stop.is_set():
                try:
                    client.settimeout(1)
                    data = client.recv(recv_size)
                    if not data:
                        break

                    decoded = data.decode("utf-8", errors="replace")
                    line_buffer += decoded

                    lines = line_buffer.split("\n")
                    line_buffer = lines[-1]
                    complete_lines = lines[:-1]

                    with self._lock:
                        if self.mode == "BIN":
                            if len(self.output_buffer) == 0:
                                self.output_buffer.append(data)
                            else:
                                self.output_buffer[0] += data
                        elif self.mode == "LINE":
                            for line in complete_lines:
                                self.output_buffer.append(line)

                    if "Exit Code" in decoded:
                        break

                except socket.timeout:
                    continue
                except ConnectionResetError:
                    with self._lock:
                        self.output_buffer.append("\n" + response("system", "connection_closed"))
                    break
                except UnicodeDecodeError:
                    with self._lock:
                        self.output_buffer.append("\n" + response("system", "binary_data"))
                except OSError as e:
                    if self._should_stop.is_set():
                        break
                    with self._lock:
                        self.output_buffer.append("\n" + response("system", "connection_error").format(str(e)))
                    break

            if line_buffer and not self._should_stop.is_set():
                with self._lock:
                    self.output_buffer.append(line_buffer)

            with self._lock:
                if self.max_length > 0:
                    while len(self.output_buffer) > self.max_length:
                        self.output_buffer.pop(0)

        except Exception as e:
            _log.error(f"任务 {self.request_id} 执行异常: {e}", exc_info=True)
            with self._lock:
                self.output_buffer.append("\n" + response("system", "running_error") + str(e))
        finally:
            self._socket = None
            self._completed.set()

    def close_connection(self) -> None:
        """关闭连接并停止任务线程。"""
        if self.task_type == "DEEPSEEK":
            if self.pid == -1:
                return
            import psutil
            try:
                parent = psutil.Process(self.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        pass
                parent.kill()
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                _log.warning(f"强杀 DEEPSEEK 进程 {self.pid} 失败: {e}")
            subprocess.run(
                "stop.bat",
                cwd=cfg("deepseek", "work_dir", default=r"D:\0.0\lib\ds-browser"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=None,
                shell=True,
            )
            self.pid = -1
            self._completed.set()
            return
        self._should_stop.set()

        if self._socket:
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
            except Exception:
                pass
            finally:
                self._socket = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=cfg("thread_join_timeout", default=1.0))

        self.output_buffer = []
        self._completed.set()

    def __del__(self):
        self.close_connection()

    def get_output(self) -> str:
        """获取当前输出内容（线程安全）。"""
        if self.task_type == "DEEPSEEK":
            log_dir = cfg("deepseek", "log_path", default=config_data.get("deepseek_log_path"))
            main_log = os.path.join(log_dir, "logs\\latest-main.log")
            test_log = os.path.join(log_dir, "logs\\latest-test.log")

            main_exists = os.path.exists(main_log)
            test_exists = os.path.exists(test_log)
            if not main_exists:
                return response("task", "log_not_ready")

            content = ""
            if main_exists:
                with open(main_log, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

            if test_exists:
                with open(test_log, "r", encoding="utf-8", errors="ignore") as f:
                    test_content = f.read()
                content = content + "\n" + test_content
            return content
        with self._lock:
            if self.mode == "LINE":
                return "\n".join(self.output_buffer)
            elif self.mode == "BIN":
                return self.output_buffer[0].decode("utf-8")
        return ""

    def is_completed(self) -> bool:
        return self._completed.is_set()

    def wait_completion(self, timeout=None) -> bool:
        return self._completed.wait(timeout)
