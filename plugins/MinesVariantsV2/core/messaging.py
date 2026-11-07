"""消息组装与发送：文本/图片/合并转发。"""
import base64
import os

from ncatbot.core.api import check_and_log

from .config import USER_ID, NICK_NAME, response
from .utils import HOST_IP


def pck(content, image="", user_id=USER_ID, nickname=NICK_NAME) -> list:
    """把文本/列表/字典内容打包成合并转发节点。"""
    if isinstance(content, str):
        msg = [{"type": "text", "data": {"text": content}}]
        if image and os.path.exists(image):
            with open(image, "rb") as f:
                image_data = "base64://" + base64.b64encode(f.read()).decode("utf-8")
            msg.append({"type": "image", "data": {"file": image_data}})
        return [{"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": msg}}]
    if isinstance(content, list):
        nodes = []
        for _text in content:
            nodes.extend(pck(_text))
        return [{"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": nodes}}]
    if isinstance(content, dict):
        uid = content.get("uid", USER_ID)
        name = content.get("name", NICK_NAME)
        image = content.get("image", "")
        return pck(content["content"], image=image, user_id=uid, nickname=name)
    return []


class MessagingMixin:
    """依赖 self.api 的发送辅助方法。"""

    async def send_message(self, msg, message: str, reply=None, image_path=None):
        image = None
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image = "base64://" + base64.b64encode(f.read()).decode("utf-8")
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, message, reply=reply, image=image)
        else:
            await self.api.post_private_msg(msg.user_id, message, reply=reply, image=image)

    async def send_private_forward_msg_text(self, text, msg, news=None, source=None, summary=None):
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

    async def send_group_forward_msg_text(self, text, msg, news=None, source=None, summary=None):
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

    async def send_group_forward_msg_image(self, path, msg, summary=None):
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

    async def send_private_forward_msg_image(self, path, msg, summary=None):
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
