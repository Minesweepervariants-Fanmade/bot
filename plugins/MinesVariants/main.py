import asyncio
import os
import pathlib
import random
import re
import subprocess
import time
from pathlib import Path
import socket
import threading
import datetime
from typing import Union
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
import regex
import requests
import yaml
import base64
from ncatbot.core.api import check_and_log

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils import logger
import json


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.147.19.0', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip


async def run_command(command: str, cwd=None):
    """
    在指定目录下执行命令并返回输出

    Args:
        command (str or list): 要执行的命令
        cwd (str): 工作目录路径，如果为None则在当前目录执行

    Returns:
        tuple: (returncode, stdout, stderr)
    """
    try:
        # 执行命令
        # process = subprocess.Popen(
        #     command,
        #     cwd=cwd,
        #     stdout=subprocess.PIPE,
        #     stderr=subprocess.PIPE,
        #     text=True,
        #     shell=isinstance(command, str)  # 如果命令是字符串，则使用shell
        # )
        process = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # 获取输出
        stdout, stderr = await process.communicate()

        return process.returncode, stdout.decode("ansi") or " ", stderr.decode("ansi")

    except Exception as e:
        return -1, "", str(e)


def response(*key: str) -> str:
    result = yaml.full_load(open(f"{SELF_PATH}/response.yaml", "r", encoding="utf-8"))
    for _key in key:
        result = result[_key]
    if type(result) is list:
        result = random.choice(result)
    return result


def update_all_rules():
    global ALL_RULE
    request = None
    for _ in range(6):
        request = Request()
        request.run_task("list --json", mode="BIN")
        request.wait_completion(timeout=10)
    result = request.get_output().split("\n")[1]
    # print(request.get_output(), result)
    with open(f"{SELF_PATH}/rule.json", 'w', encoding="utf-8") as f:
        f.write(result)
    _log.info("发起更新规则列表")
    ALL_RULE = []
    return True


def get_system_stats(interval=None) -> str:
    """获取系统 CPU 和内存占用，返回格式化字符串"""
    import psutil
    if interval is None:
        interval = config_data["interval"]
    cpu_percent = psutil.cpu_percent(interval=interval)  # 1秒采样，避免瞬时波动
    mem = psutil.virtual_memory()
    return f"CPU: {cpu_percent}% | MEM: {mem.percent}% ({mem.used // (1024 ** 2)}MB/{mem.total // (1024 ** 2)}MB)"


def get_rule_image(file_name: str):
    file_name = file_name.replace("-", "--")
    file_name = file_name.replace('?', '-q')
    file_name = file_name.replace('*', '-a')
    file_name = file_name.replace('<', '-l')
    file_name = file_name.replace('>', '-g')
    file_name = file_name.replace('/', '-s')
    file_name = file_name.replace('\\', '-b')
    file_name = file_name.replace(':', '-c')
    return file_name


SELF_PATH = Path(__file__).parent.__str__()

_log = logger.get_log()
bot = CompatibleEnrollment
config_data: dict = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))

request_map: dict[int, "Request"] = {}
HOST_IP = get_host_ip()
ALL_RULE = []  # {name: [], doc: "..."}, ...

NICK_NAME = response("users", "default_bot", "nickname")
USER_ID = response("users", "default_bot", "id")


def pck(content, image="", user_id=USER_ID, nickname=NICK_NAME) -> list:
    if type(content) is str:
        content = [{"type": "text", "data": {"text": content}}]
        if image and os.path.exists(image):
            with open(image, "rb") as f:
                image = "base64://" + base64.b64encode(f.read()).decode('utf-8')
            content.append({"type": "image", "data": {"file": image}})
        if os.path.exists(image):
            print(content)
        _message = {"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": content}}
        return [_message]
    elif type(content) is list:
        _message = []
        for _text in content:
            _text = pck(_text)
            _message.extend(_text)
        _message = {"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": _message}}
        return [_message]
    elif type(content) is dict:
        uid = content.get("uid", USER_ID)
        name = content.get("name", NICK_NAME)
        image = content.get("image", "")
        content = content["content"]
        __result = pck(content, image=image, user_id=uid, nickname=name)
        return __result
    else:
        return []


class Request:
    def __init__(self, max_length=0, _request_id=0):
        self.mode = None
        self.output_buffer = []
        self.max_length = max_length
        self.request_id = _request_id
        self._thread = None
        self._socket = None
        self._should_stop = threading.Event()
        self._lock = threading.Lock()  # 用于保护output_buffer的线程安全
        self._completed = threading.Event()
        self.pid = -1

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
        """
        启动新线程运行任务（异步执行）

        参数:
            args: 传递的参数字符串
            host: 目标主机
            mode: BIN / LINE
        """
        self.mode = mode
        self._thread = threading.Thread(
            target=self._run_task, args=(args,), daemon=True
        )
        self._thread.start()

    def _run_task(self, args: str,
                  host: str = "localhost",
                  port: int = 31408) -> None:
        """实际执行任务的线程函数"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            self._socket = client  # 保存socket引用用于关闭

            # 接收初始握手信号
            init_data = client.recv(4)
            if init_data != b'14mv':
                raise ConnectionError("无效的服务器握手信号")

            # 发送参数
            client.sendall(args.encode('utf-8'))

            # 持续接收数据
            while not self._should_stop.is_set():
                try:
                    # 设置超时以定期检查停止标志
                    client.settimeout(1)
                    data = client.recv(4096)
                    if not data:  # 正常断开
                        break

                    decoded = data.decode('utf-8', errors='replace')
                    with self._lock:
                        if self.mode == "BIN":
                            if len(self.output_buffer) == 0:
                                self.output_buffer.append(data)
                            else:
                                self.output_buffer[0] += data
                        elif self.mode == "LINE":
                            self.output_buffer.append(decoded)

                    if "Exit Code" in decoded:
                        break

                except socket.timeout:
                    # 超时后继续循环检查停止标志
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
                        # 如果是主动关闭导致的错误，正常退出
                        break
                    with self._lock:
                        self.output_buffer.append("\n" + response("system", "connection_error").format(str(e)))
                    break

            # 维护缓冲区长度
            with self._lock:
                if self.max_length > 0:
                    while len(self.output_buffer) > self.max_length:
                        self.output_buffer.pop(0)

        except Exception as e:
            print(str(e))
            with self._lock:
                self.output_buffer.append("\n" + response("system", "running_error") + str(e))
        finally:
            self._socket = None
            self._completed.set()

    def close_connection(self) -> None:
        """关闭连接并停止任务线程"""
        self._should_stop.set()

        # 关闭socket中断阻塞操作
        if self._socket:
            try:
                # 强制关闭socket
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
            except:
                pass
            finally:
                self._socket = None

        # 等待线程结束
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

        self.output_buffer = []
        self._completed.set()

    def __del__(self):
        self.close_connection()

    def get_output(self) -> str:
        """获取当前输出内容（线程安全）"""
        with self._lock:
            if self.mode == "LINE":
                return '\n'.join(self.output_buffer)
            elif self.mode == "BIN":
                return self.output_buffer[0].decode('utf-8')

    def is_completed(self) -> bool:
        """检查任务是否已完成"""
        return self._completed.is_set()

    def wait_completion(self, timeout=None) -> bool:
        """等待任务完成（可设置超时）"""
        return self._completed.wait(timeout)


class MinesVariants(BasePlugin):
    name = "MinesVariants"
    version = "0.0.0"

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        print("[PRI]", msg.user_id, ":", msg.raw_message[:20].replace("\n", ""), end="\r")
        try:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()
            if not command:
                return
            match command[0]:
                case "#生成" | "#sc" | "#summon" | "#run":
                    self.data["id"] += 1
                    request_map[self.data["id"]] = Request(max_length=50, _request_id=self.data["id"])
                    request_map[self.data["id"]].nickname = msg.sender.nickname
                    threading.Thread(
                        target=self.thread_target, daemon=True,
                        args=(msg, command[:], request_map[self.data["id"]])
                    ).start()
                    # time.sleep(1)
                    if self.data["id"] in request_map:
                        await self.api.post_private_msg(
                            msg.user_id, response("task", "created").format(self.data["id"])
                        )
                case "#所有规则" | "#规则列表" | "#list":
                    await self.rule_list(msg)
                case "#查询规则" | "#cxr":
                    await self.search_rule(msg)
                case "#log":
                    if len(command) > 1:
                        await self.get_log(msg, command[1])
                    else:
                        await self.api.post_private_msg(msg.user_id, response("prompts", "log_format_error"))
                case "#查询" | "#cx":
                    await self.query_thread(msg)
                case "#帮助" | "#help" | "#?":
                    HELP_TEXT = yaml.full_load(open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8"))
                    await self.send_private_forward_msg_text(HELP_TEXT, msg)
                case "#状态" | "#state" | "##":
                    await self.state(msg)
                case "#终止" | "#kill" | "#k":
                    await self.kill_thread(command, msg)
                case "#pull":
                    await self.pull(msg)
                case "#update":
                    await self.api.post_private_msg(msg.user_id, response("categories", "update_start"))
                    if update_all_rules():
                        await self.api.post_private_msg(msg.user_id, response("categories", "update_end"))
                    else:
                        await self.api.post_private_msg(msg.user_id, response("categories", "update_fail"))
                case "#":  # 综合
                    await self.shape(msg)
                    return
                case _:
                    await self.shape(msg, raw_message[1:].split())
            # _log.warning(f"Received empty or invalid command: {msg.raw_message}")
        except Exception as e:
            _log.error(f"Error in on_private_event: {e}", exc_info=True)
            # try:
            #     await self.api.post_private_msg(
            #         msg.user_id, 
            #         f"处理命令时发生错误: {str(e)}. 请检查命令格式或稍后再试。"
            #     )
            # except Exception as send_error:
            #     _log.error(f"Failed to send error message: {send_error}")

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        print("[GUP]", msg.group_id, ":", msg.raw_message[:20].replace("\n", ""), end="\r")
        try:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()
            if not raw_message.startswith("#"):
                return

            # if command:
            #     command[0] = command[0][1:]

            if not command:
                return
            match command[0]:
                case "#生成" | "#sc" | "#summon" | "#run":
                    self.data["id"] += 1
                    self.data.save()
                    request_map[self.data["id"]] = Request(max_length=50, _request_id=self.data["id"])
                    request_map[self.data["id"]].nickname = msg.sender.nickname
                    threading.Thread(
                        target=self.thread_target, daemon=True,
                        args=(msg, command[:], request_map[self.data["id"]])
                    ).start()
                    # time.sleep(1)
                    if self.data["id"] in request_map:
                        await self.api.post_group_msg(
                            msg.group_id, response("task", "created").format(self.data["id"])
                        )
                case "#update":
                    await self.api.post_group_msg(msg.group_id, response("categories", "update_start"))
                    if update_all_rules():
                        await self.api.post_group_msg(msg.group_id, response("categories", "update_end"))
                    else:
                        await self.api.post_group_msg(msg.group_id, response("categories", "update_fail"))
                case "#所有规则" | "#规则列表" | "#list" | "#ls":
                    await self.rule_list(msg)
                case "#查询规则" | "#cxr":
                    await self.search_rule(msg)
                case "#查询" | "#cx":
                    await self.query_thread(msg)
                case "#帮助" | "#help" | "#?":
                    try:
                        HELP_TEXT = yaml.full_load(open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8"))
                        await self.send_group_forward_msg_text(HELP_TEXT, msg)
                    except Exception as e:
                        _log.error(f"Failed to load help file: {e}")
                        if command[0] == "#帮助":
                            error_msg = "无法加载帮助文件，请稍后再试。"
                        else:
                            error_msg = "Failed to load help file, please try again later."
                        await self.api.post_group_msg(msg.group_id, error_msg)
                case "#log":
                    if len(command) > 1:
                        await self.get_log(msg, command[1])
                    else:
                        await self.api.post_group_msg(msg.group_id, response("prompts", "log_format_error"))
                case "#状态" | "#state" | "##":
                    await self.state(msg)
                case "#终止" | "#kill" | "#k":
                    await self.kill_thread(command, msg)
                case "#pull":
                    await self.pull(msg)
                case "#cmd" | "#$":
                    if "admin" not in self.data:
                        self.data["admin"] = [3140864122]
                    if msg.user_id not in self.data["admin"]:
                        await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
                        return
                    await self.command(' '.join(command[1:]), msg)
                case "#注册规则" | "#reg":
                    command = msg.raw_message.split(" ", 2)
                    if len(command) == 3:
                        # 注册新规则
                        rule_doc = "".join(
                            [data["data"]["text"] for data in msg.message if data["type"] == "text"]
                        ).split(" ", 2)[-1]
                        await self.register_rules(msg, command[1], rule_doc)
                    elif len(command) == 2:
                        # 删除规则
                        await self.register_rules(msg, command[1], "")
                    else:
                        await self.api.post_group_msg(msg.group_id, response("rules", "register_fmt_error"))
                case "#op":
                    if "admin" not in self.data:
                        self.data["admin"] = [3140864122]
                    if msg.user_id not in self.data["admin"]:
                        await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
                        return
                    if len(msg.message) < 2:
                        await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
                        return
                    target = msg.message[1]
                    if target.get("type", None) != "at":
                        await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
                        return
                    target = int(target["data"]["qq"])
                    if target in self.data["admin"]:
                        await self.api.post_group_msg(msg.group_id, response("command", "target_is_admin"))
                        return
                    self.data["admin"].append(target)
                    await self.api.post_group_msg(msg.group_id, response("command", "op_done"))
                case "#deop":
                    if "admin" not in self.data:
                        self.data["admin"] = [3140864122]
                    if len(msg.message) < 2:
                        await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
                        return
                    target = msg.message[1]
                    if target.get("type", None) != "at":
                        await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
                        return
                    target = int(target["data"]["qq"])
                    if target == 3140864122:
                        await self.api.post_group_msg(msg.group_id, response("command", "target_is_master"))
                        return
                    if msg.user_id not in self.data["admin"]:
                        await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
                        return
                    if target not in self.data["admin"]:
                        await self.api.post_group_msg(msg.group_id, response("command", "target_not_admin"))
                        return
                    self.data["admin"].remove(target)
                    await self.api.post_group_msg(msg.group_id, response("command", "deop_done"))
                case "#del":
                    if "admin" not in self.data:
                        self.data["admin"] = [3140864122]
                    if msg.user_id not in self.data["admin"]:
                        return
                    if not msg.message[0]["type"] == "reply":
                        return
                    message_id = msg.message[0]["data"]["id"]
                    await self.api.delete_msg(message_id)
                    await self.api.delete_msg(msg.message_id)
                case "#":  # 综合
                    await self.shape(msg)
                    return
                case _:
                    await self.shape(msg, raw_message[1:].split())

                # _log.warning(f"Received empty or invalid command in group {msg.group_id}: {msg.raw_message}")
        except Exception as e:
            _log.error(f"Error in on_group_event: {e}", exc_info=True)
            try:
                await self.api.post_group_msg(
                    msg.group_id,
                    f"处理命令时发生错误: {str(e)}。"
                )
            except Exception as send_error:
                _log.error(f"Failed to send error message to group: {send_error}")
                if msg.user_id not in self.data["admin"]:
                    await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
                # await self.command(command[1:], msg)

    async def shape(self, msg, command=None):
        # sc/cx/##
        if command is None:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()[1:]
        if len(command) == 0:  # 如果只有单个#表示状态
            await self.state(msg)
        elif command[0].isdigit():
            # 如果第一个是数字
            if int(command[0]) < 1000 and "/f" not in command:
                self.data["id"] += 1
                self.data.save()
                request_map[self.data["id"]] = Request(max_length=50, _request_id=self.data["id"])
                request_map[self.data["id"]].nickname = msg.sender.nickname
                threading.Thread(
                    target=self.thread_target, daemon=True,
                    args=(msg, ["#"] + command[:], request_map[self.data["id"]])
                ).start()
                # time.sleep(1)
                if self.data["id"] in request_map:
                    await self.send_message(
                        msg, response("task", "created").format(self.data["id"])
                    )
            else:
                # cx进程
                await self.query_thread(msg, [""] + command)
        else:
            # 如果不是数字就是查询规则
            await self.search_rule(msg, [""] + command)

    async def get_log(self, msg: PrivateMessage | GroupMessage, log_id: str = None):
        if log_id is None:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()
            if len(command) < 2:
                await self.api.post_group_msg(msg.group_id, response("prompts", "log_format_error"))
                return
            log_id = command[1]
            if not log_id.isdigit():
                await self.api.post_group_msg(msg.group_id, response("prompts", "log_id_format_error"))
                return
        log_id = int(log_id)
        log_path = f"{config_data['log_path']}/{log_id}.log"
        if not os.path.exists(log_path):
            await self.api.post_group_msg(msg.group_id, response("prompts", "log_unfind_error"))
            return

        remote_host = "root@10.147.19.3"
        remote_dir = "/napcat/data"
        container_file_path = f"/app/data/{log_id}.log"

        # 上传文件到宿主机
        subprocess.run(
            ["scp", log_path, f"{remote_host}:{remote_dir}"],
            stdout=subprocess.DEVNULL,  # 丢弃标准输出
            stderr=subprocess.DEVNULL   # 丢弃标准错误
        )

        # 发送文件：使用容器内本地路径
        if isinstance(msg, GroupMessage):
            await self.api.post_group_file(msg.group_id, file=container_file_path)
        elif isinstance(msg, PrivateMessage):
            # 注意：私聊发送文件的方法名可能是 post_private_file，请根据你的 API 确认
            await self.api.post_private_file(msg.user_id, file=container_file_path)

        # 清理远程文件
        subprocess.run(["ssh", remote_host, f"rm {remote_dir}/{log_id}.log"], text=True)

    async def send_message(self, msg, message: str, reply=None, image_path=None):
        image = None
        if image_path:
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    image = "base64://" + base64.b64encode(f.read()).decode('utf-8')
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, message, reply=reply, image=image)
        else:
            await self.api.post_private_msg(msg.user_id, message, reply=reply, image=image)
        return

    async def register_rules(self, msg, name, doc):
        reply = None
        _response = None
        if msg.message[0]["type"] == "reply":
            reply = msg.message[0]["data"]["id"]
            reply_msgs = await self.api.get_msg(reply)
            for reply_msg_part in reply_msgs["data"]["message"]:
                if reply_msg_part["type"] == "image":
                    img_url = reply_msg_part["data"]["url"]
                    _response = requests.get(img_url)
                    break
        rule_todo: list[dict] = json.load(open(f"{SELF_PATH}/fanmade_doc/rule/ruleTodo.json", "r", encoding="utf-8"))
        rule_data = None
        _doc = ""
        for rule in rule_todo:
            if rule["name"] == name:
                if (
                    int(rule["author_uid"]) != int(msg.user_id) and
                    msg.user_id not in self.data["admin"]
                ):
                    await self.send_message(msg, response("categories", "todo_rule_unauthor"))
                    return
                else:
                    rule_data = rule
                    _doc = rule_data["doc"]
                    if not doc:
                        rule_todo.remove(rule)
                    break
        if doc:
            if rule_data is None:
                rule_data = {
                    "time": time.time(),
                    "name": name,
                    "author_uid": int(msg.user_id),
                    "author_name": msg.sender.nickname,
                    "doc": doc,
                }
                rule_todo.append(rule_data)
            else:
                rule_data["time"] = time.time()
                rule_data["doc"] = doc
        if not rule_data and not doc:
            await self.send_message(msg, response("categories", "todo_rule_del_empty").format(name))
            return

        # 0. 定义路径
        repo_path = os.path.join(SELF_PATH, "fanmade_doc", "rule")
        json_path = os.path.join(repo_path, "ruleTodo.json")
        image_dir = os.path.join(repo_path, "image")
        os.makedirs(image_dir, exist_ok=True)
        image_name = get_rule_image(name) + ".png"
        image_path = os.path.join(image_dir, image_name)

        # 1. 同步远程（保持已有逻辑）
        await run_command('git fetch origin doc', cwd=repo_path)
        ret, _, err = await run_command('git reset --hard origin/doc', cwd=repo_path)
        if ret != 0:
            await self.send_message(msg, "同步远程失败")
            return

        # 2. 处理图片（根据场景决定是添加、替换还是删除）
        if doc and _response and _response.status_code == 200:
            # 更新规则并提供了新图片 → 保存新图片
            with open(image_path, "wb") as f:
                f.write(_response.content)
            _log.info(f"新图片已保存: {image_path}")
            rule_data["image"] = image_name
            await run_command(f'git add "{image_path}"', cwd=repo_path)

        if (doc and not reply) or (not doc):
            if os.path.exists(image_path):
                os.remove(image_path)
                await run_command(f'git add "{image_path}"', cwd=repo_path)
                _log.info(f"图片已移除: {image_path}")
                # 注意：此时删除操作已暂存，但仍需 commit
                if "image" in rule_data:
                    del rule_data["image"]

        # 3. 修改 YAML 文件
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(rule_todo, f, ensure_ascii=True)

        # 4. 发送消息（放在文件修改之后，但不要干扰后续 Git 操作）
        if doc:
            if _doc:
                await self.send_message(msg, response("categories", "todo_rule_update").format(name, _doc))
            else:
                await self.send_message(msg, response("categories", "todo_rule_create").format(name))
        else:
            await self.send_message(msg, response("categories", "todo_rule_del").format(name))

        # 5. 刷新内存规则
        ALL_RULE.clear()
        self.all_rule()

        # 6. Git 添加所有变更（包括新增、修改、删除）
        #    使用 -A 自动处理所有状态
        await run_command('git add -A', cwd=repo_path)

        # 7. 提交
        commit_msg = f"User[{msg.sender.nickname}] " + ('update' if doc else 'delete') + f' RULE[{name}]'
        ret, _, _ = await run_command(f'git commit -m "{commit_msg}"', cwd=repo_path)
        if ret != 0:
            await self.send_message(msg, "无内容变更，跳过推送")
            return

        # 8. 推送（保留你的冲突处理）
        ret, _, _ = await run_command('git push origin doc', cwd=repo_path)
        if ret != 0:
            await run_command('git pull --rebase origin doc', cwd=repo_path)
            ret, _, _ = await run_command('git push origin doc', cwd=repo_path)
            if ret != 0:
                await self.send_message(msg, "推送失败，请手动检查")
                return

        # 9. 更新 hash
        ret, hash_out, _ = await run_command('git rev-parse origin/doc', cwd=repo_path)
        if ret == 0 and hash_out:
            self.data["last_remote_hash_doc"] = hash_out.strip()
            await self.send_message(msg, "规则文件已推送到远端仓库。")

    async def pull(self, msg):
        await self.send_message(msg, "开始拉取远程库")
        result = []
        proj_path: str = config_data["porject_path"]

        # ================= 1. 主仓库更新 (移除 --recurse-submodules，避免重置子模块) =================
        _, pre_main, _ = await run_command("git rev-parse HEAD", proj_path)
        pre_main = pre_main.strip()

        rc, out, err = await run_command("git pull", proj_path)
        result.append("命令: git pull")
        result.append(f"退出码: {rc}")
        if out.strip(): result.append(f"输出:\n{out.strip()}")
        if err.strip(): result.append(f"错误:\n{err.strip()}")

        _, main_log, _ = await run_command(
            f'git log {pre_main}..HEAD --pretty=format:"  - %h %s (%an, %ad)" --date=short',
            proj_path
        )
        if main_log.strip():
            result.append("主仓库新增提交:")
            result.append(main_log.strip())
        else:
            result.append("主仓库无新增提交")

        # ================= 2. 子模块独立更新与变更捕获 =================
        _, status, _ = await run_command("git submodule status", proj_path)
        sub_paths = []
        for line in status.splitlines():
            line = line.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    sub_paths.append(parts[1])

        # 记录更新前 HEAD
        pre_sub_shas = {}
        for sp in sub_paths:
            sub_cwd = os.path.join(proj_path, sp)
            if os.path.isdir(os.path.join(sub_cwd, '.git')) or os.path.isfile(os.path.join(sub_cwd, '.git')):
                _, sha, _ = await run_command("git rev-parse HEAD", sub_cwd)
                pre_sub_shas[sp] = sha.strip() if sha else ""

        # 执行子模块远程更新
        rc, out, err = await run_command("git submodule update --remote --recursive", proj_path)
        result.append("命令: git submodule update --remote --recursive")
        result.append(f"退出码: {rc}")
        if out.strip(): result.append(f"输出:\n{out.strip()}")
        if err.strip(): result.append(f"错误:\n{err.strip()}")

        # 严格对比 SHA，仅输出真实位移
        result.append("子模块新增提交:")
        has_change = False
        for sp in sub_paths:
            sub_cwd = os.path.join(proj_path, sp)
            _, new_sha, _ = await run_command("git rev-parse HEAD", sub_cwd)
            new_sha = new_sha.strip()
            old_sha = pre_sub_shas.get(sp, "")

            # 核心拦截：SHA 一致、未初始化或长度异常直接跳过
            if not old_sha or not new_sha or len(new_sha) != 40 or old_sha == new_sha:
                continue

            _, log, _ = await run_command(
                f'git log {old_sha}..{new_sha} --pretty=format:"    - %h %s (%an, %ad)" --date=short',
                sub_cwd
            )
            if log.strip():
                has_change = True
                result.append(f"{sp}:")
                result.append(log.strip())

        if not has_change:
            result.pop(-1)
            result.append("子模块无变更")

        update_all_rules()
        await self.send_group_forward_msg_text(result, msg)

    async def command(self, command, msg):
        returncode, stdout, stderr = await run_command(
            command, config_data["porject_path"]
        )
        if not stdout:
            await self.api.post_group_msg(msg.group_id, response("command", "running_error") + stderr)
        else:
            if type(command) is list:
                command = " ".join(command)
            stdout = ["run command: " + command, stdout, "exit code: " + str(returncode), "stderr: \n\n" + stderr]
            await self.send_group_forward_msg_text(stdout, msg)

    async def search_rule(self, msg: GroupMessage | PrivateMessage, command=None):
        if command is None:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()
        if len(command) == 1:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, response("prompts", "rule_query"))
            else:
                await self.api.post_private_msg(msg.user_id, response("prompts", "rule_query"))
            return

        args = command[1:]
        forcibly = "/f" in args
        if forcibly:
            args.remove("/f")

        regular = "/re" in args
        if regular:
            args.remove("/re")

        on_random = 0
        for arg in args[:]:
            if not arg.startswith("/rand"):
                continue
            _arg = arg.split('/rand')[1]
            if _arg:
                if not _arg.isdigit():
                    continue
            args.remove(arg)
            on_random = int(_arg) if _arg else 1

        upper = "/u" in args  # upper为True则大小写严格
        if upper:
            args.remove("/u")

        only_name = "/n" in args  # 仅搜索名称
        if only_name:
            args.remove("/n")

        only_R = False
        if "/r" in args:
            args.remove("/r")
            only_R = True
        if "/R" in args:
            args.remove("/R")
            only_R = True

        only_L = False
        if "/l" in args:
            args.remove("/l")
            only_L = True
        if "/L" in args:
            args.remove("/L")
            only_L = True

        only_M = False
        if "/m" in args:
            args.remove("/m")
            only_M = True
        if "/M" in args:
            args.remove("/M")
            only_M = True

        only_T = False
        if "/t" in args:
            args.remove("/t")
            only_T = True
        if "/T" in args:
            args.remove("/T")
            only_T = True

        page = -1
        for arg in args[:]:
            if not arg.startswith("/p"):
                continue
            _arg = arg.split('/p')[1]
            if not _arg.isdigit():
                continue
            args.remove(arg)
            page = int(_arg)

        only_switch = only_R or only_L or only_M or only_T

        patterns = [
            regex.compile(arg, *[i for i in [regex.IGNORECASE] if not upper])
            if regular else arg for arg in args
        ]

        all_rule = self.all_rule()

        result = []
        if (len(args) == 1) and (not forcibly) and (not regular) and (not on_random):
            for rules_index in range(len(all_rule)):
                if only_switch:
                    if not [only_L, only_M, only_R, only_T][rules_index]:
                        continue
                rules = all_rule[rules_index]
                for rule in rules:
                    names = rule["name"]
                    if (
                            (args[0] in names) or
                            (not upper and args[0].lower() in [name.lower() for name in names])
                    ):
                        doc = rule.get("doc").get("content")
                        image = rule.get("doc").get("image")
                        await self.send_message(msg, doc, image_path=image)
                        return

        for rules_index in range(len(all_rule)):
            if only_switch:
                if not [only_L, only_M, only_R, only_T][rules_index]:
                    continue
            rules = all_rule[rules_index]
            for rule in rules:
                rule_doc: dict = rule["doc"]
                content = ''.join(rule["name"]) + ("" if only_name else rule_doc["content"])
                if type(rule_doc) is dict:
                    rule_doc = rule_doc.copy()
                if regular and all(
                    pattern.search(content, timeout=0.2)
                    for pattern in patterns
                ):
                    result.append(rule_doc)
                elif not regular and all(
                        (pattern in content) if upper else
                        (pattern.lower() in content.lower())
                        for pattern in args
                ):
                    result.append(rule_doc)
        result_length = len(result)
        if on_random:
            result = random.choices(result, k=min(on_random, len(result)))
        if page > -1:
            result = result[page * 100: (page + 1) * 100]
        if (page < 0) and ((result_length if on_random == 0 else on_random) > 100):
            result = [result[i:i + 100] for i in range(0, len(result), 100)]
        if on_random == 1 and not forcibly and len(result) > 0:
            await self.send_message(
                msg, result[0].get("content", "空规则描述"),
                image_path=result[0].get("image", None)
            )
            return
        result = [response("rules", "found_rules").format(result_length, args)] + result

        if msg.message_type == "group":
            await self.send_group_forward_msg_text(result, msg)
        elif msg.message_type == "private":
            await self.send_private_forward_msg_text(result, msg)

    async def rule_list(self, msg):
        # news = [{"text": response("categories", "left_rules")},
        #         {"text": response("categories", "middle_rules")},
        #         {"text": response("categories", "right_rules")}]

        self.all_rule()
        all_rule: list[list[str | dict]] = []
        for index in range(3):
            all_rule.append([[
                response("categories", "left_rules_title"),
                response("categories", "middle_rules_title"),
                response("categories", "right_rules_title"),
            ][index]])
            for rule in ALL_RULE[index]:
                rule_doc: dict = rule["doc"]
                all_rule[-1].append(rule_doc)

        all_rule += [response("categories", "todo_rules_title")]

        result = []

        for rule in ALL_RULE[3]:
            result.append(rule["doc"])
        if len(result) > 100:
            result = [result[i:i + 100] for i in range(0, len(result), 100)]
        all_rule += result

        await self.send_group_forward_msg_text(
            all_rule, msg,
            # source=response("categories", "rules_list")
        )

    def all_rule(self) -> list[list[dict[str, list[str] | dict | str]]]:
        """
        :return: [{"name": ["a", "b", ...], "doc": "..." | {msg}}, ...], ...
        """
        global ALL_RULE
        if ALL_RULE:
            return ALL_RULE
        with open(f"{SELF_PATH}/rule.json", "r", encoding="utf-8") as f:
            rule_json: dict = json.load(f)

        rules_list: list[list] = []
        for key in rule_json:
            rules_list.append([])
            for rule_dict in rule_json[key]:
                author = rule_dict["author"]
                if rule_dict["image"]:
                    image = os.path.join(config_data["image_path"], rule_dict["image"])
                else:
                    image = ""
                on_user = (
                    (author["id"] is not None) and
                    (author["id"]) and
                    (int(author["id"]) > 0)
                )
                rule_data = {
                    "name": (
                        [rule_dict["id"]] +
                        list(rule_dict["name"].values()) +
                        list(rule_dict.get("aliases", []))
                    ),
                    "doc": {
                        "content": "",
                        "uid": author["id"] if on_user else None,
                        "name": author["name"] if on_user else None,
                        "image": image if os.path.exists(image) else "",
                    },
                    "author": (
                        author["id"] if on_user else None,
                        author["name"] if on_user else None
                    )
                }
                content = f'[{rule_dict["id"]}]'
                content += f'{rule_dict["name"].get("zh_CN", rule_dict["name"].get("default", ""))}'
                content += f': {rule_dict["doc"].get("zh_CN", rule_dict["doc"].get("default", "空描述"))}'
                rule_data["doc"]["content"] = content
                rules_list[-1].append(rule_data)
        rule_todo_list = json.load(open(f"{SELF_PATH}/fanmade_doc/rule/ruleTodo.json", "r", encoding="utf-8"))
        todo_rule_fmt = response("categories", "todo_rule_fmt")
        rules_list.append([])
        for data in rule_todo_list:
            image = ""
            if "image" in data:
                image = f"{SELF_PATH}\\fanmade_doc\\rule\\image\\" + data.get('image')
            on_user = (data["author_uid"] is not None) and (int(data["author_uid"]) > 0)
            print(data, on_user)
            rules_list[-1].append(
                {
                    "name": [data["name"]],
                    "author": (
                        data["author_name"] if on_user else None,
                        data["author_uid"] if on_user else None
                    ),
                    "doc": {
                        "content": todo_rule_fmt.format(
                            data["name"], data["doc"], data["author_name"], data["author_uid"],
                            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data["time"]))
                        ),
                        "name": data["author_name"] if on_user else None,
                        "uid": data["author_uid"] if on_user else None,
                        "image": image if os.path.exists(image) else ""
                    }
                }
            )
        # print(rules_list)
        ALL_RULE = rules_list
        return ALL_RULE

    async def send_private_forward_msg_text(self, text, msg: PrivateMessage, news=None, source=None, summary=None):
        if type(text) is str:
            text = [text]
        message = pck(text)
        message = message[0]["data"]["content"]
        if not message:
            return
        params = {"user_id": msg.user_id, "message": message}
        if news is not None:
            params["news"] = news
        if source is not None:
            params["source"] = source
        if summary is not None:
            params["summary"] = summary
        return check_and_log(await self.api._http.post("/send_private_forward_msg", json=params))

    async def send_group_forward_msg_text(self, text, msg: GroupMessage, news=None, source=None, summary=None):
        if type(text) is str:
            text = [text]
        message = pck(text)
        message = message[0]["data"]["content"]
        if not message:
            return
        params = {"group_id": msg.group_id, "message": message}
        if news is not None:
            params["news"] = news
        if source is not None:
            params["source"] = source
        if summary is not None:
            params["summary"] = summary

        result = await self.api._http.post("/send_group_forward_msg", json=params)
        if result.get("status", "") != "ok":
            await self.api.post_group_msg(msg.group_id, str(result))
        return check_and_log(result)

    async def send_group_forward_msg_image(self, path, msg: GroupMessage):
        if not path.startswith("base64://"):
            path = f"http://{HOST_IP}\\" + path.replace("\\", "/").lstrip("/")
        content = [{"type": "image", "data": {
            "file": path, "summary": response("images", "answer")
        }}]
        message = [{"type": "node", "data": {
            "user_id": response("users", "default_bot", "id"),
            "nickname": response("users", "default_bot", "nickname"),
            "content": content
        }}]
        params = {"group_id": msg.group_id, "message": message, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))

    async def send_private_forward_msg_image(self, path, msg: PrivateMessage):
        if not path.startswith("base64://"):
            path = f"http://{HOST_IP}\\" + path.replace("\\", "/").lstrip("/")
        content = [{"type": "image", "data": {
            "file": path, "summary": response("images", "answer")
        }}]
        message = [{"type": "node", "data": {
            "user_id": response("users", "default_bot", "id"),
            "nickname": response("users", "default_bot", "nickname"),
            "content": content
        }}]
        params = {"user_id": msg.user_id, "message": message, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_private_forward_msg", json=params))

    async def state(self, msg):
        def _get_process_info_block(key, proc_info, _interval=None):
            """
            获取单个进程的信息块（保持原有换行格式）
            返回字符串：开头的换行 + 三行基本信息 + （如有 pid）第四行 CPU/内存
            """
            if _interval is None:
                _interval = config_data["interval"]
            _block = "\n"
            _block += response("status", "process_info", "1").format(
                key, proc_info.pid, proc_info.start_time
            )
            _block += response("status", "process_info", "2").format(proc_info.data)
            _block += response("status", "process_info", "3").format(proc_info.nickname)

            if proc_info.pid:
                try:
                    process = psutil.Process(proc_info.pid)
                    # 内存信息
                    rss = process.memory_info().rss
                    memory_info = "NAN"
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if rss < 1024.0:
                            memory_info = f"{rss:.1f}{unit}"
                            break
                        rss /= 1024.0
                    # CPU 使用率（阻塞 0.2 秒，但在多线程中并发执行）
                    cpu_percent = process.cpu_percent(interval=_interval)
                    cpu_usage = round(cpu_percent / psutil.cpu_count(), 2)
                    # 第四行前添加换行（与原逻辑一致）
                    _block += "\n" + response("status", "process_info", "4").format(cpu_usage, memory_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                    # 进程已退出或无权限，跳过第四行（与原行为一致，原代码无 try 会崩溃，这里安全处理）
                    pass
            _block += self._query_thread(key)
            return _block

        async def _main():
            # ---------- 主逻辑 ----------
            result = response("status", "total_processes").format(len(request_map.keys()))
            command: list[str] = ''.join(
                [i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip().split()
            if len(command) > 1 and command[1].replace(".", "").isdigit():
                interval = float(command[1])
            else:
                interval = config_data["interval"]

            keys = list(request_map.keys())
            # 线程池最大工作线程数：系统状态任务 + 进程任务，限制上限避免过多线程
            max_workers = len(keys) + 1

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交系统状态任务（索引0）
                future_sys = executor.submit(get_system_stats, interval)

                # 提交所有进程信息任务，按顺序保存 future
                process_futures = []
                for key in keys:
                    process_futures.append(executor.submit(_get_process_info_block, key, request_map[key], interval))

                # 获取系统状态结果（会阻塞直到完成）
                sys_stats = future_sys.result()

                # 按原顺序获取所有进程信息结果
                process_blocks = [fut.result() for fut in process_futures]

            # 拼接最终结果：先加系统状态（原代码有换行）
            result += "\n" + sys_stats
            for block in process_blocks:
                result += block

            if len(request_map.keys()) > 3:
                if hasattr(msg, "group_id"):
                    await self.send_group_forward_msg_text(result, msg)
                else:
                    await self.send_private_forward_msg_text(result, msg)
            else:
                if hasattr(msg, "group_id"):
                    await self.api.post_group_msg(msg.group_id, result)
                else:
                    await self.api.post_private_msg(msg.user_id, result)

        def _run_main_in_thread():
            """在新线程中运行 _main"""
            asyncio.run(_main())  # 在新线程中创建新的事件循环

        # 在 state 函数里：
        t = threading.Thread(target=_run_main_in_thread, daemon=True)
        t.start()  # 非阻塞，立即返回，不卡主线程

    async def kill_thread(self, command, msg):
        kill_list = []
        if "all" in command:
            command.extend([str(i) for i in request_map.keys()])
        for command_arg in command[1:]:
            if command_arg.isdigit():
                kill_list.append(int(command_arg))
        if not kill_list:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(
                    msg.group_id,
                    response("errors", "invalid_input")
                )
            else:
                await self.api.post_private_msg(
                    msg.user_id,
                    response("errors", "invalid_input")
                )
            return
        for query_id in kill_list:
            if query_id not in request_map:
                kill_list.remove(query_id)
                continue
            if msg.sender.user_id not in self.data["admin"]:
                if request_map[query_id].nickname != msg.sender.nickname:
                    continue
            request = request_map[query_id]
            del request_map[query_id]
            request.close_connection()
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(
                msg.group_id,
                response("task", "terminated").format(f"[{', '.join([str(i) for i in kill_list])}]")
            )
        else:
            await self.api.post_private_msg(
                msg.user_id,
                response("task", "terminated").format(f"[{', '.join([str(i) for i in kill_list])}]")
            )

    async def query_thread(self, msg: PrivateMessage | GroupMessage, command=None):
        if command is None:
            raw_message = ''.join([i["data"]["text"] for i in msg.message if i["type"] == "text"]).strip()
            command: list[str] = raw_message.split()
        forcibly = "/f" in command
        if forcibly:
            command.remove("/f")
        if len(command) == 1:
            await self.send_message(msg, response("task", "unid"))
            return
        if not command[1].isdigit():
            await self.search_rule(msg)
            return
        if len(command) > 2 and command[2].isdigit():
            str_length = int(float(command[2]))
            if str_length < 1:
                str_length = 2000
        else:
            str_length = 2000
        if len(command) > 3 and command[3].isdigit():
            msg_length = int(float(command[3]))
            if msg_length < 1:
                msg_length = 8000 // str_length
            if msg_length > 100:
                msg_length = 100
        else:
            msg_length = 12000 // str_length
        query_id = int(command[1])
        if query_id not in request_map:
            await self.send_message(msg, response("task", "not_found"))
            return
        result = request_map[query_id].get_output()
        log_file_name = config_data["log_path"] + "\\" + str(query_id) + ".log"
        if os.path.exists(log_file_name):
            with open(log_file_name, "rb") as log_file:
                log_file.seek(0, os.SEEK_END)
                log_file.seek(max(0, log_file.tell() - 16384))
                log_text = log_file.read().decode("utf-8", errors="ignore")
        else:
            log_text = ""
        if result == "":
            await self.send_message(msg, "终端输出为空")
            return
        if not forcibly:
            reply_text = ""
            if "生成用时" in log_text:
                await self.send_message(msg, response("progress", "saving_image"))
                return
            if "尝试第" in log_text and "次minesweepervariants" in log_text:
                try_index = int(log_text.rsplit("尝试第", 1)[1].rsplit("次minesweepervariants")[0])
                if try_index > 1:
                    reply_text += response("progress", "retrying").format(try_index)
            for line in result.split("\n")[::-1]:
                line: str
                if line.strip() == "":
                    continue
                if "进度" in line:
                    result = ((reply_text + "\n") if reply_text else "") + line
                    await self.send_message(msg, result)
                    return
            if reply_text:
                await self.send_message(msg, reply_text)
                return

        reply_text = log_text + "\n" + "\n".join([line for line in result.split("\n")][::-1][:10][::-1])
        result = [reply_text[i:i + str_length] for i in range(0, len(reply_text), str_length)][::-1][:msg_length][::-1]
        if type(msg) is GroupMessage:
            await self.send_group_forward_msg_text(result, msg=msg)
        elif type(msg) is PrivateMessage:
            await self.send_private_forward_msg_text(result, msg=msg)
        return

    def _query_thread(self, query_id):
        result = request_map[query_id].get_output()
        log_file_name = config_data["log_path"] + "\\" + str(query_id) + ".log"
        if os.path.exists(log_file_name):
            with open(log_file_name, "rb") as log_file:
                log_file.seek(0, os.SEEK_END)
                log_file.seek(max(0, log_file.tell() - 16384))
                log_text = log_file.read().decode("utf-8", errors="ignore")
        else:
            log_text = ""

        reply_text = ""
        if "生成用时" in log_text:
            return response("progress", "saving_image")
        if "尝试第" in log_text and "次minesweepervariants" in log_text:
            try_index = int(log_text.rsplit("尝试第", 1)[1].rsplit("次minesweepervariants")[0])
            if try_index > 1:
                reply_text += f"\n重试第{try_index}次"
        for line in result.split("\n")[::-1]:
            line: str
            if line.strip() == "":
                continue
            if "进度" in line:
                return reply_text + "\n用时:" + line.split("用时:")[1]
        return reply_text

    def thread_target(self, msg, command, request):
        # 创建新事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.spawn(msg, command, request))
        loop.close()

    async def spawn(self, msg, command, request: Request):
        if len(command) < 2:
            await self.send_message(
                msg,
                response("prompts", "generate_usage"),
                reply=msg.message_id
            )
            del request_map[request.request_id]
            return
        if not command[1].isdigit():
            await self.send_message(
                msg,
                response("prompts", "size_position"),
                reply=msg.message_id
            )
            del request_map[request.request_id]
            return
        if msg.message[0]["type"] == "reply":
            reply_msg = await self.api.get_msg(msg.message[0]["data"]["id"])
            reply_message = reply_msg["data"]["message"]
            for reply_msg_part in reply_message:
                if reply_msg_part["type"] != "image":
                    continue
                replace_image_url = reply_msg_part["data"]["url"]
                for command_index in range(len(command)):
                    command_arg = command[command_index]
                    if "$img" in command_arg:
                        command[command_index] = command_arg.replace("$img", replace_image_url)
                break
        size = [command[1]]
        if len(command) > 2:
            if command[2].isdigit():
                size.append(command[2])
                command = command[3:]
            else:
                command = command[2:]
        else:
            command = []
        if not command:
            await self.send_message(
                msg,
                response("prompts", "generate_usage"),
                reply=msg.message_id
            )
            del request_map[request.request_id]
            return
        rules = command
        # for rule in rules[:]:
        #     if rules.count(rule) > 1:
        #         rules.remove(rule)

        data = rules[:]
        # if "-d" in data:
        #     data = data[:data.index("-d")] + data[data.index("-d") + 2:]
        # if "-t" in data:
        #     data = data[:data.index("-t")] + data[data.index("-t") + 2:]
        # if "-a" in data:
        #     data = data[:data.index("-a")] + data[data.index("-a") + 2:]
        # if "-r" in data:
        #     data.remove("-r")
        request.data += "尺寸:"
        request.data += "x".join(size)
        request.data += " 规则:"
        request.data += " ".join(data)

        for rule_index in range(len(rules)):
            rule: str = rules[rule_index]
            if "$" in rule:
                rules[rule_index] = rules[rule_index].replace("$", "$0")
            if "^" in rule:
                rules[rule_index] = rules[rule_index].replace("^", "$1")
            if "|" in rule:
                rules[rule_index] = rules[rule_index].replace("|", "$2")
            if "&" in rule:
                rules[rule_index] = rules[rule_index].replace("&", "$3")
            if ">" in rule:
                rules[rule_index] = rules[rule_index].replace(">", "$4")
            if "<" in rule:
                rules[rule_index] = rules[rule_index].replace("<", "$5")
            if "%" in rule:
                rules[rule_index] = rules[rule_index].replace("%", "$6")

        args = "-a 5 -s "
        args += " ".join(size)
        args += " -c "
        args += " ".join(rules)
        args += " --file-name " + str(request.request_id)
        state = 1
        result = ""

        demo_img = config_data["out_path"] + "\\" + str(request.request_id) + "demo.png"
        answer_img = config_data["out_path"] + "\\" + str(request.request_id) + "answer.png"
        log_path = config_data["log_path"] + "\\" + str(request.request_id) + ".log"

        for _ in range(1):
            request.run_task(args)
            while "PID" not in ''.join(request.output_buffer):
                time.sleep(0.1)
            request.pid = int(
                [
                    i for i in request.output_buffer if "PID" in i
                ][0].split("PID:[")[1].split("]")[0]
            )
            request.wait_completion()
            if request.request_id not in request_map:
                return
            result = request.get_output()
            request.output_buffer.clear()
            request.close_connection()
            if result == "":
                if request.request_id in request_map:
                    del request_map[request.request_id]
                return
            if "未找到规则" in result:
                state = 2
                break
            if os.path.exists(demo_img) and os.path.exists(answer_img):
                state = 0
                break
            _request = request.clone()
            del request_map[request.request_id]
            del request
            request = _request
            request_map[request.request_id] = _request

        if os.path.exists(log_path):
            with open(log_path, "rb") as f:
                f.seek(max(0, os.path.getsize(log_path) - 4096))
                raw = f.read()
                log_text = raw.decode("utf-8", errors="replace")  # 非法字节变 �
        else:
            log_text = "[EMPTY]"

        if state == 0:
            if isinstance(msg, GroupMessage):
                await self.api.post_group_file(
                    msg.group_id,
                    image=demo_img
                )
            elif isinstance(msg, PrivateMessage):
                await self.api.post_private_file(
                    msg.user_id,
                    image=demo_img
                )
            with open(answer_img, "rb") as f:
                base64_content = "base64://" + base64.b64encode(f.read()).decode('utf-8')

            if isinstance(msg, GroupMessage):
                await self.send_group_forward_msg_image(
                    path=base64_content,
                    msg=msg
                )
            elif isinstance(msg, PrivateMessage):
                await self.send_private_forward_msg_image(
                    path=base64_content,
                    msg=msg
                )
            pathlib.Path.unlink((config_data["out_path"] + "\\" +
                                 str(request.request_id) + "answer.png"))
            pathlib.Path.unlink((config_data["out_path"] + "\\" +
                                 str(request.request_id) + "demo.png"))
            try:
                pathlib.Path.unlink((config_data["out_path"] + "\\" +
                                     str(request.request_id) + ".txt"))
            except:
                ...
            if "线索图: " in log_text:
                clue_img = log_text.rsplit("线索图: ")[-1].split("\n")[0]
            else:
                clue_img = ""
            clue_img = f"线索图: {clue_img}\n" if clue_img else ""

            await self.send_message(
                msg, clue_img + response("task", "completed"),
                reply=msg.message_id
            )
        if state == 1:
            if request.request_id not in request_map:
                return
            msg_length = 9
            str_length = 1000
            result = log_text + "\n\n" + '\n'.join([i for i in result.split("\n")][-50:])
            err_result = [result[i:i + str_length] for i in range(0, len(result), str_length)][::-1][:msg_length][::-1]
            if isinstance(msg, GroupMessage):
                response_text = response("task", "failed").format(request.request_id)
                if "[STDERR EMPTY]" not in result:
                    traceback = (result.split("[STDERR]:")[-1].rsplit(":[STDERR]", 1)[0]).split("\n")
                    response_text += "\n" + [i for i in traceback if i][::-1][0]
                await self.api.post_group_msg(
                    msg.group_id,
                    response_text,
                    reply=msg.message_id
                )
                await self.send_group_forward_msg_text(
                    text=err_result,
                    source=response("categories", "terminal_output"),
                    msg=msg
                )
            elif isinstance(msg, PrivateMessage):
                await self.api.post_private_msg(
                    msg.user_id,
                    response("task", "failed").format(request.request_id),
                    reply=msg.message_id
                )
                await self.send_private_forward_msg_text(
                    text=err_result,
                    source=response("categories", "terminal_output"),
                    msg=msg
                )
        if state == 2:
            rule_name = result.split("未找到规则[")[-1].split("]", 1)[0]
            await self.send_message(
                msg,
                response("errors", "unknown_rule").format(rule_name),
                reply=msg.message_id
            )

        del request_map[request.request_id]
