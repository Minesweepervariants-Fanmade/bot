"""MinesVariantsV2 插件入口（重构版）。

与原 MinesVariants 功能一致，但：
- 按职责拆到 core/ 子模块
- 所有 bot 文案外置到 i18n/zh_CN.yaml
- 权限改为统一数字等级：-1=ban, 0=普通, 1=user, 2=admin
"""
import json
import os
import threading

import yaml
from ncatbot.core.api import check_and_log
from ncatbot.plugin import BasePlugin, CompatibleEnrollment

from .core.config import SELF_PATH, response, request_map, _log, cfg
from .core.hints import HintsMixin
from .core.messaging import MessagingMixin
from .core.permissions import (
    ADMIN,
    BAN,
    NORMAL,
    USER,
    PermissionsMixin,
    level_name,
)
from .core.request import Request
from .core.rules import RulesMixin, update_all_rules
from .core.tasks import TasksMixin

bot = CompatibleEnrollment


def _raw_text(msg) -> str:
    return "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()


class MinesVariantsV2(
    BasePlugin, PermissionsMixin, MessagingMixin, RulesMixin, TasksMixin, HintsMixin
):
    name = "MinesVariantsV2"
    version = "2.1.0"

    # ---------------- 生命周期 ----------------
    async def on_load(self):
        if self.data.get("id") is None:
            self.data["id"] = 0
        self.init_levels()
        self.data.save()

    # ---------------- 事件入口 ----------------
    @bot.private_event()
    async def on_private_event(self, msg):
        await self._handle(msg, is_group=False)

    @bot.group_event()
    async def on_group_event(self, msg):
        await self._handle(msg, is_group=True)

    async def _handle(self, msg, is_group: bool):
        if self.is_banned(msg.user_id):
            return
        try:
            raw_message = _raw_text(msg)
            if not raw_message.startswith("#"):
                return
            command = raw_message.split()
            if not command:
                return
            await self._dispatch(msg, command, raw_message, is_group)
        except Exception as e:
            _log.error(f"处理命令出错: {e}", exc_info=True)
            if is_group:
                try:
                    await self.api.post_group_msg(msg.group_id, response("errors", "cmd_exception").format(e))
                except Exception:
                    pass

    # ---------------- 命令分发 ----------------
    async def _dispatch(self, msg, command, raw_message, is_group: bool):
        head = command[0]

        if head in ("#生成", "#sc", "#summon", "#run"):
            await self._start_generate(msg, command, is_group)
            return
        if head in ("#所有规则", "#规则列表", "#list", "#ls"):
            await self.rule_list(msg)
            return
        if head in ("#查询规则", "#cxr"):
            await self.search_rule(msg)
            return
        if head == "#log":
            await self.get_log(msg, command[1] if len(command) > 1 else None)
            return
        if head in ("#查询", "#cx"):
            await self.query_thread(msg)
            return
        if head in ("#帮助", "#help", "#?"):
            await self._send_help(msg, is_group)
            return
        if head in ("#状态", "#state", "##"):
            await self.state(msg)
            return
        if head in ("#终止", "#kill", "#k"):
            await self.kill_thread(command, msg)
            return
        if head == "#pull":
            await self.pull(msg)
            return
        if head == "#update":
            await self._do_update(msg, command, is_group)
            return

        # ---------- 仅群聊 ----------
        if is_group and head in ("#hint", "#提示"):
            await self.get_hint(msg, command[1] if len(command) > 1 else "")
            return
        if is_group and head in ("#cmd", "#$"):
            if not await self._require_admin(msg):
                return
            await self.command(" ".join(command[1:]), msg)
            return
        if is_group and head in ("#修改名字", "#rename"):
            await self.todo_rule_rename(msg, command)
            return
        if is_group and head in ("#修改作者", "#chown"):
            if not await self._require_admin(msg):
                return
            await self.chown(msg)
            return
        if is_group and head in ("#注册规则", "#reg"):
            await self._register(msg, command, raw_message)
            return
        if is_group and head == "#op":
            await self._op(msg, command)
            return
        if is_group and head == "#deop":
            await self._set_level_cmd(msg, command, NORMAL, "deop_done")
            return
        if is_group and head == "#ban":
            await self._set_level_cmd(msg, command, BAN, "ban_done")
            return
        if is_group and head == "#unban":
            await self._set_level_cmd(msg, command, NORMAL, "unban_done")
            return
        if is_group and head == "#del":
            if not await self._require_admin(msg):
                return
            if msg.message[0]["type"] == "reply":
                await self.api.delete_msg(msg.message[0]["data"]["id"])
                await self.api.delete_msg(msg.message_id)
            return
        if is_group and head == "#dsmsg":
            await self._dsmsg(msg, raw_message)
            return
        if is_group and head == "#ds":
            await self._start_deepseek(msg, command)
            return

        # ---------- 综合 / 默认 ----------
        if head == "#":
            await self.shape(msg)
        else:
            await self.shape(msg, raw_message[1:].split())

    # ---------------- 各命令实现 ----------------
    async def _start_generate(self, msg, command, is_group):
        self.data["id"] += 1
        self.data.save()
        rid = self.data["id"]
        req = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=rid)
        req.nickname = msg.sender.nickname
        request_map[rid] = req
        threading.Thread(target=self.thread_target, daemon=True, args=(msg, command[:], req)).start()
        target = msg.group_id if is_group else msg.user_id
        poster = self.api.post_group_msg if is_group else self.api.post_private_msg
        await poster(target, response("task", "created").format(rid))

    async def _start_deepseek(self, msg, command):
        if not self.is_user(msg.user_id):
            await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
            return
        if len(command) == 1:
            await self.api.post_group_msg(msg.group_id, response("deepseek", "cmd_error"))
            return
        rule_id = command[1]
        with open(os.path.join(SELF_PATH, "fanmade_doc", "rule", "ruleTodo.json"), "r", encoding="utf-8") as f:
            rule_todo = json.load(f)
        if not any(r["name"] == rule_id for r in rule_todo):
            await self.api.post_group_msg(msg.group_id, response("prompts", "rule_not_found"))
            return
        self.data["id"] += 1
        self.data.save()
        rid = self.data["id"]
        req = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=rid, task_type="DEEPSEEK")
        req.nickname = msg.sender.nickname
        request_map[rid] = req
        threading.Thread(target=self.thread_deepseek, daemon=True, args=(msg, command[:], req)).start()
        await self.api.post_group_msg(msg.group_id, response("task", "created").format(rid))

    async def _do_update(self, msg, command, is_group):
        target = msg.group_id if is_group else msg.user_id
        poster = self.api.post_group_msg if is_group else self.api.post_private_msg
        await poster(target, response("categories", "update_start"))
        timeout = int(command[1]) if len(command) > 1 and command[1].isdigit() else cfg("update_rules_timeout", default=20)
        ok = update_all_rules(timeout)
        await poster(target, response("categories", "update_end") if ok else response("categories", "update_fail"))

    async def _send_help(self, msg, is_group):
        try:
            with open(f"{SELF_PATH}/help.yaml", "r", encoding="utf-8") as f:
                help_text = yaml.full_load(f)
            if is_group:
                result = await self.send_group_forward_msg_text(help_text, msg)
                if result and result.get("status", "") != "ok":
                    await self.api.post_group_msg(msg.group_id, response("forward", "help_send_failed"))
                check_and_log(result)
            else:
                await self.send_private_forward_msg_text(help_text, msg)
        except Exception as e:
            _log.error(f"加载帮助文件失败: {e}")
            target = msg.group_id if is_group else msg.user_id
            poster = self.api.post_group_msg if is_group else self.api.post_private_msg
            await poster(target, response("forward", "help_unavailable"))

    async def _register(self, msg, command, raw_message):
        if len(command) > 2:
            rule_doc = raw_message.split(" ", 2)[-1]
            await self.register_rules(msg, command[1], rule_doc)
        elif len(command) == 2:
            await self.register_rules(msg, command[1], "")
        else:
            await self.api.post_group_msg(msg.group_id, response("rules", "register_fmt_error"))

    # ---------------- 权限命令 ----------------
    async def _require_admin(self, msg) -> bool:
        if not self.is_admin(msg.user_id):
            await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
            return False
        return True

    def _parse_target(self, msg, command):
        """解析被操作用户：优先数字参数，其次 at 段。返回 None 表示格式错误。"""
        if len(command) > 1 and command[1].isdigit():
            return int(command[1])
        if len(msg.message) > 1 and msg.message[1].get("type") == "at":
            return int(msg.message[1]["data"]["qq"])
        return None

    def _parse_level(self, msg, command) -> int:
        """解析等级参数（默认 2=admin）。数字参数在 command[2]，at 场景在 message[2]。"""
        raw = None
        if len(command) > 1 and command[1].isdigit() and len(command) > 2:
            raw = command[2]
        elif len(msg.message) > 2 and msg.message[2].get("type") == "text":
            raw = msg.message[2]["data"]["text"]
        if raw is None:
            return ADMIN
        raw = str(raw).strip()
        if raw in ("-1", "0", "1", "2"):
            return int(raw)
        # 兼容旧写法：名字
        return {"ban": BAN, "normal": NORMAL, "user": USER, "admin": ADMIN}.get(raw.lower(), ADMIN)

    async def _op(self, msg, command):
        """#op <@用户|QQ> <等级>

        等级：-1=ban, 0=普通, 1=user, 2=admin（默认 2）
        """
        if not await self._require_admin(msg):
            return
        target = self._parse_target(msg, command)
        if target is None:
            await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
            return
        if target == self.master_uid and self.level_of(msg.user_id) < ADMIN:
            await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
            return
        level = self._parse_level(msg, command)
        if level not in (BAN, NORMAL, USER, ADMIN):
            await self.api.post_group_msg(msg.group_id, response("command", "unknown_level"))
            return
        if target == self.master_uid and level < ADMIN:
            await self.api.post_group_msg(msg.group_id, response("command", "target_is_master"))
            return

        old = self.set_level(target, level)
        text = response("command", {
            BAN: "ban_done",
            NORMAL: "deop_done",
            USER: "user_done",
            ADMIN: "op_done",
        }[level])
        await self.api.post_group_msg(
            msg.group_id,
            f"{text}\n{target}: {level_name(old)}({old}) -> {level_name(level)}({level})",
        )

    async def _set_level_cmd(self, msg, command, level: int, done_key: str):
        """#ban / #unban / #deop 的共用实现。"""
        if not await self._require_admin(msg):
            return
        target = self._parse_target(msg, command)
        if target is None:
            await self.api.post_group_msg(msg.group_id, response("command", "cmd_fmt"))
            return
        if target == self.master_uid:
            await self.api.post_group_msg(msg.group_id, response("command", "target_is_master"))
            return
        old = self.level_of(target)
        if level == BAN and old == BAN:
            await self.send_message(msg, response("command", "target_is_ban"))
            return
        if level == NORMAL and old == NORMAL:
            await self.send_message(msg, response("command", "target_is_unban"))
            return
        if old >= USER and level < old and level <= NORMAL:
            # 仅允许降级到自己能管的范围之外不再额外限制
            pass
        self.set_level(target, level)
        await self.send_message(
            msg,
            f"{response('command', done_key)}\n{target}: {level_name(old)}({old}) -> {level_name(level)}({level})",
        )

    async def _dsmsg(self, msg, raw_message):
        if not self.is_user(msg.user_id):
            await self.api.post_group_msg(msg.group_id, response("command", "user_not_admin"))
            return
        if not any(r.task_type == "DEEPSEEK" for r in request_map.values()):
            await self.api.post_group_msg(msg.group_id, response("deepseek", "dsmsg_no_task"))
            return
        content = raw_message[len("#dsmsg"):].lstrip()
        if not content:
            await self.api.post_group_msg(msg.group_id, response("deepseek", "dsmsg_usage"))
            return
        try:
            prompt_dir = cfg("deepseek", "prompt_dir", default=r"D:\0.0\lib\my_python\dsBrowser\prompt")
            os.makedirs(prompt_dir, exist_ok=True)
            for fname in cfg("deepseek", "prompt_files", default=["main.txt", "test.txt"]):
                with open(os.path.join(prompt_dir, fname), "a", encoding="utf-8") as f:
                    f.write(content + "\n")
            await self.api.post_group_msg(msg.group_id, response("deepseek", "dsmsg_done"))
        except Exception as e:
            await self.api.post_group_msg(msg.group_id, response("deepseek", "dsmsg_failed").format(e))

    # ---------------- 综合指令 # ----------------
    async def shape(self, msg, command=None):
        if command is None:
            command = _raw_text(msg).split()[1:]
        if len(command) == 0:
            await self.state(msg)
        elif command[0].isdigit():
            if int(command[0]) < cfg("mine_runner", "simple_threshold", default=1000) and "/f" not in command:
                self.data["id"] += 1
                self.data.save()
                rid = self.data["id"]
                req = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=rid)
                req.nickname = msg.sender.nickname
                request_map[rid] = req
                threading.Thread(target=self.thread_target, daemon=True, args=(msg, ["#"] + command[:], req)).start()
                await self.send_message(msg, response("task", "created").format(rid))
            else:
                await self.query_thread(msg, [""] + command)
        else:
            await self.search_rule(msg, [""] + command)
