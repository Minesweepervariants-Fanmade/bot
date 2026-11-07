"""轻量 i18n：按语言从 yaml 读取文案，支持点路径 key 与列表随机取一条。

用法:
    from ..i18n import t
    t("git.sync_failed")
"""
import random
import threading
from pathlib import Path

import yaml

_I18N_DIR = Path(__file__).resolve().parent
_lock = threading.Lock()
_cache: dict = {}

_default_locale = "zh_CN"
_current_locale = _default_locale


def set_locale(name: str) -> None:
    global _current_locale
    _current_locale = name


def get_locale() -> str:
    return _current_locale


def reload_locale(name: str = None) -> None:
    name = name or _current_locale
    with _lock:
        _cache.pop(name, None)


def _load(locale: str) -> dict:
    path = _I18N_DIR / f"{locale}.yaml"
    if not path.exists():
        path = _I18N_DIR / f"{_default_locale}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.full_load(f) or {}


def _get_data(locale: str) -> dict:
    data = _cache.get(locale)
    if data is None:
        with _lock:
            data = _cache.get(locale)
            if data is None:
                data = _load(locale)
                _cache[locale] = data
    return data


def t(key: str, default: str = "") -> str:
    """按点路径取一条文案；结果为列表时随机取一条；缺失返回 default。"""
    node = _get_data(_current_locale)
    for part in key.split("."):
        if not isinstance(node, dict) or part not in node:
            return default if default else key
        node = node[part]
    if isinstance(node, list):
        node = random.choice(node) if node else default
    if not isinstance(node, str):
        return str(node)
    return node
