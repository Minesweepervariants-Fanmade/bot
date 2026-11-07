"""全局配置：data.yaml + 内置默认值（深度合并），并包装 i18n。

用法:
    from .core.config import cfg, config_data, project_path
    cfg("socket", "port")            # 点路径读取，缺失返回 None
    cfg("forward", "max_length", default=7000)
    config_data["out_path"]          # 仍然兼容旧的字典式访问
"""
import asyncio
from pathlib import Path

import yaml
from ncatbot.utils import logger

from ..i18n import set_locale as _set_locale
from ..i18n import t as _t

# 插件根目录（core/ 的上一级）
SELF_PATH: str = Path(__file__).resolve().parent.parent.__str__()

_log = logger.get_log()

# ---------------------------------------------------------------------------
# 内置默认值：data.yaml 中缺失的键会自动回退到这里，保证旧配置可直接运行
# ---------------------------------------------------------------------------
DEFAULTS = {
    # 路径
    "out_path": r"D:\MinesweeperVariants\output",
    "log_path": r"D:\MinesweeperVariants\log",
    "image_path": r"D:\MinesweeperVariants\minesweepervariants\impl\rule\image",
    "porject_path": r"D:\MinesweeperVariants",  # 保留历史拼写
    # 运行
    "interval": 0.5,
    "locale": "zh_CN",
    "master_uid": 3140864122,
    "thread_join_timeout": 1.0,
    # 任务连接
    "socket": {"host": "localhost", "port": 31408, "recv_size": 4096},
    # 生成任务
    "mine_runner": {
        "max_buffer": 50,
        "log_tail_bytes": 4096,
        "error_msg_length": 9,
        "error_str_length": 1000,
        "error_tail_lines": 50,
        "simple_threshold": 1000,
    },
    # 合并转发
    "forward": {"max_length": 7000, "chunk_max_length": 100},
    # 查询
    "query": {
        "log_tail_bytes": 16384,
        "default_str_length": 2000,
        "max_chunks": 100,
        "str_budget": 12000,
        "force_stdout_chars": 5000,
    },
    # 提示
    "hint": {
        "log_tail_bytes": 4096,
        "error_msg_length": 9,
        "error_str_length": 1000,
        "error_tail_lines": 250,
        "download_timeout": 30,
        "download_chunk": 8192,
    },
    # 其它
    "regex_timeout": 0.2,
    "update_rules_timeout": 20,
    "deepseek": {
        "log_path": r"D:\0.0\lib\my_python\dsBrowser",
        "work_dir": r"D:\0.0\lib\ds-browser",
        "prompt_dir": r"D:\0.0\lib\my_python\dsBrowser\prompt",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """递归合并，override 优先。"""
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_config(path: str) -> dict:
    data = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.full_load(f) or {}
    except FileNotFoundError:
        _log.warning(f"未找到配置文件 {path}，使用内置默认值")
    except Exception as e:
        _log.warning(f"读取配置文件失败 {path}: {e}，使用内置默认值")
    if not isinstance(data, dict):
        _log.warning("data.yaml 顶层不是字典，忽略其内容")
        data = {}
    return _deep_merge(DEFAULTS, data)


config_data: dict = _load_config(f"{SELF_PATH}/data.yaml")

# 兼容旧代码里的 config_data["deepseek_log_path"]
config_data.setdefault("deepseek_log_path", config_data["deepseek"]["log_path"])

# 应用语言设置
_set_locale(str(config_data.get("locale") or "zh_CN"))


def cfg(*keys, default=None):
    """按点路径读取配置；缺失返回 default。"""
    node = config_data
    for k in keys:
        if isinstance(node, dict) and k in node:
            node = node[k]
        else:
            return default
    return node


def project_path() -> str:
    """项目根目录，优先 project_path，其次历史拼写 porject_path。"""
    return config_data.get("project_path") or config_data.get("porject_path")


def response(*key: str) -> str:
    """按层级 key 从 i18n 取一条文案（列表则随机取一条）。"""
    return _t(".".join(key))


NICK_NAME = response("users", "default_bot", "nickname")
USER_ID = response("users", "default_bot", "id")

# 合并转发分块参数
MAX_LENGTH = cfg("forward", "max_length", default=7000)
CHUNK_MAX_LENGTH = cfg("forward", "chunk_max_length", default=100)

# 规则注册互斥锁
REG_LOCK = asyncio.Lock()

# 运行中的任务表：request_id -> Request
request_map: dict = {}
