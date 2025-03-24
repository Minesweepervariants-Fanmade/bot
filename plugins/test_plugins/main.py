from pathlib import Path
import socket
import asyncio

from ncatbot.plugin import BasePlugin, CompatibleEnrollment, EventBus, Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log


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

_log = get_log()
bot = CompatibleEnrollment
SELF_PATH = Path(__file__).parent.__str__()
HOST_IP = get_host_ip()



class Test(BasePlugin):
    name = 'test'
    version = '0.0'

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        # 定义的回调函数
        print(msg)
        if msg.raw_message == "测试":
            await self.api.post_group_msg(msg.group_id, text="Ncatbot 插件测试成功喵")
            await self.api.post_group_file(msg.group_id, file=f"http://{HOST_IP}/{SELF_PATH}/test.txt")
