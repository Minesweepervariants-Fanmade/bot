from pathlib import Path
import socket
import asyncio

from ncatbot.plugin import BasePlugin, CompatibleEnrollment, EventBus, Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log
from ncatbot.core.api import check_and_log

_log = get_log()
bot = CompatibleEnrollment
SELF_PATH = Path(__file__).parent.__str__()


class Test(BasePlugin):
    name = 'test'
    version = '0.0'

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        # 定义的回调函数
        if msg.raw_message == "#测试":
            path = "http://10.147.19.27\\D:\\0.0\\lib\\my_python\\Minesweeper_Variants\\output\\demo.png"
            await self.api.post_group_msg(msg.group_id, text="Ncatbot 插件测试成功喵")
            # await self.send_group_forward_msg_image(path, msg)
            # await self.send_group_forward_msg_text("path", msg)
            # await self.api.post_group_msg(msg.group_id, image=path)

    async def send_group_forward_msg_text(self, text, msg):
        content = [{"type": "text", "data": {"text": text, "name": "demo.png"}}]
        message = [{"type": "node", "data": {"user_id": "460535002", "nickname": "7pi", "content": content}}]
        params = {"group_id": msg.group_id, "message": message, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))

    async def send_group_forward_msg_image(self, path, msg):
        content = [{"type": "image", "data": {"file": path, "summary": "[答案]"}}]
        message = [{"type": "node", "data": {"user_id": "460535002", "nickname": "7pi", "content": content}}]
        params = {"group_id": msg.group_id, "message": message, "new": [{"text": "string"}]}
        return check_and_log(await self.api._http.post("/send_group_forward_msg", json=params))
