import json
from pathlib import Path
from typing import Dict, List

Message = Dict[str, str]


class MemoryStore:
    """
    使用 JSON 文件保存聊天历史的简单实现。

    这里只保留一个类，方便初学者理解：构造函数负责准备存储目录，
    `load` 读取历史，`save` 写回历史，其余逻辑都在内部完成。
    """

    def __init__(self, root_dir: str):
        """
        初始化存储目录。

        :param root_dir: 保存所有会话文件的根目录路径。
        """
        self.root = Path(root_dir)               # 转成 Path 对象，便于后续操作
        self.root.mkdir(parents=True, exist_ok=True)  # 若目录不存在则创建（支持多级）

    def load(self, session_id: str) -> List[Message]:
        """
        根据会话 ID 读取历史记录。

        - 会话 ID 会被转换成 root_dir 下的文件名（例如 default.json）。
        - 如果文件不存在，则返回空列表，代表这是一次全新的对话。
        """
        target = self._file_path(session_id)
        if target.exists():
            return self._load_file(target)
        return []

    def save(self, session_id: str, history: List[Message]) -> None:
        """
        将历史记录保存到磁盘。

        `ensure_ascii=False` 能保留中文字符，`indent=2` 让生成的 JSON 更易读。
        """
        target = self._file_path(session_id)
        with target.open("w", encoding="utf-8") as handle:
            json.dump(history, handle, ensure_ascii=False, indent=2)

    # --- 以下是内部辅助方法 ---

    def _file_path(self, session_id: str) -> Path:
        """
        根据会话 ID 生成文件路径。

        只保留字母、数字、连字符和下划线，防止生成非法文件名。
        空字符串会退回到默认会话 `default`。
        """
        safe_id = session_id.strip() or "default"
        safe_id = "".join(ch for ch in safe_id if ch.isalnum() or ch in ("-", "_"))
        if not safe_id:
            safe_id = "default"
        return self.root / f"{safe_id}.json"

    @staticmethod
    def _load_file(path: Path) -> List[Message]:
        """辅助函数：读取 JSON 文件并返回列表。"""
        try:
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except FileNotFoundError:
            return []
