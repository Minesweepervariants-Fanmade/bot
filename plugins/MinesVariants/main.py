import asyncio
from pathlib import Path

import yaml
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils import logger

try:
    import ollama
except ImportError as e:
    print("未安装Ollama 请在项目解释器下使用pip install ollama安装")
    raise e
from ollama import chat
from ollama import ChatResponse

SELF_PATH = Path(__file__).parent.__str__()

_log = logger.get_log()
bot = CompatibleEnrollment
download_json_path = f"{SELF_PATH}\\cache\\download.json"
config_data = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))


class MinesVariants(BasePlugin):
    name = "MinesVariants"
    version = "0.0.0"

    @staticmethod
    def post_ollama(message=None, assistant="", descri="") -> ChatResponse:
        if message is None:
            message = [
                {"role": "assistant", "content": assistant},
                {"role": "user", "content": descri}
            ]
        return chat(model=config_data["model"], messages=message)

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if msg.raw_message.startswith("#mv"):
            command = msg.raw_message.split(" ")[1:]
            if command[0] == "新建规则":
                for message in msg.message:
                    if message["type"] != "text":
                        await self.api.post_group_msg(msg.group_id, "无法识别非文字信息,请改用文字描述")
                        return
                await self.api.post_group_msg(msg.group_id, "开始尝试理解规则")
                descri = msg.raw_message.split(" ", 2)[2]
                response = self.post_ollama(
                    assistant="\n".join(config_data["params"]["check"]),
                    descri=descri
                )
                print(response.message.content)
                data = eval(response.message.content.rsplit("\"", 2)[1])
                print("rule check:", data)
                if not data:
                    await self.api.post_group_msg(msg.group_id, "未描述规则,请检查并重新键入")
                    return
                else:
                    await self.api.post_group_msg(msg.group_id, "已通过规则检查")
                response: ChatResponse = self.post_ollama(
                    assistant="\n".join(config_data["params"]["init_examp"]),
                    descri=descri
                )
                print(response.message.content)
                data = eval(response.message.content.rsplit("\"", 2)[1])
                print("data:", data)
                if not data:
                    await self.api.post_group_msg(msg.group_id, "请给出规则的示例内容")
                    return
                else:
                    await self.api.post_group_msg(msg.group_id, "已获取到示例信息")


def main():
    # ollama.chat
    print(config_data)


if __name__ == '__main__':
    main()
