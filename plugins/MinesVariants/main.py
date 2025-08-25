import asyncio
import time
from pathlib import Path
import socket
import threading
import datetime

import yaml
from ncatbot.core.api import check_and_log

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage
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


SELF_PATH = Path(__file__).parent.__str__()

_log = logger.get_log()
bot = CompatibleEnrollment
config_data: dict = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))

request_map = {}
request_id = 1616
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
                        self.output_buffer.append("\n[连接被服务器强制关闭]")
                    break
                except UnicodeDecodeError:
                    with self._lock:
                        self.output_buffer.append(f"\n[二进制数据: {data}]")
                except OSError as e:
                    if self._should_stop.is_set():
                        # 如果是主动关闭导致的错误，正常退出
                        break
                    with self._lock:
                        self.output_buffer.append(f"\n[连接错误: {str(e)}]")
                    break

            # 维护缓冲区长度
            with self._lock:
                if self.max_length > 0:
                    while len(self.output_buffer) > self.max_length:
                        self.output_buffer.pop(0)

        except Exception as e:
            with self._lock:
                self.output_buffer.append(f"\n[任务执行异常: {str(e)}]")
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

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        command: list[str] = msg.raw_message.split(" ")
        match command[0]:
            case "#生成":
                global request_id
                request_id += 1
                request_map[request_id] = Request(max_length=50, _request_id=request_id)
                request_map[request_id].nickname = msg.sender.nickname
                threading.Thread(target=self.thread_target, args=(msg, command[:], request_map[request_id])).start()
                time.sleep(0.5)
                if request_id in request_map:
                    await self.api.post_group_msg(msg.group_id, f"已创建进程 id:{request_id} 可使用\"#查询 {request_id}\"")
            case "#所有规则":
                await self.rule_list(msg)
            case "#规则列表":
                await self.rule_list(msg)
            case "#查询规则":
                await self.search_rule(command, msg)
            case "#查询":
                await self.query_thread(command, msg)
            case "#cx":
                await self.query_thread(command, msg)
            case "#帮助":
                HELP_TEXT = yaml.full_load(open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8"))
                await self.send_group_forward_msg_text(HELP_TEXT, msg)
            case "#help":
                HELP_TEXT = yaml.full_load(open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8"))
                await self.send_group_forward_msg_text(HELP_TEXT, msg)
            case "#状态":
                await self.state(msg)
            case "#state":
                await self.state(msg)
            case "#终止":
                await self.kill_thread(command, msg)
            case "#kill":
                await self.kill_thread(command, msg)
            case "#test":
                await self.rule_list(msg)

    async def search_rule(self, command, msg):
        map_data = yaml.full_load(open(f"{SELF_PATH}/map.yaml", "r", encoding="utf-8"))
        if len(command) == 1:
            await self.api.post_group_msg(msg.group_id, "请输入规则名或者规则描述")
            return
        args = command[1]
        all_rule = [rule for rules in self.all_rule() for rule in rules]
        if "/f" not in command:
            if args.upper() in map_data:
                if type(map_data[args.upper()]) is list:
                    result = args.upper() + "包含以下规则:\n["
                    result += "], [".join(map_data[args]) + "]"
                    await self.api.post_group_msg(msg.group_id, result)
                    return
                if type(map_data[args.upper()]) is str:
                    args = map_data[args.upper()]
            for rule in all_rule:
                if f"[{args.upper()}]" in rule:
                    await self.api.post_group_msg(msg.group_id, rule)
                    return
        result = []
        for rule in all_rule:
            if args in rule:
                result.append(rule)
        result = [f"共找到{len(result)}条规则描述包含字段\"{args}\""] + result
        await self.send_group_forward_msg_text(result, msg)

    async def rule_list(self, msg):
        map_data: dict = yaml.full_load(open(f"{SELF_PATH}/map.yaml", "r", encoding="utf-8"))
        rules_list = self.all_rule()
        rules_list.append([])
        for key, value in map_data.items():
            if type(value) is list:
                result = "[" + key + "]包含以下规则:\n["
                result += "], [".join(map_data[key]) + "]"
                rules_list[-1].append(result)
        news = [{"text": "左线规则列表"}, {"text": "中线规则列表"},
                {"text": "右线规则列表"}, {"text": "复合规则映射列表"}]
        await self.send_group_forward_msg_text(rules_list, msg, news=news, source="规则列表")

    def all_rule(self):
        request = Request()
        request.run_task("list --shell")
        request.wait_completion(timeout=5)
        output = request.get_output().split("hex_start:")[1].split(":hex_end")[0]
        output = bytes.fromhex(output)
        output = output.decode("utf-8").replace("\r", "")
        split_symbol, output = output[:50], output[50:]
        output = output.split(split_symbol*2)[:-1]
        rules_list: list[list] = []
        for i in range(len(output)):
            rules: list[str] = output[i].split(split_symbol)
            rules = [["左线规则", "中线规则", "右线规则"][i]] + rules
            rules_list.append(rules)
        return rules_list

    async def send_group_forward_msg_text(self, text, msg, news=None, source=None, summary=None):
        def pck(content, user_id="2947571390", nickname="老婆") -> list:
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
                uid = content.get("uid", "2947571390")
                name = content.get("name", "老婆")
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
        params = {"group_id": msg.group_id, "message": message}
        if news is not None:
            params["news"] = news
        if source is not None:
            params["source"] = source
        if summary is not None:
            params["summary"] = summary
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))

    async def send_group_forward_msg_image(self, path, msg):
        path = f"http://{HOST_IP}\\" + path
        content = [{"type": "image", "data": {"file": path, "summary": "[答案]"}}]
        message = [{"type": "node", "data": {"user_id": "2947571390", "nickname": "老婆", "content": content}}]
        params = {"group_id": msg.group_id, "message": message, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))

    async def state(self, msg):
        result = f"目前共{len(request_map.keys())}个进程正在运行"
        for key in request_map.keys():
            result += f"\n进程[{key}] 起始时间:{request_map[key].start_time}"
            result += f"\n{request_map[key].data}"
            result += f"\n调用用户:{request_map[key].nickname}"
        if len(request_map.keys()) > 7:
            await self.send_group_forward_msg_text(result, msg)
        else:
            await self.api.post_group_msg(msg.group_id, result)

    async def kill_thread(self, command, msg):
        if not command[1].isdigit():
            await self.api.post_group_msg(msg.group_id, "请输入进程id查询")
            return
        query_id = int(command[1])
        if query_id not in request_map:
            await self.api.post_group_msg(msg.group_id, "进程id不在运行")
            return
        request = request_map[query_id]
        request.close_connection()
        del request_map[query_id]
        await self.api.post_group_msg(msg.group_id, "已终止进程")

    async def query_thread(self, command, msg):
        forcibly = "/f" in command
        if forcibly:
            command.remove("/f")
        if len(command) == 1:
            await self.api.post_group_msg(msg.group_id, "请输入进程id查询")
            return
        if not command[1].isdigit():
            await self.search_rule(command, msg)
            return
        query_id = int(command[1])
        if query_id not in request_map:
            await self.api.post_group_msg(msg.group_id, "进程id不在运行中")
            return
        result = request_map[query_id].output_buffer[::-1].copy()
        if forcibly:
            await self.send_group_forward_msg_text(result[::-1][-10:], msg=msg)
            return
        for line in result:
            line: str
            if line.strip() == "":
                continue
            else:
                if "生成失败" in line:
                    await self.api.post_group_msg(msg.group_id, "生成失败,正在重试")
                    return
                if "生成用时" in line:
                    await self.api.post_group_msg(msg.group_id, "生成完毕, 正在保存为图片")
                    return
                if "进度" in line:
                    await self.api.post_group_msg(msg.group_id, line.strip())
                    return
            await self.send_group_forward_msg_text(result[::-1][-10:], msg=msg)
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
            await self.api.post_group_msg(msg.group_id, "请输入尺寸和规则, 例\"#生成 5 V\", 详情参阅\"#帮助\"", reply=msg.message_id)
            del request_map[request.request_id]
            return
        if not command[1].isdigit():
            await self.api.post_group_msg(msg.group_id, "请将题板尺寸放置在第一个参数处, 例\"#生成 5 V\"", reply=msg.message_id)
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
        if size in [["0"], ["1"], ["2"]]:
            await self.api.post_group_msg(msg.group_id, "题板大小不得为0/1/2", reply=msg.message_id)
            del request_map[request.request_id]
            return

        for rule in rules:
            rule: str
            if "^" in rule:
                rules[rules.index(rule)] = rule.replace("^", "$")

        args = "-a 1 -s "
        args += " ".join(size)
        args += " -c "
        args += " ".join(rules)
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
            await self.api.post_group_file(msg.group_id, image=config_data["out_path"] + "\\demo.png")
            await self.send_group_forward_msg_image(path=config_data["out_path"] + "\\answer.png", msg=msg)
            await self.api.post_group_msg(reply=msg.message_id, text="生成完成", group_id=msg.group_id)
        if state == 1:
            await self.api.post_group_msg(msg.group_id, f"进程[{request.request_id}]生成失败", reply=msg.message_id)
            await self.send_group_forward_msg_text(text=result, source="终端末尾输出", msg=msg)
        if state == 2:
            rule_name = result.split("未找到规则[")[-1].split("]", 1)[0]
            await self.api.post_group_msg(msg.group_id, f"未知的规则[{rule_name}]", reply=msg.message_id)

        del request_map[request.request_id]


# if __name__ == '__main__':
#     request = Request()
#     request.run_task("list --shell")
#     time.sleep(1)
#     request.wait_completion()
#     request.wait_completion()
#     output = request.get_output()[:-13]
#     print(output)
