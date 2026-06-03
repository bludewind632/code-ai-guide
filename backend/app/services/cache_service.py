"""分析结果缓存服务 —— 避免重复分析同一个 commit 的仓库。"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[2]
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

HISTORY_FILE = CACHE_DIR / "_history.json"


# ═══════════════════════════════════════════════════════════════
# 缓存读写
# ═══════════════════════════════════════════════════════════════

def _cache_path(repo_id: str) -> Path:
    return CACHE_DIR / f"{repo_id}.json"


def get_cached(repo_id: str, commit_hash: str) -> dict | None:
    """读取缓存。若 commit 不匹配则返回 None。"""
    path = _cache_path(repo_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    if data.get("commit_hash") != commit_hash:
        return None
    return data.get("result")


def save_cache(repo_id: str, commit_hash: str, result: dict) -> None:
    """保存分析结果到缓存文件。"""
    _cache_path(repo_id).write_text(
        json.dumps({
            "commit_hash": commit_hash,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "result": result,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ═══════════════════════════════════════════════════════════════
# 历史记录
# ═══════════════════════════════════════════════════════════════

def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(entries: list[dict]) -> None:
    HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def record_history(repo_id: str, repo_url: str, commit_hash: str) -> None:
    """记录一次分析历史（去重 + 移至最前）。"""
    entries = _load_history()
    # 移除同 repo_id 的旧记录
    entries = [e for e in entries if e.get("repo_id") != repo_id]
    entries.insert(0, {
        "repo_id": repo_id,
        "repo_url": repo_url,
        "commit_hash": commit_hash,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
    })
    # 最多保留 20 条
    _save_history(entries[:20])


def get_history() -> list[dict]:
    """返回历史记录列表。"""
    return _load_history()


def clear_cache_for_repo(repo_id: str) -> None:
    """删除某个仓库的缓存文件。"""
    path = _cache_path(repo_id)
    if path.exists():
        path.unlink()


def clear_all_cache() -> None:
    """清空所有缓存文件。"""
    for f in CACHE_DIR.glob("*.json"):
        if f.name != "_history.json":
            f.unlink()


def clear_all_history() -> None:
    """清空历史记录文件。"""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()


def clear_all() -> None:
    """清空所有缓存 + 历史记录。"""
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
