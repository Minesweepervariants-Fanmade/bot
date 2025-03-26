from pathlib import Path
import socket
import asyncio

from ncatbot.plugin import BasePlugin, CompatibleEnrollment, EventBus, Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log

_log = get_log()
bot = CompatibleEnrollment
SELF_PATH = Path(__file__).parent.__str__()


class Test(BasePlugin):
    name = 'test'
    version = '0.0'

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        # 定义的回调函数
        print("test", msg)
        if msg.raw_message == "测试":
            await self.api.post_group_msg(msg.group_id, text="Ncatbot 插件测试成功喵")

    @bot.private_event()
    async def on_private_event(self, msg: PrivateMessage):
        print("test", msg)