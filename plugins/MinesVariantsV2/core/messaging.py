"""消息组装与发送：文本/图片/合并转发。"""
import base64
import os

from ncatbot.core.api import check_and_log

from .config import USER_ID, NICK_NAME, response
from .schema import ApiResult, Msg, MsgNode
from .utils import HOST_IP


def pck(
    content: str | list | dict,
    image: str = "",
    user_id: str = USER_ID,
    nickname: str = NICK_NAME,
) -> list[MsgNode]:
    """把文本/列表/字典内容打包成合并转发节点。"""
    if isinstance(content, str):
        return _pck_text(content, image, user_id, nickname)
    if isinstance(content, list):
        return _pck_list(content, user_id, nickname)
    if isinstance(content, dict):
        return _pck_dict(content)
    return []


def _pck_text(text: str, image: str, user_id: str, nickname: str) -> list[MsgNode]:
    """打包单个文本节点。"""
    elems: list[dict] = [{"type": "text", "data": {"text": text}}]
    if image and os.path.exists(image):
        with open(image, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        elems.append({"type": "image", "data": {"file": "base64://" + b64}})
    node = {
        "type": "node",
        "data": {"user_id": user_id, "nickname": nickname, "content": elems},
    }
    return [node]


def _pck_list(items: list, user_id: str, nickname: str) -> list[MsgNode]:
    """递归打包文本列表。"""
    elems: list = []
    for item in items:
        elems.extend(pck(item))
    node = {
        "type": "node",
        "data": {"user_id": user_id, "nickname": nickname, "content": elems},
    }
    return [node]


def _pck_dict(item: dict) -> list[MsgNode]:
    """打包带自定义 uid/nickname/image 的字典。"""
    uid = item.get("uid", USER_ID)
    name = item.get("name", NICK_NAME)
    image = item.get("image", "")
    return pck(item["content"], image=image, user_id=uid, nickname=name)


class MessagingMixin:
    """依赖 self.api 的发送辅助方法。"""

    async def send_message(
        self,
        msg: Msg,
        message: str,
        reply: int | str | None = None,
        image_path: str | None = None,
    ) -> None:
        image = None
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image = "base64://" + base64.b64encode(f.read()).decode("utf-8")
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, message, reply=reply, image=image)
        else:
            await self.api.post_private_msg(msg.user_id, message, reply=reply, image=image)

    async def send_private_forward_msg_text(
        self,
        text: str | list[str],
        msg: Msg,
        news: list | None = None,
        source: str | None = None,
        summary: str | None = None,
    ) -> ApiResult | None:
        if isinstance(text, str):
            text = [text]
        message = pck(text)[0]["data"]["content"]
        if not message:
            return None
        params = {"user_id": msg.user_id, "message": message}
        if news is not None:
            params["news"] = news
        if source is not None:
            params["source"] = source
        if summary is not None:
            params["summary"] = summary
        return check_and_log(await self.api._http.post("/send_private_forward_msg", json=params))

    async def send_group_forward_msg_text(
        self,
        text: str | list[str],
        msg: Msg,
        news: list | None = None,
        source: str | None = None,
        summary: str | None = None,
    ) -> ApiResult | None:
        if isinstance(text, str):
            text = [text]
        message = pck(text)[0]["data"]["content"]
        if not message:
            return None
        params = {"group_id": msg.group_id, "message": message}
        if news is not None:
            params["news"] = news
        if source is not None:
            params["source"] = source
        if summary is not None:
            params["summary"] = summary
        return await self.api._http.post("/send_group_forward_msg", json=params)

    @staticmethod
    def _to_url(path: str) -> str:
        if path.startswith("base64://"):
            return path
        return f"http://{HOST_IP}/" + path.replace("\\", "/").lstrip("/")

    async def send_group_forward_msg_image(
        self, path: str | list[str], msg: Msg, summary: str | None = None
    ) -> ApiResult | None:
        paths = [path] if isinstance(path, str) else list(path)
        if not paths:
            return None
        messages = []
        for p in paths:
            node = {
                "type": "node",
                "data": {
                    "user_id": response("users", "default_bot", "id"),
                    "nickname": response("users", "default_bot", "nickname"),
                    "content": [{"type": "image", "data": {"file": self._to_url(p)}}],
                },
            }
            if summary:
                node["data"]["content"][0]["data"]["summary"] = summary
            messages.append(node)
        params = {"group_id": msg.group_id, "messages": messages}
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))

    async def send_private_forward_msg_image(
        self, path: str | list[str], msg: Msg, summary: str | None = None
    ) -> ApiResult | None:
        paths = [path] if isinstance(path, str) else list(path)
        if not paths:
            return None
        messages = []
        for p in paths:
            node = {
                "type": "node",
                "data": {
                    "user_id": response("users", "default_bot", "id"),
                    "nickname": response("users", "default_bot", "nickname"),
                    "content": [{"type": "image", "data": {"file": self._to_url(p)}}],
                },
            }
            if summary:
                node["data"]["content"][0]["data"]["summary"] = summary
            messages.append(node)
        params = {"user_id": msg.user_id, "messages": messages, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_private_forward_msg", json=params))
