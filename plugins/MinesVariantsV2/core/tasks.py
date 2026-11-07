"""任务生命周期：生成、查询、终止、状态、日志、命令与 DeepSeek（文案全部走 i18n）。"""
import asyncio
import base64
import json
import os
import pathlib
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import psutil

from .config import SELF_PATH, config_data, response, request_map, _log, cfg, project_path
from .schema import Msg
from .request import Request
from .utils import run_command, get_system_stats, HOST_IP, wait_for_pid


def _tail_log(log_file_name: str, size: int | None = None) -> str:
    if size is None:
        size = cfg("query", "log_tail_bytes", default=16384)
    if not os.path.exists(log_file_name):
        return ""
    with open(log_file_name, "rb") as f:
        f.seek(0, os.SEEK_END)
        f.seek(max(0, f.tell() - size))
        return f.read().decode("utf-8", errors="ignore")


def _fmt(path: str, rid: int, suffix: str) -> str:
    return os.path.join(path, str(rid) + suffix)


def _parse_interval(command: list[str], default: float) -> float:
    """解析 `#state <秒>` 的可选采样间隔，非法输入回退 default。"""
    if len(command) <= 1:
        return default
    try:
        value = float(command[1])
    except (TypeError, ValueError):
        return default
    if value <= 0:
        return default
    return value


class TasksMixin:
    # ---------------- 生成 ----------------
    def thread_target(self, msg: Msg, command: list[str], request: Request) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.spawn(msg, command, request))
        finally:
            loop.close()

    async def spawn(self, msg: Msg, command: list[str], request: Request) -> None:
        if len(command) < 2:
            await self.send_message(msg, response("prompts", "generate_usage"), reply=msg.message_id)
            request_map.pop(request.request_id, None)
            return
        if not command[1].isdigit():
            await self.send_message(msg, response("prompts", "size_position"), reply=msg.message_id)
            request_map.pop(request.request_id, None)
            return

        if msg.message[0]["type"] == "reply":
            reply_msg = await self.api.get_msg(msg.message[0]["data"]["id"])
            for part in reply_msg["data"]["message"]:
                if part["type"] != "image":
                    continue
                url = part["data"]["url"]
                for i, arg in enumerate(command):
                    if "$img" in arg:
                        command[i] = arg.replace("$img", url)
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
            await self.send_message(msg, response("prompts", "generate_usage"), reply=msg.message_id)
            request_map.pop(request.request_id, None)
            return

        rules = command
        data = rules[:]
        request.data += "尺寸:" + "x".join(size) + " 规则:" + " ".join(data)

        replacements = {"$": "$0", "^": "$1", "|": "$2", "&": "$3", ">": "$4", "<": "$5", "%": "$6"}
        for idx, rule in enumerate(rules):
            for raw, repl in replacements.items():
                if raw in rule:
                    rules[idx] = rules[idx].replace(raw, repl)

        args = "-a 1 -s " + " ".join(size) + " -c " + " ".join(rules) + " --file-name " + str(request.request_id)

        demo_img = _fmt(config_data["out_path"], request.request_id, "demo.png")
        answer_img = _fmt(config_data["out_path"], request.request_id, "answer.png")
        txt_path = _fmt(config_data["out_path"], request.request_id, ".txt")
        log_path = _fmt(config_data["log_path"], request.request_id, ".log")
        is_test = "-T" in data or "--test" in data
        state = 1

        request.run_task(args)
        await wait_for_pid(request)
        request.wait_completion()
        if request.request_id not in request_map:
            return
        result = request.get_output()
        request.output_buffer.clear()
        request.close_connection()

        if result == "":
            request_map.pop(request.request_id, None)
            return
        if "未找到规则" in result:
            state = 2
        elif (is_test or os.path.exists(demo_img)) and os.path.exists(answer_img):
            state = 0

        log_text = "[EMPTY]"
        if os.path.exists(log_path):
            with open(log_path, "rb") as f:
                f.seek(max(0, os.path.getsize(log_path) - cfg("mine_runner", "log_tail_bytes", default=4096)))
                log_text = f.read().decode("utf-8", errors="replace")

        if state == 0:
            image = answer_img if is_test else demo_img
            if hasattr(msg, "group_id"):
                await self.api.post_group_file(msg.group_id, image=image)
            else:
                await self.api.post_private_file(msg.user_id, image=image)

            if is_test:
                pathlib.Path(answer_img).unlink(missing_ok=True)
                pathlib.Path(txt_path).unlink(missing_ok=True)
                await self.send_message(msg, response("task", "completed"), reply=msg.message_id)
                request_map.pop(request.request_id, None)
                return

            with open(answer_img, "rb") as f:
                b64 = "base64://" + base64.b64encode(f.read()).decode("utf-8")
            summary = response("images", "answer")
            if hasattr(msg, "group_id"):
                await self.send_group_forward_msg_image(b64, msg, summary)
            else:
                await self.send_private_forward_msg_image(b64, msg, summary)

            pathlib.Path(answer_img).unlink(missing_ok=True)
            pathlib.Path(demo_img).unlink(missing_ok=True)
            pathlib.Path(txt_path).unlink(missing_ok=True)

            clue_img = ""
            if "线索图: " in log_text:
                clue_img = log_text.rsplit("线索图: ")[-1].split("\n")[0]
            clue = f"线索图: {clue_img}\n" if clue_img else ""
            await self.send_message(msg, clue + response("task", "completed"), reply=msg.message_id)

        elif state == 1:
            if request.request_id not in request_map:
                return
            str_length = cfg("mine_runner", "error_str_length", default=1000)
            msg_length = cfg("mine_runner", "error_msg_length", default=9)
            tail_lines = cfg("mine_runner", "error_tail_lines", default=50)
            err = log_text + "\n\n" + "\n".join(result.split("\n")[-tail_lines:])
            err_result = [err[i:i + str_length] for i in range(0, len(err), str_length)][-msg_length:]
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, response("task", "failed").format(request.request_id), reply=msg.message_id)
                resp = await self.send_group_forward_msg_text(err_result, msg, source=response("categories", "terminal_output"))
                if resp and resp.get("status", "") != "ok":
                    await self.api.post_group_msg(msg.group_id, response("forward", "output_failed"))
            else:
                await self.api.post_private_msg(msg.user_id, response("task", "failed").format(request.request_id), reply=msg.message_id)
                resp = await self.send_private_forward_msg_text(err_result, msg, source=response("categories", "terminal_output"))
                if resp and resp.get("status", "") != "ok":
                    await self.api.post_private_msg(msg.user_id, response("forward", "output_failed"))

        elif state == 2:
            rule_name = result.split("未找到规则[")[-1].split("]", 1)[0]
            await self.send_message(msg, response("errors", "unknown_rule").format(rule_name), reply=msg.message_id)

        request_map.pop(request.request_id, None)

    # ---------------- DeepSeek ----------------
    def thread_deepseek(self, msg: Msg, command: list[str], request: Request) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.deepseek_summon(msg, command, request))
        finally:
            loop.close()

    async def deepseek_summon(self, msg: Msg, command: list[str], request: Request) -> None:
        rule_id = command[1]
        with open(os.path.join(SELF_PATH, "fanmade_doc", "rule", "ruleTodo.json"), "r", encoding="utf-8") as f:
            rule_todo = json.load(f)
        rule_data = next((r for r in rule_todo if r["name"] == rule_id), None)
        if rule_data is None:
            await self.send_message(msg, response("prompts", "rule_not_found"))
            request_map.pop(request.request_id, None)
            return

        rule_content = response("categories", "todo_rule_fmt").format(
            rule_data["name"], rule_data["doc"], rule_data["author_name"], rule_data["author_uid"],
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(rule_data["time"])),
        )

        log_dir = cfg("deepseek", "log_path", default=config_data.get("deepseek_log_path"))
        work_dir = cfg("deepseek", "work_dir", default=r"D:\0.0\lib\ds-browser")
        test_log = os.path.join(log_dir, cfg("deepseek", "test_log", default=r"logs\latest-test.log"))
        open(test_log, "w", encoding="utf-8").close()

        process = await asyncio.create_subprocess_shell(
            cfg("deepseek", "save_rule_bat", default="save_rule.bat"),
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
        )
        await process.communicate(input=rule_content.encode("utf-8"))
        if process.returncode != 0:
            await self.send_message(msg, response("deepseek", "task_usage"))
            request_map.pop(request.request_id, None)
            return

        process = await asyncio.create_subprocess_shell(
            cfg("deepseek", "run_bat", default="run.bat") + ("-u" if "-u" in command else ""),
            cwd=work_dir,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            stdin=None,
        )
        request.pid = process.pid
        request.data = response("deepseek", "impl_rule").format(rule_id)
        await process.wait()
        if request.request_id not in request_map:
            return
        if process.returncode != 0:
            await self.send_message(msg, response("deepseek", "impl_fail"), reply=msg.message_id)
        else:
            await self.send_message(msg, response("deepseek", "impl_done"), reply=msg.message_id)
            await self.pull(msg)
        request_map.pop(request.request_id, None)

    # ---------------- 查询 ----------------
    async def query_thread(self, msg: Msg, command: list[str] | None = None) -> None:
        if command is None:
            raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
            command = raw_message.split()
        forcibly = "/f" in command
        if forcibly:
            command.remove("/f")
        if len(command) == 1:
            await self.send_message(msg, response("task", "unid"))
            return
        if not command[1].isdigit():
            await self.search_rule(msg)
            return

        default_str_length = cfg("query", "default_str_length", default=2000)
        max_chunks = cfg("query", "max_chunks", default=100)
        str_budget = cfg("query", "str_budget", default=12000)

        if len(command) > 2 and command[2].isdigit() and int(float(command[2])) >= 1:
            str_length = int(float(command[2]))
        else:
            str_length = default_str_length

        if len(command) > 3 and command[3].isdigit():
            msg_length = int(float(command[3]))
            if msg_length < 1:
                msg_length = 8000 // str_length
            msg_length = min(msg_length, max_chunks)
        else:
            msg_length = str_budget // str_length

        query_id = int(command[1])
        if query_id not in request_map:
            await self.send_message(msg, response("task", "not_found"))
            return

        result = request_map[query_id].get_output()
        log_text = _tail_log(os.path.join(config_data["log_path"], str(query_id) + ".log"))
        if result == "":
            await self.send_message(msg, response("task", "empty_output"))
            return
        if request_map[query_id].task_type == "DEEPSEEK":
            forcibly, log_text, result = True, result, ""

        if not forcibly:
            reply_text = ""
            if "生成用时" in log_text:
                await self.send_message(msg, response("progress", "saving_image"))
                return
            if "尝试第" in log_text and "次minesweepervariants" in log_text:
                try_index = int(log_text.rsplit("尝试第", 1)[1].rsplit("次minesweepervariants")[0])
                if try_index > 1:
                    reply_text += response("progress", "retrying").format(try_index)
            for line in reversed(result.split("\n")):
                if not line.strip():
                    continue
                if "进度" in line:
                    await self.send_message(msg, ((reply_text + "\n") if reply_text else "") + line)
                    return
            if reply_text:
                await self.send_message(msg, reply_text)
                return

        reply_text = log_text + "\n" + "\n".join(result.split("\n")[-10:])
        chunks = [reply_text[i:i + str_length] for i in range(0, len(reply_text), str_length)][-msg_length:]
        if hasattr(msg, "group_id"):
            resp = await self.send_group_forward_msg_text(chunks, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_group_msg(msg.group_id, response("forward", "send_failed"))
        else:
            resp = await self.send_private_forward_msg_text(chunks, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_private_msg(msg.user_id, response("forward", "send_failed"))

    def _query_thread(self, query_id: int) -> str:
        if request_map[query_id].task_type == "DEEPSEEK":
            return ""
        result = request_map[query_id].get_output()
        log_text = _tail_log(os.path.join(config_data["log_path"], str(query_id) + ".log"))
        reply_text = ""
        if "生成用时" in log_text:
            return response("progress", "saving_image")
        if "尝试第" in log_text and "次minesweepervariants" in log_text:
            try_index = int(log_text.rsplit("尝试第", 1)[1].rsplit("次minesweepervariants")[0])
            if try_index > 1:
                reply_text += response("progress", "retrying").format(try_index)
        for line in reversed(result.split("\n")):
            if not line.strip():
                continue
            if "进度" in line:
                parts = line.split("用时:", 1)
                if len(parts) < 2:
                    return reply_text + "\n" + line
                return reply_text + "\n用时:" + parts[1]
        return reply_text

    # ---------------- 终止 ----------------
    async def kill_thread(self, command: list[str], msg: Msg) -> None:
        kill_list = []
        if "all" in command or "a" in command:
            command.extend([str(i) for i in request_map.keys()] + ["0"])
        for arg in command[1:]:
            if arg.isdigit():
                kill_list.append(int(arg))
        if not kill_list:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, response("errors", "invalid_input"))
            else:
                await self.api.post_private_msg(msg.user_id, response("errors", "invalid_input"))
            return

        terminated = []
        for qid in kill_list:
            if qid not in request_map:
                continue
            if not self.is_user(msg.sender.user_id):
                if request_map[qid].nickname != msg.sender.nickname:
                    continue
            req = request_map.pop(qid)
            req.close_connection()
            terminated.append(qid)

        text = response("task", "terminated").format(f"[{', '.join(str(i) for i in terminated)}]")
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, text)
        else:
            await self.api.post_private_msg(msg.user_id, text)

    # ---------------- 状态 ----------------
    async def state(self, msg: Msg) -> None:
        def _block(key: int, proc_info: Request, interval: float) -> str:
            block = "\n" + response("status", "process_info", "1").format(key, proc_info.pid, proc_info.start_time)
            block += response("status", "process_info", "2").format(proc_info.data)
            block += response("status", "process_info", "3").format(proc_info.nickname)
            if proc_info.pid:
                try:
                    process = psutil.Process(proc_info.pid)
                    rss = process.memory_info().rss
                    memory_info = "NAN"
                    for unit in ["B", "KB", "MB", "GB"]:
                        if rss < 1024.0:
                            memory_info = f"{rss:.1f}{unit}"
                            break
                        rss /= 1024.0
                    cpu_usage = round(process.cpu_percent(interval=interval) / psutil.cpu_count(), 2)
                    block += "\n" + response("status", "process_info", "4").format(cpu_usage, memory_info)
                except Exception:
                    pass
            block += self._query_thread(key)
            return block

        async def _main() -> None:
            command = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip().split()
            interval = _parse_interval(command, config_data["interval"])
            result = response("status", "total_processes").format(len(request_map))
            keys = list(request_map.keys())

            with ThreadPoolExecutor(max_workers=len(keys) + 1) as executor:
                future_sys = executor.submit(get_system_stats, interval)
                process_futures = [executor.submit(_block, k, request_map[k], interval) for k in keys]
                sys_stats = future_sys.result()
                blocks = [fut.result() for fut in process_futures]

            result += "\n" + sys_stats + "".join(blocks)
            if len(keys) > 3:
                if hasattr(msg, "group_id"):
                    resp = await self.send_group_forward_msg_text(result, msg)
                    if resp and resp.get("status", "") != "ok":
                        await self.api.post_group_msg(msg.group_id, response("forward", "merge_failed"))
                else:
                    resp = await self.send_private_forward_msg_text(result, msg)
                    if resp and resp.get("status", "") != "ok":
                        await self.api.post_private_msg(msg.user_id, response("forward", "merge_failed"))
            else:
                if hasattr(msg, "group_id"):
                    await self.api.post_group_msg(msg.group_id, result)
                else:
                    await self.api.post_private_msg(msg.user_id, result)

        threading.Thread(target=lambda: asyncio.run(_main()), daemon=True).start()

    # ---------------- 日志 ----------------
    async def get_log(self, msg: Msg, log_id: str | None = None) -> None:
        from ncatbot.core.api import check_and_log

        async def _reply(target: int, text: str) -> None:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(target, text)
            else:
                await self.api.post_private_msg(target, text)

        if log_id is None:
            command = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip().split()
            target = msg.group_id if hasattr(msg, "group_id") else msg.user_id
            if len(command) < 2:
                await _reply(target, response("prompts", "log_format_error"))
                return
            log_id = command[1]
            if not log_id.isdigit():
                await _reply(target, response("prompts", "log_id_format_error"))
                return
        log_id = int(log_id)
        log_path = os.path.join(config_data["log_path"], f"{log_id}.log")
        if not os.path.exists(log_path):
            target = msg.group_id if hasattr(msg, "group_id") else msg.user_id
            await _reply(target, response("prompts", "log_unfind_error"))
            return

        url_path = "http://" + HOST_IP + "/" + log_path.replace(":", "%3A").replace("\\", "/")
        payload = {"message": [{"type": "file", "data": {"file": url_path, "name": f"{log_id}.log.txt"}}]}
        if hasattr(msg, "group_id"):
            payload["group_id"] = msg.group_id
            return check_and_log(await self.api._http.post("/send_group_msg", json=payload))
        payload["user_id"] = msg.user_id
        return check_and_log(await self.api._http.post("/send_private_msg", json=payload))

    # ---------------- 命令 ----------------
    async def command(self, command: str, msg: Msg) -> None:
        reply_text = ""
        if msg.message[0]["type"] == "reply":
            reply_msg = await self.api.get_msg(msg.message[0]["data"]["id"])
            for part in reply_msg["data"]["message"]:
                if part["type"] == "text":
                    reply_text = part["data"]["text"]
                    break
        returncode, stdout, stderr = await run_command(command, project_path(), input_str=reply_text)
        if not stdout:
            await self.api.post_group_msg(msg.group_id, response("command", "running_error") + stderr)
            return
        clip = cfg("query", "force_stdout_chars", default=5000)
        lines = [
            response("diag", "run_command").format(command),
            stdout[max(0, len(stdout) - clip):],
            response("diag", "exit_code").format(returncode),
            response("diag", "stderr").format(stderr[max(0, len(stderr) - clip):]),
        ]
        await self.send_group_forward_msg_text(lines, msg)
