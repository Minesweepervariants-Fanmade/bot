from pathlib import Path

import jmcomic as jm

SELF_PATH = Path(__file__).parent.__str__()

jmoption = jm.JmOption.construct({"dir_rule": {"base_dir": f"{SELF_PATH}\\download", "rule": "Bd_Pid"}})
jmoption.plugins["after_photo"] = [{"plugin": "img2pdf", "kwargs":{"pdf_dir": f"{SELF_PATH}\\download", "filename_rule": "Pid"}}]


if __name__ == '__main__':
    jm.download_album("11451", option=jmoption)
    print(jmoption)
