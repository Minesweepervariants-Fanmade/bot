"""规则缓存、查询、注册与仓库同步（文案全部走 i18n）。"""
import asyncio
import json
import os
import random
import time
from typing import Awaitable, Callable

import regex
import requests

from .schema import Msg

from .config import SELF_PATH, config_data, response, _log, REG_LOCK, cfg, project_path

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
from .request import Request
from .utils import run_command, split_by_content_length, get_rule_image

ALL_RULE: list = []


def _fetch_bytes(url: str) -> bytes:
    """同步拉取图片字节（供 asyncio.to_thread 调用）。"""
    headers = {"User-Agent": cfg("http", "user_agent", default=DEFAULT_UA)}
    resp = requests.get(url, headers=headers, timeout=cfg("http", "timeout", default=30))
    resp.raise_for_status()
    return resp.content


def update_all_rules(timeout: int | None = None) -> bool:
    """请求后端重新导出 rule.json 并清空缓存。"""
    if timeout is None:
        timeout = cfg("update_rules_timeout", default=20)
    global ALL_RULE
    retries = cfg("update_rules_retries", default=6)
    _log.info("发起更新规则列表")
    for _ in range(retries):
        try:
            request = Request()
            request.run_task(f"list --json -F {SELF_PATH}/rule.json", mode="BIN")
            request.wait_completion(timeout=timeout)
        except Exception:
            _log.warning("更新规则列表失败，重试", exc_info=True)
            continue
        ALL_RULE = []
        return True
    return False


class RulesMixin:
    async def rule_list(self, msg: Msg) -> None:
        await self.send_message(msg, response("rules", "rule_list"))

    async def search_rule(self, msg: Msg, command: list[str] | None = None) -> None:
        if command is None:
            raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
            command = raw_message.split()
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
            _arg = arg.split("/rand")[1]
            if _arg and not _arg.isdigit():
                continue
            args.remove(arg)
            on_random = int(_arg) if _arg else 1

        upper = "/u" in args
        if upper:
            args.remove("/u")
        only_name = "/n" in args
        if only_name:
            args.remove("/n")

        flags = {}
        for key in ("/r", "/l", "/m", "/t"):
            lower, upper_key = key, key.upper()
            found = lower in args or upper_key in args
            if lower in args:
                args.remove(lower)
            if upper_key in args:
                args.remove(upper_key)
            flags[key[1]] = found
        only_R, only_L, only_M, only_T = flags["r"], flags["l"], flags["m"], flags["t"]

        page = -1
        for arg in args[:]:
            if not arg.startswith("/p"):
                continue
            _arg = arg.split("/p")[1]
            if not _arg.isdigit():
                continue
            args.remove(arg)
            page = int(_arg)

        only_switch = only_R or only_L or only_M or only_T
        patterns = [
            regex.compile(arg, *([regex.IGNORECASE] if not upper else [])) if regular else arg
            for arg in args
        ]

        all_rule = self.all_rule()
        result = []

        if len(args) == 1 and not forcibly and not regular and not on_random:
            for rules_index, rules in enumerate(all_rule):
                if only_switch and not [only_L, only_M, only_R, only_T][rules_index]:
                    continue
                for rule in rules:
                    names = rule["name"]
                    if args[0] in names or (
                        not upper and args[0].lower() in [n.lower() for n in names]
                    ):
                        doc = rule.get("doc").get("content")
                        image = rule.get("doc").get("image")
                        await self.send_message(msg, doc, image_path=image)
                        return

        for rules_index, rules in enumerate(all_rule):
            if only_switch and not [only_L, only_M, only_R, only_T][rules_index]:
                continue
            for rule in rules:
                rule_doc = rule["doc"]
                content = rule_doc["content"]
                if isinstance(rule_doc, dict):
                    rule_doc = rule_doc.copy()
                if only_name:
                    if regular:
                        rt = cfg("regex_timeout", default=0.2)
                        matched = all(any(p.search(n, timeout=rt) for n in rule["name"]) for p in patterns)
                    else:
                        matched = all(
                            any((p in n) if upper else (p.lower() in n.lower()) for n in rule["name"])
                            for p in args
                        )
                else:
                    if regular:
                        matched = all(p.search(content, timeout=cfg("regex_timeout", default=0.2)) for p in patterns)
                    else:
                        matched = all(
                            (p in content) if upper else (p.lower() in content.lower()) for p in args
                        )
                if matched:
                    result.append(rule_doc)

        result_length = len(result)
        if on_random:
            result = random.sample(result, k=min(on_random, len(result)))
        if page > -1:
            chunks = split_by_content_length(result)
            result = chunks[page] if 0 <= page < len(chunks) else []
        if page < 0 and ((result_length if on_random == 0 else on_random) > 100):
            result = split_by_content_length(result)
            if len(result) == 1:
                result = result[0]
        if on_random == 1 and not forcibly and result:
            await self.send_message(
                msg, result[0].get("content", response("rules", "empty_doc")), image_path=result[0].get("image")
            )
            return

        result = [response("rules", "found_rules").format(result_length, args)] + result
        if msg.message_type == "group":
            resp = await self.send_group_forward_msg_text(result, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_group_msg(msg.group_id, response("forward", "search_failed"))
        elif msg.message_type == "private":
            resp = await self.send_private_forward_msg_text(result, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_private_msg(msg.user_id, response("forward", "search_failed"))

    def all_rule(self) -> list[list[dict]]:
        """返回分组规则缓存：[{name, doc, author}, ...] × 4 组。"""
        global ALL_RULE
        if ALL_RULE:
            return ALL_RULE
        with open(f"{SELF_PATH}/rule.json", "r", encoding="utf-8") as f:
            rule_json = json.load(f)

        rules_list = []
        for key in rule_json:
            rules_list.append([])
            for rule_dict in rule_json[key]:
                author = rule_dict["author"]
                image = (
                    os.path.join(config_data["image_path"], rule_dict["image"])
                    if rule_dict["image"]
                    else ""
                )
                on_user = author["id"] is not None and author["id"] and int(author["id"]) > 0
                rule_data = {
                    "name": [rule_dict["id"]]
                    + list(rule_dict["name"].values())
                    + list(rule_dict.get("aliases", [])),
                    "doc": {
                        "content": "",
                        "uid": author["id"] if on_user else None,
                        "name": author["name"] if on_user else None,
                        "image": image if os.path.exists(image) else "",
                    },
                    "author": (author["id"], author["name"]) if on_user else (None, None),
                }
                content = f'[{rule_dict["id"]}]'
                content += f'{rule_dict["name"].get("zh_CN", rule_dict["name"].get("default", ""))}'
                content += f': {rule_dict["doc"].get("zh_CN", rule_dict["doc"].get("default", response("rules", "empty_doc")))}'
                if author["name"] or (author["id"].isdigit() and int(author["id"]) > 1):
                    content += f"\n作者:{author['name']} ({author['id']})"
                if rule_dict["creation_time"]:
                    content += f"\n时间:{rule_dict['creation_time']}"
                rule_data["doc"]["content"] = content
                rules_list[-1].append(rule_data)

        with open(f"{SELF_PATH}/fanmade_doc/rule/ruleTodo.json", "r", encoding="utf-8") as f:
            rule_todo_list = json.load(f)
        todo_rule_fmt = response("categories", "todo_rule_fmt")
        rules_list.append([])
        for data in rule_todo_list:
            image = ""
            if "image" in data:
                image = f"{SELF_PATH}\\fanmade_doc\\rule\\image\\" + data.get("image")
            on_user = data["author_uid"] is not None and int(data["author_uid"]) > 0
            rules_list[-1].append(
                {
                    "name": [data["name"]],
                    "author": (
                        data["author_name"] if on_user else None,
                        data["author_uid"] if on_user else None,
                    ),
                    "doc": {
                        "content": todo_rule_fmt.format(
                            data["name"],
                            data["doc"],
                            data["author_name"],
                            data["author_uid"],
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(data["time"])),
                        ),
                        "name": data["author_name"] if on_user else None,
                        "uid": data["author_uid"] if on_user else None,
                        "image": image if os.path.exists(image) else "",
                    },
                }
            )
        ALL_RULE = rules_list
        return ALL_RULE

    async def push_todo_rule(
        self, callback: Callable[[], Awaitable[str]], msg: Msg
    ) -> None:
        """同步远程 doc 分支 -> 回调修改 -> 提交并推送。"""
        repo_path = os.path.join(SELF_PATH, "fanmade_doc", "rule")
        async with REG_LOCK:
            await run_command("git fetch origin doc", cwd=repo_path)
            ret, _, _ = await run_command("git reset --hard origin/doc", cwd=repo_path)
            if ret != 0:
                await self.send_message(msg, response("git", "sync_failed"))
                return

            commit_msg = await callback()
            ALL_RULE.clear()
            self.all_rule()

            await run_command("git add -A", cwd=repo_path)
            ret, _, _ = await run_command(f'git commit -m "{commit_msg}"', cwd=repo_path)
            if ret != 0:
                await self.send_message(msg, response("git", "no_change"))
                return

            ret, _, _ = await run_command("git push origin doc", cwd=repo_path)
            if ret != 0:
                await run_command("git pull --rebase origin doc", cwd=repo_path)
                ret, _, _ = await run_command("git push origin doc", cwd=repo_path)
                if ret != 0:
                    await self.send_message(msg, response("git", "push_failed"))
                    return

            ret, hash_out, _ = await run_command("git rev-parse origin/doc", cwd=repo_path)
            if ret == 0 and hash_out:
                self.data["last_remote_hash_doc"] = hash_out.strip()
                await self.send_message(msg, response("git", "pushed"))

    async def register_rules(self, msg: Msg, name: str, doc: str) -> None:
        reply = None
        _image_bytes = None
        if msg.message[0]["type"] == "reply":
            reply = msg.message[0]["data"]["id"]
            reply_msgs = await self.api.get_msg(reply)
            for part in reply_msgs["data"]["message"]:
                if part["type"] == "image":
                    _image_bytes = await asyncio.to_thread(
                        _fetch_bytes, part["data"]["url"]
                    )
                    break

        with open(f"{SELF_PATH}/fanmade_doc/rule/ruleTodo.json", "r", encoding="utf-8") as f:
            rule_todo = json.load(f)

        rule_data = None
        _doc = ""
        for rule in rule_todo:
            if rule["name"] == name:
                if int(rule["author_uid"]) != int(msg.user_id) and not self.is_admin(msg.user_id):
                    await self.send_message(msg, response("categories", "todo_rule_unauthor"))
                    return
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

        repo_path = os.path.join(SELF_PATH, "fanmade_doc", "rule")
        json_path = os.path.join(repo_path, "ruleTodo.json")
        image_dir = os.path.join(repo_path, "image")
        os.makedirs(image_dir, exist_ok=True)
        image_name = get_rule_image(name) + ".png"
        image_path = os.path.join(image_dir, image_name)

        async def callback() -> str:
            if doc and _image_bytes:
                with open(image_path, "wb") as f:
                    f.write(_image_bytes)
                rule_data["image"] = image_name
                await run_command(f'git add "{image_path}"', cwd=repo_path)

            if (doc and not reply) or (not doc):
                if os.path.exists(image_path):
                    os.remove(image_path)
                    await run_command(f'git add "{image_path}"', cwd=repo_path)
                    if "image" in rule_data:
                        del rule_data["image"]

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rule_todo, f, ensure_ascii=False, indent=4)

            if doc:
                tpl = "todo_rule_update" if _doc else "todo_rule_create"
                fmt = response("categories", tpl)
                await self.send_message(msg, fmt.format(name, _doc) if _doc else fmt.format(name))
            else:
                await self.send_message(msg, response("categories", "todo_rule_del").format(name, _doc))
            return f"User[{msg.sender.nickname}] " + ("update" if doc else "delete") + f" RULE[{name}]"

        await self.push_todo_rule(callback, msg)

    async def todo_rule_rename(
        self, msg: Msg, command: list[str] | None = None
    ) -> None:
        if command is None:
            raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
            command = raw_message.split()
        if len(command) < 3:
            await self.send_message(msg, response("rename", "fmt_error"))
            return

        repo_path = os.path.join(SELF_PATH, "fanmade_doc", "rule")
        json_path = os.path.join(repo_path, "ruleTodo.json")
        image_dir = os.path.join(repo_path, "image")
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                rule_todo = json.load(f)
        except Exception as e:
            await self.send_message(msg, response("rename", "read_failed").format(e))
            return

        rule_id, target_rule_id = command[1], command[2]
        source_rule = next((r for r in rule_todo if r["name"] == rule_id), None)
        if source_rule is None:
            await self.send_message(msg, response("rename", "not_found").format(rule_id))
            return
        if not self.is_admin(msg.user_id) and source_rule["author_uid"] != msg.user_id:
            await self.send_message(msg, response("categories", "todo_rule_unauthor"))
            return
        if rule_id == target_rule_id:
            await self.send_message(msg, response("rename", "same"))
            return

        async def callback() -> str:
            for _rule in rule_todo:
                if _rule["name"] == target_rule_id and _rule is not source_rule:
                    await self.send_message(msg, response("rename", "occupied").format(target_rule_id))
                    return ""
            old_image = source_rule.get("image")
            if old_image:
                old_path = os.path.join(image_dir, old_image)
                new_image_name = get_rule_image(target_rule_id) + ".png"
                new_path = os.path.join(image_dir, new_image_name)
                if os.path.exists(old_path) and old_image != new_image_name:
                    try:
                        os.replace(old_path, new_path)
                        source_rule["image"] = new_image_name
                    except Exception as e:
                        await self.send_message(msg, response("rename", "image_failed").format(e))
                        return ""
            source_rule["name"] = target_rule_id
            source_rule["time"] = time.time()
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(rule_todo, f, ensure_ascii=False, indent=4)
            await self.send_message(msg, response("rename", "done").format(rule_id, target_rule_id))
            return f"rename: 规则 [{rule_id}] -> [{target_rule_id}] 由 {msg.sender.nickname}"

        await self.push_todo_rule(callback, msg)
        ALL_RULE.clear()
        self.all_rule()

    async def chown(self, msg: Msg, command: list[str] | None = None) -> None:
        if command is None:
            raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
            command = raw_message.split()
        if len(command) < 3:
            await self.send_message(msg, response("chown", "fmt_error"))
            return

        rule_id, new_author_name = command[1], command[2]
        new_author_uid = int(command[3]) if len(command) >= 4 and command[3].isdigit() else -1
        todo_path = os.path.join(SELF_PATH, "fanmade_doc", "rule", "ruleTodo.json")
        if not os.path.exists(todo_path):
            await self.send_message(msg, response("chown", "todo_missing"))
            return

        async def callback() -> str:
            with open(todo_path, "r", encoding="utf-8") as f:
                rule_todo = json.load(f)
            target = next((r for r in rule_todo if r["name"] == rule_id), None)
            if target is None:
                await self.send_message(msg, response("rename", "not_found").format(rule_id))
                return ""
            old_name, old_uid = target["author_name"], target["author_uid"]
            target["author_name"] = new_author_name
            if new_author_uid is not None:
                target["author_uid"] = new_author_uid
            with open(todo_path, "w", encoding="utf-8") as f:
                json.dump(rule_todo, f, ensure_ascii=False, indent=4)
            if new_author_uid:
                await self.send_message(msg, response("chown", "done_uid").format(rule_id, new_author_name, new_author_uid))
            else:
                await self.send_message(msg, response("chown", "done").format(rule_id, new_author_name))
            return f"chown: 修改规则 [{rule_id}] 作者从 {old_name}({old_uid}) 为 {new_author_name}({new_author_uid})"

        await self.push_todo_rule(callback, msg)
        ALL_RULE.clear()
        self.all_rule()

    async def pull(self, msg: Msg) -> None:
        await self.send_message(msg, response("git", "start_pull"))
        result = []
        proj_path = project_path()

        _, branch, _ = await run_command("git rev-parse --abbrev-ref HEAD", proj_path)
        branch = branch.strip()
        if not branch:
            result.append(response("git", "branch_error"))
            await self._send_forward_text(result, msg)
            return

        _, pre_main, _ = await run_command("git rev-parse HEAD", proj_path)
        pre_main = pre_main.strip()

        rc, out, err = await run_command("git fetch --all --prune", proj_path)
        result.append(response("diag", "git_cmd").format("git fetch --all --prune"))
        result.append(response("diag", "git_exit").format(rc))
        if out.strip():
            result.append(response("diag", "git_stdout").format(out.strip()))
        if err.strip():
            result.append(response("diag", "git_stderr").format(err.strip()))

        rc, out, err = await run_command(f"git reset --hard origin/{branch}", proj_path)
        result.append(response("diag", "git_cmd").format(f"git reset --hard origin/{branch}"))
        result.append(response("diag", "git_exit").format(rc))
        if out.strip():
            result.append(response("diag", "git_stdout").format(out.strip()))
        if err.strip():
            result.append(response("diag", "git_stderr").format(err.strip()))

        _, main_log, _ = await run_command(
            f'git log {pre_main}..HEAD --pretty=format:"  - %h %s (%an, %ad)" --date=short',
            proj_path,
        )
        result.append(response("diag", "main_new"))
        result.append(main_log.strip() if main_log.strip() else response("diag", "main_none"))

        _, status, _ = await run_command("git submodule status", proj_path)
        sub_paths, pre_sub_shas = [], {}
        for line in status.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                sp = parts[1]
                sub_paths.append(sp)
                sub_cwd = os.path.join(proj_path, sp)
                if os.path.isdir(os.path.join(sub_cwd, ".git")) or os.path.isfile(os.path.join(sub_cwd, ".git")):
                    _, sha, _ = await run_command("git rev-parse HEAD", sub_cwd)
                    pre_sub_shas[sp] = sha.strip() if sha else ""

        rc, out, err = await run_command("git submodule update --init --recursive --force --remote", proj_path)
        result.append(response("diag", "git_cmd").format("git submodule update --init --recursive --force --remote"))
        result.append(response("diag", "git_exit").format(rc))
        if out.strip():
            result.append(response("diag", "git_stdout").format(out.strip()))
        if err.strip():
            result.append(response("diag", "git_stderr").format(err.strip()))

        result.append(response("diag", "sub_header"))
        has_change = False
        for sp in sub_paths:
            sub_cwd = os.path.join(proj_path, sp)
            if not (os.path.isdir(os.path.join(sub_cwd, ".git")) or os.path.isfile(os.path.join(sub_cwd, ".git"))):
                result.append(response("diag", "sub_uninit").format(sp))
                continue
            _, new_sha, _ = await run_command("git rev-parse HEAD", sub_cwd)
            new_sha = new_sha.strip()
            old_sha = pre_sub_shas.get(sp, "")
            if old_sha and new_sha and old_sha != new_sha:
                has_change = True
                _, log, _ = await run_command(
                    f'git log {old_sha}..{new_sha} --pretty=format:"    - %h %s (%an, %ad)" --date=short',
                    sub_cwd,
                )
                result.append(response("diag", "sub_log").format(sp))
                result.append(log.strip() if log.strip() else response("diag", "sub_sha_change").format(sp))
            else:
                result.append(response("diag", "sub_none").format(sp))
        if not has_change:
            result.append(response("diag", "sub_no_change"))

        update_all_rules()
        await self._send_forward_text(result, msg)

    async def _send_forward_text(self, result: list[str], msg: Msg) -> None:
        if hasattr(msg, "group_id"):
            resp = await self.send_group_forward_msg_text(result, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_group_msg(msg.group_id, response("forward", "output_failed"))
        else:
            resp = await self.send_private_forward_msg_text(result, msg)
            if resp and resp.get("status", "") != "ok":
                await self.api.post_private_msg(msg.user_id, response("forward", "output_failed"))
