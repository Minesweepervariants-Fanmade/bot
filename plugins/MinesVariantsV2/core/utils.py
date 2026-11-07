"""通用工具：网络、子进程、系统状态、文件名与日志解析。"""
import ast
import asyncio
import os
import socket

import psutil

from .config import config_data, _log, cfg


def get_host_ip() -> str:
    """查询本机对内网地址，失败时回退到 127.0.0.1。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.147.19.0", 80))
        return s.getsockname()[0]
    except OSError as e:
        _log.warning(f"获取本机 IP 失败，回退 127.0.0.1: {e}")
        return "127.0.0.1"
    finally:
        s.close()


HOST_IP = get_host_ip()


async def run_command(command: str, cwd=None, input_str: str = None):
    """在指定目录执行 shell 命令。

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        if input_str:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate(input=input_str.encode("utf-8"))
        else:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
        return (
            process.returncode,
            stdout.decode("ansi", errors="replace") or " ",
            stderr.decode("ansi", errors="replace"),
        )
    except Exception as e:
        return -1, "", str(e)


async def wait_for_pid(request, timeout: float = 10.0, interval: float = 0.05) -> int:
    """异步等待 request 输出中出现 PID，返回 pid；超时或解析失败返回 -1。

    替代原先的 `while "PID" not in ...: time.sleep(0.1)` 忙等，
    既不阻塞事件循环，也不会无限等待。
    """
    deadline = asyncio.get_running_loop().time() + timeout
    while True:
        joined = "".join(request.output_buffer)
        if "PID" in joined:
            try:
                pid = int([i for i in request.output_buffer if "PID" in i][0]
                          .split("PID:[")[1].split("]")[0])
                request.pid = pid
                return pid
            except (IndexError, ValueError):
                return -1
        if asyncio.get_running_loop().time() >= deadline:
            return -1
        await asyncio.sleep(interval)


def get_system_stats(interval=None) -> str:
    """获取系统 CPU 和内存占用，返回格式化字符串。"""
    if interval is None:
        interval = config_data["interval"]
    cpu_percent = psutil.cpu_percent(interval=interval)
    mem = psutil.virtual_memory()
    return (
        f"CPU: {cpu_percent}% | MEM: {mem.percent}% "
        f"({mem.used // (1024 ** 2)}MB/{mem.total // (1024 ** 2)}MB)"
    )


def get_rule_image(file_name: str) -> str:
    """把规则名转成安全的图片文件名。"""
    file_name = file_name.replace("-", "--")
    file_name = file_name.replace("?", "-q")
    file_name = file_name.replace("*", "-a")
    file_name = file_name.replace("<", "-l")
    file_name = file_name.replace(">", "-g")
    file_name = file_name.replace("/", "-s")
    file_name = file_name.replace("\\", "-b")
    file_name = file_name.replace(":", "-c")
    return file_name


def parse_log_for_codes(log_path: str):
    """从 hint 日志中解析 board_code / answer_code / rules / total / used_r。

    Returns:
        tuple: (board_code, answer_code, rules_list, total, used_r)
    """
    board_code = ""
    answer_code = ""
    rules_list = []
    total = -1
    used_r = False
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for line in lines:
            if "|[BOARD]: " in line:
                board_code = line.split("|[BOARD]: ")[1].split("|", 1)[0].strip()
            elif "|[ANSWER_BOARD]: " in line:
                answer_code = line.split("|[ANSWER_BOARD]: ")[1].split("|", 1)[0].strip()
            elif "RULE:" in line and "EARLY_RULE:" in line:
                part = line.split("RULE:", 1)[1].split("EARLY_RULE:", 1)[0]
                rules_list = ast.literal_eval(part)
            elif "[TOTAL]:" in line:
                total = ast.literal_eval(line.split("[TOTAL]:", 1)[1].split("|", 1)[0])
            elif "[USED_R]:" in line:
                used_r = ast.literal_eval(line.split("[USED_R]:", 1)[1].strip())
    except Exception as e:
        _log.error(f"解析日志失败 {log_path}: {e}")
    return board_code, answer_code, rules_list, total, used_r


def split_by_content_length(items, max_len=None, chunk_max_length=None):
    if max_len is None:
        max_len = cfg("forward", "max_length", default=7000)
    if chunk_max_length is None:
        chunk_max_length = cfg("forward", "chunk_max_length", default=100)
    """按内容长度把消息节点切块，避免单条合并转发超限。"""
    chunks = []
    cur_chunk = []
    cur_len = 0
    for item in items:
        item_len = len(item.get("content", str(item)))
        if (cur_len + item_len > max_len and cur_chunk) or len(cur_chunk) >= chunk_max_length:
            chunks.append(cur_chunk)
            cur_chunk = [item]
            cur_len = item_len
        else:
            cur_chunk.append(item)
            cur_len += item_len
    if cur_chunk:
        chunks.append(cur_chunk)
    return chunks
