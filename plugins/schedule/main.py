from pathlib import Path
import socket
import asyncio

from ncatbot.plugin import BasePlugin, CompatibleEnrollment, EventBus, Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log

_log = get_log()
bot = CompatibleEnrollment
SELF_PATH = Path(__file__).parent.__str__()
