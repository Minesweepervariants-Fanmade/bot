from pathlib import Path
from typing import Iterator

import yaml

try:
    import ollama
except ImportError as e:
    print("未安装Ollama 请在项目解释器下使用pip install ollama安装")
    raise e
from ollama import chat
from ollama import ChatResponse

SELF_PATH = Path(__file__).parent.__str__()

download_json_path = f"{SELF_PATH}\\cache\\download.json"
config_data: dict = yaml.full_load(open(f"{SELF_PATH}/data.yaml", "r", encoding="utf-8"))
config_data.update({"model": yaml.full_load(open(f"{SELF_PATH}/model.yaml", "r", encoding="utf-8"))})


def rule_create(descri: str, post):
    def examp_check(input_data) -> bool:
        if isinstance(input_data, list):
            for i in input_data:
                if not isinstance(i, list):
                    return False
                if len(i) != 4:
                    return False
                if not (isinstance(i[0], list) and isinstance(i[0][0], list)):
                    return False
                if not isinstance(i[1], tuple):
                    return False
                if not isinstance(i[2], str):
                    return False
                if not isinstance(i[3], bool):
                    return False
            return True
        else:
            return False

    def post_ollama(model="quickout", message=None, content="") -> ChatResponse:
        if message is None:
            message = [
                {"role": "user", "content": content}
            ]
        return chat(model=config_data["model"][model], messages=message)

    print("input model:", "\n".join(config_data["params"]["rule_check"]) + "{" + descri + "}")
    data = None
    for _ in range(10):     # 模型可能不稳定 需要重复输出找到其中一个输出
        response: ChatResponse = post_ollama(
            content="\n".join(config_data["params"]["rule_check"]) + "{" + descri + "}",
        )
        print("model output:", response.message.content)
        try:
            data = eval(response.message.content.rsplit("\"", 2)[1])
        except:
            continue
        if isinstance(data, bool) and data:
            break
    print("rule_check:", data)
    print("="*100)
    # for _ in range(10):     # 模型可能不稳定 需要重复输出找到其中一个输出
    #     response: ChatResponse = post_ollama(
    #         content="\n".join(config_data["params"]["check_examp"]) + "{" + descri + "}",
    #     )
    #     print("model output:", response.message.content)
    #     try:
    #         data = eval(response.message.content.rsplit("\"", 2)[1])
    #     except:
    #         continue
    #     if isinstance(data, bool) and data:
    #         break
    # print("examp_check:", data)
    # print("="*100)
    # print("input_model:", "\n".join(config_data["params"]["init_examp"]) + "{" + descri + "}")
    # t = 0
    # while 1:     # 模型可能不稳定 需要重复输出找到其中一个输出
    #     response: ChatResponse = post_ollama(
    #         model="deepthink",
    #         content="\n".join(config_data["params"]["init_examp"]) + "{" + descri + "}",
    #     )
    #     print("*"*20 + f"第{(t := t + 1)}次尝试" + "*"*20)
    #     print("model output:", response.message.content)
    #     try:
    #         data = eval(response.message.content.rsplit("\"", 2)[1])
    #     except:
    #         continue
    #     if examp_check(data):
    #         if not data:
    #             continue
    #         break
    # print("init_examp:", data)
    print("input_model:", "\n".join(config_data["params"]["init_code"]) + descri)
    response: Iterator[ChatResponse] = chat(
        model="deepthink",
        messages=[{"role": "user", "content": "\n".join(config_data["params"]["init_code"]) + descri}],
        stream=True
    )
    code_content = ""
    for chunk in response:
        print(code_content := code_content + chunk["message"]["contect"], end="", flush=True)
    code_content = code_content.rsplit("###", 2)[1]
    print("\n\n\n", code_content)



def main():
    # ollama.chat
    print(config_data)
    descri = """对于一个线索来说 该线索将表示周围八个格子的雷数量总和 F为雷 ?为非雷 例: 
? ? F
F 5 ?
F ? F 其中线索5是错误的
? ? F
F 3 ?
F ? F 其中线索3是错误的
? F F
F 7 F
F F F 其中线索7是错误的"""
    rule_create(descri, lambda s: print("post: " + s))


if __name__ == '__main__':
    main()
