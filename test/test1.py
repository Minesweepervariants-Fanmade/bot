import base64
import json

IMAGE_SPLIT = "hjiodfabwhgiuojtgfawnshiujedohawnojgltubawiojdn cawoujgtfwuojabdrfawoujsfghbwauojrbf nawo"
USER_ID = "2947571390"
NICK_NAME = "老婆"


def pck(content, user_id=USER_ID, nickname=NICK_NAME) -> list:
    if type(content) is str:
        image = ""
        if IMAGE_SPLIT in content:
            content, image_file_path = content.rsplit(IMAGE_SPLIT, 1)
            if image_file_path:
                with open(image_file_path, "rb") as f:
                    image = "base64://" + base64.b64encode(f.read()).decode('utf-8')
        content = [{"type": "text", "data": {"text": content}}]
        if image:
            content.append({"type": "image", "data": {"file": image}})
        _message = {"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": content}}
        return [_message]
    elif type(content) is list:
        _message = []
        for _text in content:
            _text = pck(_text)
            _message.extend(_text)
        _message = {"type": "node", "data": {"user_id": user_id, "nickname": nickname, "content": _message}}
        return [_message]
    elif type(content) is dict:
        uid = content.get("uid", USER_ID)
        name = content.get("name", NICK_NAME)
        content = content["content"]
        __result = pck(content, user_id=uid, nickname=name)
        return __result
    else:
        return []

"\"app\":\"com.tencent.multimsg\",\"config\":{\"autosize\":1,\"forward\":1,\"round\":1,\"type\":\"normal\",\"width\":300},\"desc\":\"[聊天记录]\",\"extra\":{\"filename\":\"f01ea15e-f8d3-446e-944a-32950f135c76\",\"tsum\":7},\"meta\":{\"detail\":{\"news\":[{\"text\":\"老婆: [卡片消息]\"},{\"text\":\"老婆: [卡片消息]\"},{\"text\":\"老婆: [卡片消息]\"},{\"text\":\"老婆: 待办规则\"},{\"text\":\"老婆: [卡片消息]\"},{\"text\":\"老婆: [卡片消息]\"},{\"text\":\"老婆: [卡片消息]\"}],\"resid\":\"8k8NIvB21bmugJl3uOpP/W/pW15AXhigFn3dSfIYUrCXvxd45EGJeDvXfhAXL+OD\",\"source\":\"群聊的聊天记录\",\"summary\":\"查看7条转发消息\",\"uniseq\":\"f01ea15e-f8d3-446e-944a-32950f135c76\"}},\"prompt\":\"[聊天记录]\",\"ver\":\"0.0.0.5\",\"view\":\"contact\"}"

pck_msg = pck([{"uid": 3140864122, "name": "456", "content": "123"}, [{"uid": 3140864122, "name": "456", "content": "789"}]])
print(pck_msg)
msg = {"group_id": 1051027867, "message": pck_msg[0]["data"]["content"]}
print(json.dumps(msg, ensure_ascii=False).replace("\"", "\"\""))
print(json.dumps(msg, ensure_ascii=False, indent=4))
