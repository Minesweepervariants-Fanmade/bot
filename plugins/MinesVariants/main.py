from pathlib import Path
import yaml

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage
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
config_data: dict = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))
config_data.update({"model": yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))})


async def rule_create(descri: str, post):
    def post_ollama(model="quickout", message=None, content="") -> ChatResponse:
        if message is None:
            message = [
                {"role": "user", "content": content}
            ]
        return chat(model=config_data["model"][model], messages=message)
    response: ChatResponse = post_ollama(
        content="\n".join(config_data["params"]["check"]) + "{" + descri + "}",
    )
    print(response.message.content)
    data = eval(response.message.content.rsplit("\"", 2)[1])
    print("rule check:", data)


class MinesVariants(BasePlugin):
    name = "MinesVariants"
    version = "0.0.0"

    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        async def post(content):
            await self.api.post_group_msg(msg.group_id, content)
        if msg.raw_message.startswith("#mv"):
            command = msg.raw_message.split(" ")[1:]
            if command[0] == "新建规则":
                for message in msg.message:
                    if message["type"] != "text":
                        await self.api.post_group_msg(msg.group_id, "无法识别非文字信息,请改用文字描述")
                        return
                return rule_create(descri=command[1], post=post)


def main():
    # ollama.chat
    print(config_data)
    descri = """
对于一个线索来说 该线索将表示周围八个格子的雷数量总和 F为雷 ?为非雷 例: 
? ? ?
F 3 ?
F ? F 其中线索3是正确的
    """
    rule_create(descri, print)


if __name__ == '__main__':
    main()
