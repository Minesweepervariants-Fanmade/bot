"""提示（hint）功能：从回复图片 OCR 或历史日志重算提示图。"""
import asyncio
import base64
import os
import threading
from pathlib import Path

import requests

from .config import config_data, response, request_map, _log, cfg
from .utils import wait_for_pid
from .request import Request


def _read_log_tail(log_path: str, size: int = None) -> str:
    if size is None:
        size = cfg("hint", "log_tail_bytes", default=4096)
    if not os.path.exists(log_path):
        return "[EMPTY]"
    with open(log_path, "rb") as f:
        f.seek(max(0, os.path.getsize(log_path) - size))
        return f.read().decode("utf-8", errors="replace")


def _collect_images(text: str) -> list:
    images = []
    for line in text.splitlines():
        line = line.strip()
        if "Image saved to:" in line:
            images.append(line.split("Image saved to:", 1)[1].strip())
    return images


def _download_image(url: str, dest: str) -> None:
    """同步下载图片到本地（供 asyncio.to_thread 调用）。"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    resp = requests.get(
        url, headers=headers, stream=True,
        timeout=cfg("hint", "download_timeout", default=30),
    )
    resp.raise_for_status()
    chunk_size = cfg("hint", "download_chunk", default=8192)
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)


def _images_to_base64(images: list) -> list:
    out = []
    for path in images:
        with open(path, "rb") as f:
            out.append("base64://" + base64.b64encode(f.read()).decode("utf-8"))
    return out


def _img_sort_key(p: str) -> int:
    try:
        return int(p.split("_")[-1].split(".")[0])
    except (IndexError, ValueError):
        return 0


def _run_coro_in_thread(coro_factory):
    def runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro_factory())
        finally:
            loop.close()

    threading.Thread(target=runner, daemon=True).start()


class HintsMixin:
    async def _send_fail_output(self, msg, result_lines, request_id):
        str_length = cfg("hint", "error_str_length", default=1000)
        msg_length = cfg("hint", "error_msg_length", default=9)
        err_result = [result_lines[i:i + str_length] for i in range(0, len(result_lines), str_length)][-msg_length:]
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, response("task", "failed").format(request_id), reply=msg.message_id)
            resp = await self.send_group_forward_msg_text(err_result, msg, source=response("categories", "terminal_output"))
            if resp and resp.get("status", "") != "ok":
                await self.api.post_group_msg(msg.group_id, response("forward", "output_failed"))
        else:
            await self.api.post_private_msg(msg.user_id, response("task", "failed").format(request_id), reply=msg.message_id)
            resp = await self.send_private_forward_msg_text(err_result, msg, source=response("categories", "terminal_output"))
            if resp and resp.get("status", "") != "ok":
                await self.api.post_private_msg(msg.user_id, response("forward", "output_failed"))

    async def _send_images(self, msg, base64_contents):
        _log.info(f"hint: 共{len(base64_contents)}份图片待发送")
        if hasattr(msg, "group_id"):
            await self.send_group_forward_msg_image(base64_contents, msg, summary=None)
        else:
            await self.send_private_forward_msg_image(base64_contents, msg, summary=None)

    async def get_hint(self, msg, hint_id: str = None):
        raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
        command = raw_message.split()
        ocr_path = ""
        request_id = -1

        if msg.message[0]["type"] == "reply":
            reply_msg = await self.api.get_msg(msg.message[0]["data"]["id"])
            for part in reply_msg["data"]["message"]:
                if part["type"] != "image":
                    continue
                self.data["id"] += 1
                request_id = self.data["id"]
                img_url = part["data"]["url"]
                ocr_path = os.path.join(config_data["out_path"], f"ocr{request_id}.png")
                try:
                    await asyncio.to_thread(
                        _download_image, img_url, ocr_path
                    )
                    _log.info(f"图片被保存至{ocr_path}")
                except requests.exceptions.RequestException:
                    _log.warning(f"图片{img_url}下载失败")
                    ocr_path = ""
                break

        if not ocr_path:
            await self._get_hint_from_log(msg, hint_id=hint_id)
            return

        log_path = os.path.join(config_data["log_path"], f"{request_id}.log")

        async def _hint_by_board(board_code: str):
            args = f"hint -b {board_code} -F {request_id} -m PUZZLE " + " ".join(command[1:])
            request = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=request_id)
            request_map[request_id] = request
            request.data = response("hint", "state_calculating")
            request.run_task(args, mode="LINE")
            await wait_for_pid(request)
            request.wait_completion()

            log_text = ""
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    log_text = f.read()
            images_path = sorted(_collect_images(request.get_output() + log_text), key=_img_sort_key)
            base64_contents = _images_to_base64(images_path) if images_path else []

            if request_map.pop(request_id, None) is None:
                for p in images_path:
                    Path(p).unlink(missing_ok=True)
                return

            if not images_path:
                tail = "\n".join(request.get_output().split("\n")[-cfg("hint", "error_tail_lines", default=250):])
                await self._send_fail_output(msg, log_text + "\n" + tail, request.request_id)
                request.close_connection()
                return

            await self._send_images(msg, base64_contents)
            request.close_connection()
            for p in images_path:
                Path(p).unlink(missing_ok=True)

        async def get_ocr():
            request = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=request_id)
            request_map[request_id] = request
            args = f"ocr -i {ocr_path} -f {request_id} " + " ".join(command[1:])
            request.data = response("hint", "state_ocr")
            request.run_task(args, mode="LINE")
            await wait_for_pid(request)

            await self.send_message(msg, response("hint", "start_calc").format(request_id))
            request.wait_completion()
            Path(ocr_path).unlink(missing_ok=True)
            if request_map.pop(request_id, None) is None:
                return

            log_text = _read_log_tail(log_path)
            result = request.get_output()
            if "Exit Code: 0" not in result:
                tail = "\n".join(result.split("\n")[-cfg("mine_runner", "error_tail_lines", default=50):])
                await self._send_fail_output(msg, log_text + "\n\n" + tail, request.request_id)
                return

            board_code = ""
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if "|[BOARD]: " in line:
                        board_code = line.split("|[BOARD]: ", 1)[1].split("|", 1)[0]
                        break
            if not board_code:
                await self.send_message(msg, response("prompts", "log_unfind_error"))
                return
            await _hint_by_board(board_code)

        _run_coro_in_thread(get_ocr)

    async def _get_hint_from_log(self, msg, hint_id: str = None):
        if not hint_id:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, response("prompts", "log_format_error"))
            else:
                await self.api.post_private_msg(msg.user_id, response("prompts", "log_format_error"))
            return
        raw_message = "".join(i["data"]["text"] for i in msg.message if i["type"] == "text").strip()
        command = raw_message.split()
        if len(command) < 2:
            await self.send_message(msg, response("prompts", "log_format_error"))
            return
        if not hint_id.isdigit():
            await self.send_message(msg, response("prompts", "log_id_format_error"))
            return

        more_arg = raw_message.split(maxsplit=2)[-1]
        more_arg = "" if more_arg == hint_id else more_arg
        hint_id = int(hint_id)
        target_log_path = os.path.join(config_data["log_path"], f"{hint_id}.log")
        if not os.path.exists(target_log_path):
            await self.send_message(msg, response("prompts", "log_unfind_error"))
            return

        try:
            import ast
            with open(target_log_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            rule_list, used_r, board_code, answer_code, total = [], False, "", "", -1
            for line in lines:
                if "RULE" in line and not rule_list:
                    rule_list = list(ast.literal_eval(line.split("RULE:", 1)[1].split("EARLY_RULE:[", 1)[0]))
                elif "[USED_R]" in line:
                    used_r = ast.literal_eval(line.split("[USED_R]:", 1)[1].strip())
                elif "|[BOARD]: " in line and not board_code:
                    board_code = line.split("|[BOARD]: ", 1)[1].split("|", 1)[0]
                elif "|[ANSWER_BOARD]: " in line and not answer_code:
                    answer_code = line.split("|[ANSWER_BOARD]: ", 1)[1].split("|", 1)[0]
                elif "[TOTAL]" in line:
                    total = ast.literal_eval(line.split("[TOTAL]:", 1)[1].split("|", 1)[0])
            rule_str = " ".join(rule_list)
        except Exception as e:
            _log.error(f"解析历史日志失败: {e}")
            await self.send_message(msg, response("prompts", "log_unfind_error"))
            return

        if not board_code:
            await self.send_message(msg, response("prompts", "log_unfind_error"))
            return

        async def get_hint():
            self.data["id"] += 1
            self.data.save()
            request_id = self.data["id"]
            file_name = str(request_id)
            request = Request(max_length=cfg("mine_runner", "max_buffer", default=50), _request_id=request_id)
            request.nickname = msg.sender.nickname
            request_map[request_id] = request

            args = (
                f"hint -b {board_code} -a {answer_code} -c {rule_str} -F {file_name} -m PUZZLE "
                + (f"-r -t {total} " if used_r else "")
                + more_arg
            )
            request.run_task(args, mode="LINE")
            await wait_for_pid(request)
            request.data = response("hint", "board_label").format(hint_id)
            await self.send_message(msg, response("hint", "start_calc").format(request_id))
            request.wait_completion()

            log_path = os.path.join(config_data["log_path"], file_name + ".log")
            log_text = ""
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    log_text = f.read()
            images_path = sorted(_collect_images(request.get_output() + log_text), key=_img_sort_key)
            base64_contents = _images_to_base64(images_path) if images_path else []

            if request_map.pop(request_id, None) is None:
                for p in images_path:
                    Path(p).unlink(missing_ok=True)
                return

            if not images_path:
                tail = "\n".join(request.get_output().split("\n")[-cfg("hint", "error_tail_lines", default=250):])
                await self._send_fail_output(msg, tail, request.request_id)
                request.close_connection()
                return

            request.data = response("hint", "state_sending").format(len(base64_contents))
            await self._send_images(msg, base64_contents)
            request.close_connection()
            for p in images_path:
                Path(p).unlink(missing_ok=True)

        _run_coro_in_thread(get_hint)
