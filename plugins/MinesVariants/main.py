from pathlib import Path
import yaml

if __name__ == "__import__":
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
config_data = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))


async def rule_create(descri: str, post):
    def post_ollama(message=None, content="", assistant="") -> ChatResponse:
        if message is None:
            message = [
                {"role": "assistant", "content": assistant},
                {"role": "user", "content": content}
            ]
        return chat(model=config_data["model"], messages=message)
    await post("")
    response: ChatResponse = post_ollama(
        assistant="\n".join(config_data["params"]["check"]),
        content=descri
    )
    print(response.message.content)
    data = eval(response.message.content.rsplit("\"", 2)[1])
    print("rule check:", data)
    if not data:
        await post("未描述规则,请检查并重新键入")
        return
    else:
        await post("已通过规则检查")
    response: ChatResponse = post_ollama(
        assistant="\n".join(config_data["params"]["init_examp"]),
        content=descri
    )
    print(response.message.content)
    data = eval(response.message.content.rsplit("\"", 2)[1])
    print("data:", data)
    if not data:
        await post("请给出规则的示例内容")
        return
    else:
        await post("已获取到示例信息")



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
    123
    """
    rule_create(descri, print)


if __name__ == '__main__':
    main()
