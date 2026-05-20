import hashlib
import os
import shutil
from pathlib import Path
from git import Repo

BASE_DIR = Path(__file__).resolve().parents[2]
REPOS_DIR = BASE_DIR / "repos"
REPOS_DIR.mkdir(exist_ok=True)

IGNORE_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".next", ".venv", "venv"}


def repo_id_from_url(repo_url: str) -> str:
    return hashlib.sha1(repo_url.encode("utf-8")).hexdigest()[:12]


def clone_or_update(repo_url: str) -> tuple[str, Path]:
    repo_id = repo_id_from_url(repo_url)
    repo_path = REPOS_DIR / repo_id

    if repo_path.exists():
        try:
            repo = Repo(repo_path)
            repo.remotes.origin.pull()
        except Exception:
            shutil.rmtree(repo_path)
            Repo.clone_from(repo_url, repo_path)
    else:
        Repo.clone_from(repo_url, repo_path)

    return repo_id, repo_path


def get_repo_path(repo_id: str) -> Path:
    repo_path = REPOS_DIR / repo_id
    if not repo_path.exists():
        raise FileNotFoundError("Repo not found. Please analyze it first.")
    return repo_path


def build_file_tree(repo_path: Path) -> list[dict]:
    def walk(path: Path) -> list[dict]:
        nodes = []
        for child in sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())):
            if child.name in IGNORE_DIRS:
                continue
            rel = str(child.relative_to(repo_path))
            if child.is_dir():
                nodes.append({"name": child.name, "path": rel, "type": "dir", "children": walk(child)})
            else:
                nodes.append({"name": child.name, "path": rel, "type": "file"})
        return nodes

    return walk(repo_path)


def read_file(repo_path: Path, file_path: str) -> str:
    target = (repo_path / file_path).resolve()
    if not str(target).startswith(str(repo_path.resolve())):
        raise ValueError("Invalid file path")
    return target.read_text(encoding="utf-8", errors="ignore")
