import asyncio
import pathlib
import random
import re
import subprocess
import time
from pathlib import Path
import socket
import threading
import datetime

import regex
import yaml
import base64
from ncatbot.core.api import check_and_log

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils import logger


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
    output = ""
    for _ in range(5):
        request = Request()
        request.run_task("list --shell")
        request.wait_completion(timeout=0)
        lime_time = time.time() + 2.5
        while time.time() < lime_time:
            time.sleep(0.05)
            if "hex_end" in request.get_output():
                break
        output = request.get_output()
        if "hex_end" in output:
            break
    if "hex_end" not in output:
        return False
    output = output.split("hex_start:")[1].split(":hex_end")[0]
    with open(f"{SELF_PATH}/rule.tmp", 'wb') as f:
        f.write(bytes.fromhex(output))
    _log.info("发起更新规则列表")
    return True


SELF_PATH = Path(__file__).parent.__str__()

_log = logger.get_log()
bot = CompatibleEnrollment
config_data: dict = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))

request_map = {}
HOST_IP = get_host_ip()


class Request:
    def __init__(self, max_length=0, _request_id=0):
        self.output_buffer = []
        self.max_length = max_length
        self.request_id = _request_id
        self._thread = None
        self._socket = None
        self._should_stop = threading.Event()
        self._lock = threading.Lock()  # 用于保护output_buffer的线程安全
        self._completed = threading.Event()

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

    def run_task(self, args: str) -> None:
        """
        启动新线程运行任务（异步执行）

        参数:
            args: 传递给bat文件的参数字符串
        """
        self._thread = threading.Thread(target=self._run_task, args=(args,))
        self._thread.daemon = True
        self._thread.start()

    def _run_task(self, args: str) -> None:
        """实际执行任务的线程函数"""
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 31408))
            self._socket = client  # 保存socket引用用于关闭

            # 接收初始握手信号
            init_data = client.recv(4)
            if init_data != b'14mv':
                raise ConnectionError("无效的服务器握手信号")

            # 发送参数
            client.sendall(args.encode('utf-8'))

            # 持续接收数据
            while not self._should_stop.is_set():
                data = b''
                try:
                    # 设置超时以定期检查停止标志
                    client.settimeout(1)
                    data = client.recv(4096)
                    if not data:  # 正常断开
                        break

                    decoded = data.decode('utf-8', errors='replace')
                    with self._lock:
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
            return ''.join(self.output_buffer)

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
        try:
            command: list[str] = msg.raw_message.split()
            match command[0]:
                case "#生成":
                    self.data["id"] += 1
                    request_map[self.data["id"]] = Request(max_length=50, _request_id=self.data["id"])
                    request_map[self.data["id"]].nickname = msg.sender.nickname
                    threading.Thread(target=self.thread_target,
                                     args=(msg, command[:], request_map[self.data["id"]])).start()
                    time.sleep(1)
                    if self.data["id"] in request_map:
                        await self.api.post_private_msg(
                            msg.user_id, response("task", "created").format(self.data["id"])
                        )
                case "#所有规则" | "#规则列表" | "#list":
                    await self.rule_list(msg)
                case "#查询规则":
                    await self.search_rule(msg)
                case "#查询" | "#cx":
                    await self.query_thread(command, msg)
                case "#帮助" | "#help":
                    HELP_TEXT = yaml.full_load(open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8"))
                    await self.send_private_forward_msg_text(HELP_TEXT, msg)
                case "#状态" | "#state":
                    await self.state(msg)
                case "#终止" | "#kill":
                    await self.kill_thread(command, msg)
                case "#pull":
                    await self.pull(msg)
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
        print(msg.group_id, ":", msg.raw_message[:20].replace("\n", ""), end="\r")
        try:
            command: list[str] = msg.raw_message.split()
            if not msg.raw_message.startswith("#"):
                return
            # if not msg.raw_message.startswith("#test"):
            #     return
            match command[0]:
                case "#生成" | "#sc" | "#summon":
                    self.data["id"] += 1
                    self.data.save()
                    request_map[self.data["id"]] = Request(max_length=50, _request_id=self.data["id"])
                    request_map[self.data["id"]].nickname = msg.sender.nickname
                    threading.Thread(target=self.thread_target,
                                     args=(msg, command[:], request_map[self.data["id"]])).start()
                    time.sleep(0.5)
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
                case "#查询规则" | "#查询" | "#cx":
                    await self.query_thread(command, msg)
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
                case "#状态" | "#state" | "##":
                    await self.state(msg)
                case "#终止" | "#kill":
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
                case "#注册规则":
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

    async def send_message(self, msg, message: str):
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, message)
        else:
            await self.api.post_private_msg(msg.user_id, message)
        return

    async def register_rules(self, msg, name, doc):
        rule_todo: list[dict] = yaml.full_load(open(f"{SELF_PATH}/ruleTodo.yaml", "r", encoding="utf-8"))
        rule_data = None
        for rule in rule_todo:
            if rule["name"] == name:
                if (
                    int(rule["author_uid"]) != int(msg.user_id) and
                    msg.user_id not in self.data["admin"]
                ):
                    await self.send_message(msg, response("categories", "todo_rule_unauthor"))
                    return
                else:
                    if doc:
                        rule_data = rule
                        break
                    rule_data = True
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
        with open(f"{SELF_PATH}/ruleTodo.yaml", "w", encoding="utf-8") as f:
            yaml.dump(rule_todo, f, allow_unicode=True)
        if doc:
            await self.send_message(msg, response("categories", "todo_rule_update").format(name))
        else:
            await self.send_message(msg, response("categories", "todo_rule_del").format(name))

    # @bot.group_event()
    # async def admin(self, messages: GroupMessage):
    #     member_list = await self.api.get_group_member_list(messages.group_id)
    #     # print(member_list)
    #     return
    #     if "admin" not in self.data:
    #         self.data["admin"] = []
    #     admin_data = None
    #     admin_flag = False
    #     for msg in messages.message:
    #         if msg["type"] == "text":
    #             if msg["data"]["text"].startswith("#admin"):
    #                 tmp_data = msg["data"]["text"].split("#admin")[1]
    #                 if not tmp_data.split()[0]:
    #                     continue
    #                 tmp_data: str
    #                 if tmp_data.isdigit():
    #                     # 是数字就当成qq号
    #                     admin_data = tmp_data.strip()
    #                 else:
    #                     # 不是就看有没有人叫这个
    #                     member_list = await self.api.get_group_member_list(messages.group_id)
    #                     print(member_list)
    #                 admin_flag = True
    #             return
    #         if msg["type"] == "at":
    #             admin_data = str(msg["data"]["qq"])
    #         if msg["type"] == "reply":
    #             await self.api.get_msg()
    #     if admin_data is None:
    #         return
    #     if messages.user_id not in self.data["admin"]:
    #         await self.api.post_group_msg(messages.group_id, response("command", "user_not_admin"))
    #         return

    async def pull(self, msg):
        result = []
        returncode, stdout, stderr = await run_command(
            "git pull --recurse-submodules",
            config_data["porject_path"]
        )
        result.extend(["run command: git pull --recurse-submodules", stdout, "exit code: " + str(returncode),
                       "stderr: \n\n" + stderr])
        returncode, stdout, stderr = await run_command(
            "git submodule update --remote",
            config_data["porject_path"]
        )
        result.extend(
            ["git submodule update --remote", stdout, "exit code: " + str(returncode), "stderr: \n\n" + stderr])
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

    async def search_rule(self, msg: GroupMessage | PrivateMessage):
        command = msg.message[0]["data"]["text"].split(" ")
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
        patterns = [regex.compile(arg, regex.IGNORECASE) for arg in args]
        all_rule = [rule for rules in self.all_rule() for rule in rules]
        result = []
        for rule in all_rule:
            if type(rule) is dict:
                rule = rule.get("content", "")
            if all(pattern.search(rule, timeout=0.2) for pattern in patterns):
                if not forcibly:
                    await self.send_message(msg, rule)
                    return
                result.append(rule)
        result_length = len(result)
        if result_length > 100:
            result = [result[i:i+100] for i in range(0, len(result), 100)]
        result = [response("rules", "found_rules").format(result_length, args)] + result
        await self.send_group_forward_msg_text(result, msg)

    async def rule_list(self, msg):
        rules_list = self.all_rule()
        # news = [{"text": response("categories", "left_rules")},
        #         {"text": response("categories", "middle_rules")},
        #         {"text": response("categories", "right_rules")}]
        await self.send_group_forward_msg_text(
            rules_list, msg,
            # source=response("categories", "rules_list")
        )

    def all_rule(self):
        with open(f"{SELF_PATH}/rule.tmp", "rb") as f:
            output = f.read()
        output = output.decode("utf-8").replace("\r", "")
        split_symbol, output = output[:50], output[50:]
        output = output.split(split_symbol * 2)[:-1]
        rules_list: list[list] = []
        for i in range(len(output)):
            rules: list[str] = output[i].split(split_symbol)
            rules = [[
                response("categories", "left_rules_title"),
                response("categories", "middle_rules_title"),
                response("categories", "right_rules_title"),
            ][i]] + rules
            rules_list.append(rules)
        rule_todo_list = yaml.full_load(open(f"{SELF_PATH}/ruleTodo.yaml", "r", encoding="utf-8"))
        todo_rule_fmt = response("categories", "todo_rule_fmt")
        rules_list.append([
            response("categories", "todo_rules_title")
        ] + [
            {
                "content": todo_rule_fmt.format(
                    data["name"], data["doc"], data["author_name"], data["author_uid"],
                    time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data["time"]))
                ), "name": data["author_name"], "uid": data["author_uid"]
            }
            for data in rule_todo_list
        ])
        return rules_list

    async def send_private_forward_msg_text(self, text, msg: PrivateMessage, news=None, source=None, summary=None):
        def pck(content, user_id=None, nickname=None) -> list:
            if user_id is None:
                user_id = response("users", "default_bot", "id")
            if nickname is None:
                nickname = response("users", "default_bot", "nickname")
            if type(content) is str:
                content = [{"type": "text", "data": {"text": content}}]
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
                uid = content.get("uid", response("users", "default_bot", "id"))
                name = content.get("name", response("users", "default_bot", "nickname"))
                content = content["content"]
                return pck(content, user_id=uid, nickname=name)
            else:
                return []

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
        NICK_NAME = response("users", "default_bot", "nickname")
        USER_ID = response("users", "default_bot", "id")

        def pck(content, user_id=USER_ID, nickname=NICK_NAME) -> list:
            if type(content) is str:
                content = [{"type": "text", "data": {"text": content}}]
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
                content = content["content"]
                __result = pck(content, user_id=uid, nickname=name)
                return __result
            else:
                return []

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
        result = response("status", "total_processes").format(len(request_map.keys()))
        for key in request_map.keys():
            result += response("status", "process_info", "1").format(key, request_map[key].start_time)
            result += response("status", "process_info", "2").format(request_map[key].data)
            result += response("status", "process_info", "3").format(request_map[key].nickname)
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

    async def kill_thread(self, command, msg):
        if not command[1].isdigit():
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
        query_id = int(command[1])
        if query_id not in request_map:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(
                    msg.group_id,
                    response("task", "not_found")
                )
            else:
                await self.api.post_private_msg(
                    msg.user_id,
                    response("task", "not_found")
                )
            return
        request = request_map[query_id]
        request.close_connection()
        del request_map[query_id]
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(
                msg.group_id,
                response("task", "terminated")
            )
        else:
            await self.api.post_private_msg(
                msg.user_id,
                response("task", "terminated")
            )

    async def query_thread(self, command, msg):
        forcibly = "/f" in command
        if forcibly:
            command.remove("/f")
        if len(command) == 1:
            await self.api.post_group_msg(
                msg.group_id,
                response("task", "unid")
            )
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
                msg_length = 12000 // str_length
            if msg_length > 100:
                msg_length = 100
        else:
            msg_length = 12000 // str_length
        query_id = int(command[1])
        if query_id not in request_map:
            await self.api.post_group_msg(
                msg.group_id,
                response("task", "not_found")
            )
            return
        result = request_map[query_id].get_output()
        if not forcibly:
            for line in result.split("\n")[::-1]:
                line: str
                if line.strip() == "":
                    continue
                if "生成用时" in line:
                    await self.api.post_group_msg(msg.group_id, response("progress", "saving_image"))
                    return
                if "进度" in line:
                    await self.api.post_group_msg(msg.group_id, line)
                    return
                if "生成失败" in line:
                    await self.api.post_group_msg(msg.group_id, response("progress", "retrying"))
                    return
        result = result
        result = [result[i:i+str_length] for i in range(0, len(result), str_length)][::-1][:msg_length][::-1]
        # print(result)
        await self.send_group_forward_msg_text(result, msg=msg)
        return

    def thread_target(self, msg, command, request):
        # 创建新事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.spawn(msg, command, request))
        loop.close()

    async def spawn(self, msg, command, request):
        try:
            map_data = yaml.full_load(open(f"{SELF_PATH}/map.yaml", "r", encoding="utf-8"))
        except:
            map_data = {}
        if len(command) < 2:
            await self.api.post_group_msg(
                msg.group_id,
                response("prompts", "generate_usage"),
                reply=msg.message_id
            )
            del request_map[request.request_id]
            return
        if not command[1].isdigit():
            await self.api.post_group_msg(
                msg.group_id,
                response("prompts", "size_position"),
                reply=msg.message_id
            )
            del request_map[request.request_id]
            return
        size = [command[1]]
        if command[2].isdigit():
            size.append(command[2])
            command = command[3:]
        else:
            command = command[2:]
        rules = []
        for rule in command:
            if rule.startswith("-"):
                rules.extend(command[command.index(rule):])
                break
            if rule in map_data.keys():
                if type(map_data[rule]) is str:
                    rules.append(map_data[rule])
                if type(map_data[rule]) is list:
                    rules.extend(map_data[rule])
            else:
                rules.append(rule)
        for rule in rules[:]:
            if rules.count(rule) > 1:
                rules.remove(rule)

        data = rules[:]
        if "-d" in data:
            data = data[:data.index("-d")] + data[data.index("-d") + 2:]
        if "-t" in data:
            data = data[:data.index("-t")] + data[data.index("-t") + 2:]
        if "-a" in data:
            data = data[:data.index("-a")] + data[data.index("-a") + 2:]
        if "-r" in data:
            data.remove("-r")
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

        args = "-a 5 -s "
        args += " ".join(size)
        args += " -c "
        args += " ".join(rules)
        args += " --file-name " + str(request.request_id)
        state = 1
        result = ""
        for _ in range(1):
            request.run_task(args)
            request.wait_completion()
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
            if "Image saved to:" in result:
                state = 0
                break
            _request = request.clone()
            del request_map[request.request_id]
            del request
            request = _request
            request_map[request.request_id] = _request

        if state == 0:
            await self.api.post_group_file(
                msg.group_id,
                image=(config_data["out_path"] + "\\" +
                       str(request.request_id) + "demo.png")
            )
            with open(config_data["out_path"] + "\\" + str(request.request_id) + "answer.png", "rb") as f:
                base64_content = "base64://" + base64.b64encode(f.read()).decode('utf-8')

            await self.send_group_forward_msg_image(
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
            await self.api.post_group_msg(
                reply=msg.message_id,
                text=response("task", "completed"),
                group_id=msg.group_id
            )
        if state == 1:
            if request.request_id not in request_map:
                return
            await self.api.post_group_msg(
                msg.group_id,
                response("task", "failed").format(request.request_id),
                reply=msg.message_id
            )
            await self.send_group_forward_msg_text(
                text=result,
                source=response("categories", "terminal_output"),
                msg=msg
            )
        if state == 2:
            rule_name = result.split("未找到规则[")[-1].split("]", 1)[0]
            await self.api.post_group_msg(
                msg.group_id,
                response("errors", "unknown_rule").format(rule_name),
                reply=msg.message_id
            )

        del request_map[request.request_id]


# if __name__ == '__main__':
#     output = ""
#     for _ in range(5):
#         request = Request()
#         request.run_task("list --shell")
#         request.wait_completion(timeout=0)
#         lime_time = time.time() + 2.5
#         while time.time() < lime_time:
#             time.sleep(0.05)
#             if "hex_end" in request.get_output():
#                 break
#         output = request.get_output()
#         if "hex_end" in output:
#             break
#     output = output.split("hex_start:")[1].split(":hex_end")[0]
#     output = bytes.fromhex(output)
#     output = output.decode("utf-8").replace("\r", "")
#     split_symbol, output = output[:50], output[50:]
#     output = output.split(split_symbol * 2)[:-1]
#     rules_list: list[list] = []
#     for i in range(len(output)):
#         print(rules_list)
#         rules: list[str] = output[i].split(split_symbol)
#         print(rules)
#         rules = [[
#                      response("categories", "left_rules_title"),
#                      response("categories", "middle_rules_title"),
#                      response("categories", "right_rules_title")
#                  ][i]] + rules
#         rules_list.append(rules)
#     print(rules_list)
