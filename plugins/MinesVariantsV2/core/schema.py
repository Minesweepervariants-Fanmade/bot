"""集中定义配置与持久化数据的类型结构（TypedDict + Protocol）。

TypedDict 在运行时零开销，仅用于类型检查与 IDE 补全。
"""
from typing import Any, Literal, Protocol, TypedDict, Union

from ncatbot.core.api import BotAPI
from ncatbot.core.message import GroupMessage, PrivateMessage

TaskType = Literal["MINES", "DEEPSEEK"]

# 消息对象（群聊/私聊的统一别名）
Msg = Union[GroupMessage, PrivateMessage]

# ncatbot API 返回的原始 JSON
class ApiResult(TypedDict, total=False):
    status: str
    retcode: int
    message: str
    data: dict
    code: int
    msg: str

# ---------------------------------------------------------------------------
# 消息节点
# ---------------------------------------------------------------------------
class TextData(TypedDict):
    text: str


class ImageData(TypedDict):
    file: str


class TextElem(TypedDict):
    type: str
    data: TextData


class ImageElem(TypedDict):
    type: str
    data: ImageData


class NodeData(TypedDict, total=False):
    user_id: str
    nickname: str
    content: list


class MsgNode(TypedDict):
    type: str
    data: NodeData


# ---------------------------------------------------------------------------
# 配置结构（对应 data.yaml，允许缺省任意项，由 config.DEFAULTS 兜底）
# ---------------------------------------------------------------------------
class SocketCfg(TypedDict, total=False):
    host: str
    port: int
    recv_size: int


class MineRunnerCfg(TypedDict, total=False):
    max_buffer: int
    log_tail_bytes: int
    error_msg_length: int
    error_str_length: int
    error_tail_lines: int
    simple_threshold: int


class ForwardCfg(TypedDict, total=False):
    max_length: int
    chunk_max_length: int


class QueryCfg(TypedDict, total=False):
    log_tail_bytes: int
    default_str_length: int
    max_chunks: int
    str_budget: int
    force_stdout_chars: int


class HintCfg(TypedDict, total=False):
    log_tail_bytes: int
    error_msg_length: int
    error_str_length: int
    error_tail_lines: int
    download_timeout: int
    download_chunk: int


class DeepseekCfg(TypedDict, total=False):
    log_path: str
    work_dir: str
    prompt_dir: str
    stop_bat: str
    save_rule_bat: str
    run_bat: str
    main_log: str
    test_log: str
    prompt_files: list[str]


class HttpCfg(TypedDict, total=False):
    user_agent: str
    timeout: int


class ConfigData(TypedDict, total=False):
    # 路径
    out_path: str
    log_path: str
    image_path: str
    porject_path: str  # 历史拼写
    project_path: str  # 优先
    # 运行
    interval: float
    locale: str
    master_uid: int
    thread_join_timeout: float
    host_ip_probe: list[str]
    # 嵌套
    socket: SocketCfg
    mine_runner: MineRunnerCfg
    forward: ForwardCfg
    query: QueryCfg
    hint: HintCfg
    http: HttpCfg
    deepseek: DeepseekCfg
    update_rules_retries: int
    deepseek_log_path: str  # 兼容旧键
    # 其它
    regex_timeout: float
    update_rules_timeout: int


# ---------------------------------------------------------------------------
# 持久化数据结构（data/<plugin>/<plugin>.json）
# ---------------------------------------------------------------------------
# 权限等级：-1=ban 0=普通 1=user 2=admin
LevelMap = dict[str, int]


class PluginData(TypedDict, total=False):
    id: int
    levels: LevelMap
    last_remote_hash_doc: str
    # 旧版字段（迁移来源，保留以防回滚）
    admin: list[int]
    user: list[int]
    ban: list[int]
    # deepseek / 其它历史字段
    model: str
    params: dict
    config: dict
    shape: bool


class DataStore(Protocol):
    """UniversalLoader 的结构化子集，供类型检查使用。"""

    def get(self, key: str, default: Any = None) -> Any: ...

    def __getitem__(self, key: str) -> Any: ...

    def __setitem__(self, key: str, value: Any) -> None: ...

    def save(self, *args: Any, **kwargs: Any) -> Any: ...


class HasApi(Protocol):
    """需要 self.api 的 mixin 的结构约束。"""

    api: BotAPI


class HasData(Protocol):
    """需要 self.data 的 mixin 的结构约束。"""

    data: DataStore
