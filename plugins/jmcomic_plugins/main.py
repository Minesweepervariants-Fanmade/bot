import os
import asyncio
import shutil
import json
import socket
from pathlib import Path

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log
from ncatbot.core.api import check_and_log

import jmcomic as jm
from jmcomic.jm_exception import MissingAlbumPhotoException

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


SELF_PATH = Path(__file__).parent.__str__()
HOST_IP = get_host_ip()

lock = asyncio.Lock()
_log = get_log()
bot = CompatibleEnrollment
download_json_path = f"{SELF_PATH}\\cache\\download.json"

jmoption = jm.JmOption.construct({"dir_rule": {"base_dir": f"{SELF_PATH}\\cache", "rule": "Bd_Pid"}})
jmoption.plugins["after_photo"] = [{"plugin": "img2pdf", "kwargs":{"pdf_dir": f"{SELF_PATH}\\cache", "filename_rule": "Pid"}}]


class JmComicPlugin(BasePlugin):
    name = "jmcomic"
    version = "0.0.1.1"

    async def post_file(self, file, file_name, msg):
        message = [{"type": "file", "data": {"name": file_name, "file": file}}]
        if isinstance(msg, GroupMessage):
            params = {"group_id": msg.group_id, "message": message}
            return check_and_log(await self.api._http.post("/send_group_msg", json=params))
        elif isinstance(msg, PrivateMessage):
            params = {"user_id": msg.user_id, "message": message}
            return check_and_log(await self.api._http.post("/send_private_msg", json=params))
        else:
            _log.warning(f"unknown message type: {type(msg)}")
            return {"code": 0, "msg": f"unknown message type{type(msg)}"}

    async def download(self, msg: GroupMessage | PrivateMessage, jmid):
        def delete_pdf(_jmid):
            shutil.rmtree(f"{SELF_PATH}\\cache\\{_jmid}")
            os.remove(f"{SELF_PATH}\\cache\\{_jmid}.pdf")

        try:
            async with lock:
                print("download start")
                if isinstance(msg, GroupMessage):
                    await self.api.post_group_msg(msg.group_id, f"开始下载{jmid}")
                elif isinstance(msg, PrivateMessage):
                    await self.api.post_private_msg(msg.user_id, f"开始下载{jmid}")
                try:
                    jm.download_album(jmid, jmoption)
                except MissingAlbumPhotoException:
                    if isinstance(msg, GroupMessage):
                        await self.api.post_group_msg(msg.group_id, f"未找到{jmid}")
                    elif isinstance(msg, PrivateMessage):
                        await self.api.post_private_msg(msg.user_id, f"未找到{jmid}")
                    return
                file_url = f"http://{HOST_IP}/{SELF_PATH}\\cache\\{jmid}.pdf"
                print("start send pdf")
                await self.post_file(file_url, f"{jmid}.pdf", msg)
                print("end send pdf")
                delete_pdf(jmid)
                if os.path.exists(download_json_path):
                    with open(download_json_path, "r", encoding="utf-8") as f:
                        history_download = json.load(f)
                else:
                    history_download = {"max": 20}
                dirlist = os.listdir(f"{SELF_PATH}\\cache")
                jmid_cache = []
                for dirname in dirlist:
                    if not os.path.isdir(f"{SELF_PATH}\\cache\\{dirname}"):
                        continue
                    jmid_cache.append(dirname)
                max_id = -1
                for key in list(history_download.keys()):
                    if key == "max":
                        continue
                    if key not in jmid_cache:
                        del history_download[key]
                        continue
                    max_id = max(max_id, history_download[key])
                for _jmid in jmid_cache:
                    if _jmid not in history_download:
                        max_id += 1
                        history_download[_jmid] = max_id
                max_id = -1
                for key in sorted(history_download, key=lambda x: history_download[x]):
                    max_id += 1
                    history_download[key] = max_id
                history_max = history_download["max"]
                while max_id > history_max:
                    for _jmid in history_download:
                        if history_download[_jmid] == 0:
                            del history_download[_jmid]
                            delete_pdf(_jmid)
                        else:
                            history_download[_jmid] -= 1
                        max_id -= 1
                with open(download_json_path, "w", encoding="utf-8") as f:
                    json.dump(history_download, f, indent=4)
                print("done")
        except Exception as e:
            _log.error(e)


    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        print("jm", msg)
        if msg.raw_message.startswith("#jm"):
            command = msg.raw_message.split(" ")[1:]
            for jmid in command:
                await self.download(msg, jmid)

    @bot.private_event()
    async def on_private_event(self, msg: GroupMessage):
        print("jm", msg)
        if msg.raw_message.startswith("#jm"):
            command = msg.raw_message.split(" ")[1:]
            for jmid in command:
                await self.download(msg, jmid)
