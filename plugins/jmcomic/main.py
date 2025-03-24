import socket
import os
from pathlib import Path

from ncatbot.plugin import BasePlugin, CompatibleEnrollment, EventBus, Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log

import jmcomic


def get_host_ip():
    """
    查询本机ip地址
    :return: ip
    """
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

class JmComic:
    name = "jmcomic"
    version = "0.0.1"

    @bot.group_event()
    async def group(self, event: GroupMessage):
        print(event)
        if event.raw_message.startswith("/jm"):
            command = event.raw_message.split(" ")[1:]
            # jmid = command[0]
            # jmcomic.download_album(jmid, )

