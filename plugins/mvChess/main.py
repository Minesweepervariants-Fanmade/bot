import asyncio
from pathlib import Path
import base64

from .chess_main.mines_chess import MVChess, find_rule

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.utils.logger import get_log


SELF_PATH = Path(__file__).parent.__str__()

lock = asyncio.Lock()
_log = get_log()
bot = CompatibleEnrollment
download_json_path = f"{SELF_PATH}\\cache\\download.json"


class MVChessMain(BasePlugin):
    name = "MVChess"
    version = "0.1"

    rules = None
    board = None
    choose_list = None
    img_url = f"{SELF_PATH}\\chess_main\\"

    def img2base64(self, img_name):
        with open(self.img_url+img_name, "rb") as f:
            return "base64://"+base64.b64encode(f.read()).decode("utf-8")

    async def output(self, group_id):
        choose_str = f"rule: {self.rules if self.rules else 'None'}\n"
        for i in range(len(self.choose_list)):
            choose_str += str(i + 1) + ": " + str(self.choose_list[i]) + "\n"
        await self.api.post_group_msg(group_id, text=choose_str, image=self.img2base64("mines_game.png"))

    @bot.group_event()
    async def on_group_event(self, event: GroupMessage):
        if not event.raw_message.startswith("#mvc"):
            return
        msg = event.raw_message
        msg = msg.split(" ")[1:]
        if msg[0] == "over":
            if self.board is None:
                await self.api.post_group_msg(event.group_id, text="对局未开始")
                return
            self.board.over(self.board.Q)
            self.board = None
            await self.api.post_group_msg(event.group_id, text="对局结束",
                                          image=self.img2base64("mines_game_over.png"))
            return
        if msg[0] == "reout":
            await self.output(event.group_id)
            return
        if msg[0] == "start":
            if self.board is not None:
                await self.api.post_group_msg(event.group_id, "棋局已开启")
                return
            for rule in msg[1:]:
                if find_rule(rule) is None:
                    await self.api.post_group_msg(event.group_id, f"规则{rule}找不到")
                    return
                self.rules = msg[1:]
            self.board = MVChess(rules=msg[1:])
        if msg[0].isdecimal():
            index = int(msg[0]) - 1
            pos = msg[1]
            try:
                if self.board.game_round(self.choose_list[index], pos) == "over":
                    await self.api.post_group_msg(event.group_id, text="对局结束",
                                                  image=self.img2base64("mines_game_over.png"))
                    self.board = None
                    return
            except Exception as e:
                print(e)
                await self.api.post_group_msg(event.group_id, text="请检查输入内容")
                return
        if self.board is None:
            return
        self.choose_list = self.board.choice_clue()
        await self.output(event.group_id)
