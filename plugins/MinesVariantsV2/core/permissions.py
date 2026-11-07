"""统一权限等级模型。

等级定义：
    -1  ban（拉黑，忽略其所有消息）
     0  普通用户
     1  user（操作员）
     2  admin（管理员）

存储：self.data["levels"] = { "<uid>": <int> }
首次加载时从旧版 admin/user/ban 三个列表迁移。
"""

BAN = -1
NORMAL = 0
USER = 1
ADMIN = 2

MASTER_UID = 3140864122  # 默认值，实际以 data.yaml 的 master_uid 为准

_LEVEL_NAMES = {BAN: "ban", NORMAL: "normal", USER: "user", ADMIN: "admin"}


def level_name(level: int) -> str:
    return _LEVEL_NAMES.get(level, str(level))


class PermissionsMixin:
    """依赖 self.data（UniversalLoader）的等级读写方法。"""

    @property
    def master_uid(self) -> int:
        """最高权限 UID，可由 data.yaml 的 master_uid 覆盖。"""
        from .config import cfg
        try:
            return int(cfg("master_uid", default=MASTER_UID))
        except (TypeError, ValueError):
            return MASTER_UID

    def init_levels(self):
        """首次加载时初始化 levels，并从旧版三列表迁移。"""
        if self.data.get("levels") is not None:
            # 确保 master 永远是 admin
            self.data["levels"][str(self.master_uid)] = ADMIN
            return

        levels = {}
        for uid in self.data.get("ban") or []:
            levels[str(uid)] = BAN
        for uid in self.data.get("user") or []:
            levels[str(uid)] = USER
        for uid in self.data.get("admin") or []:
            levels[str(uid)] = ADMIN
        levels[str(self.master_uid)] = ADMIN
        self.data["levels"] = levels

    def level_of(self, user_id) -> int:
        """取某用户等级，未记录视为普通用户。"""
        levels = self.data.get("levels") or {}
        try:
            return int(levels.get(str(user_id), NORMAL))
        except (TypeError, ValueError):
            return NORMAL

    def set_level(self, user_id, level: int) -> int:
        """设置用户等级，返回旧等级。"""
        levels = self.data.get("levels")
        if levels is None:
            levels = {}
            self.data["levels"] = levels
        key = str(user_id)
        old = int(levels.get(key, NORMAL))
        levels[key] = int(level)
        self.data.save()
        return old

    def is_banned(self, user_id) -> bool:
        return self.level_of(user_id) <= BAN

    def is_user(self, user_id) -> bool:
        return self.level_of(user_id) >= USER

    def is_admin(self, user_id) -> bool:
        return self.level_of(user_id) >= ADMIN

    def all_levels(self) -> dict:
        """返回 {uid(str): level(int)} 的副本。"""
        return {k: int(v) for k, v in (self.data.get("levels") or {}).items()}
