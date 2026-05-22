import socket
import threading


def server_listen():
    port = 31409
    host = "0.0.0.0"
    """启动一个同步TCP服务，接收连接并回复状态"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"事件总线监听于 {host}:{port}")

    while True:
        client, addr = server.accept()
        client.sendall(b'EventBus OK\n')  # 收到连接即回复
        client.close()


thread = threading.Thread(target=server_listen)
thread.daemon = True
thread.start()

import yaml
from ncatbot.core import BotClient
from ncatbot.utils.config import config
from ncatbot.utils.logger import get_log

_log = get_log()
botData = yaml.full_load(open("./data/data.yaml"))["bot"]

config.set_bot_uin(botData["qqid"])  # 设置 bot qq 号 (必填)
config.set_ws_uri(botData["url"])  # 设置 napcat websocket server 地址
config.set_token(botData["token"])  # 设置 token (napcat 服务器的 token)

bot = BotClient()

# EVENT_BUS = bot.plugin_sys.event_bus


if __name__ == "__main__":
    bot.run()
