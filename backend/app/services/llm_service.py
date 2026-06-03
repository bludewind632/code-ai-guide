import os
import httpx
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Provider 配置 ──
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
KIMI_BASE_URL = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")

PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek-v4-Pro",
        "api_key": DEEPSEEK_API_KEY,
        "base_url": DEEPSEEK_BASE_URL,
        "model": "deepseek-chat",
        "available": bool(DEEPSEEK_API_KEY),
    },
    "kimi": {
        "name": "Kimi-K2.6",
        "api_key": KIMI_API_KEY,
        "base_url": KIMI_BASE_URL,
        "model": "moonshot-v1-8k",
        "available": bool(KIMI_API_KEY),
    },
}


def get_provider(provider: str) -> dict:
    """获取指定 provider 配置，若不可用则回退到 deepseek。"""
    p = provider.lower()
    if p not in PROVIDERS:
        p = "deepseek"
    cfg = PROVIDERS[p]
    # 如果指定的不可用，回退到第一个可用的
    if not cfg["available"]:
        for key, val in PROVIDERS.items():
            if val["available"]:
                cfg = val
                break
    return cfg


def get_available_providers() -> list[dict[str, str]]:
    """返回当前可用的 provider 列表（用于前端下拉选择）。"""
    result = []
    for key, cfg in PROVIDERS.items():
        result.append({
            "id": key,
            "name": cfg["name"],
            "available": str(cfg["available"]).lower(),
        })
    return result


def _api_key_missing_hint(provider_cfg: dict) -> str:
    return f"当前没有配置 {provider_cfg['name']} API Key，所以返回基础解释。"


async def explain_code(file_path: str, code: str, provider: str = "deepseek") -> str:
    cfg = get_provider(provider)
    if not cfg["available"]:
        return local_explanation(file_path, code)

    prompt = f"""
你是资深代码导师。请用中文解释下面文件：

文件路径：{file_path}

要求：
1. 说明这个文件的职责
2. 列出关键函数/类
3. 解释主要执行流程
4. 给新手阅读建议

代码：
```text
{code[:12000]}
```
"""

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json={
                "model": cfg["model"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def local_explanation(file_path: str, code: str) -> str:
    lines = code.splitlines()
    return f"""
## 本地解释模式

当前没有配置可用的 API Key，所以返回基础解释。

文件：`{file_path}`

代码行数：{len(lines)}

建议阅读方式：

1. 先看 import，了解依赖。
2. 再看类和函数定义。
3. 找入口函数，例如 main、app、handler、router。
4. 结合架构图查看它与其他文件的关系。
"""


async def ask_question(
    repo_path: str,
    question: str,
    file_path: str | None = None,
    history: list[dict[str, str]] | None = None,
    provider: str = "deepseek",
) -> str:
    """向 AI 提问关于仓库的问题，支持多轮对话。"""
    repo_dir = Path(repo_path)

    # ── 构建仓库上下文 ──
    context_parts = []

    # 文件树摘要
    tree_lines = _build_tree_summary(repo_dir)
    if tree_lines:
        context_parts.append("## 仓库文件结构\n" + "\n".join(tree_lines[:60]))

    # 如果指定了文件，包含其代码
    if file_path:
        try:
            target = (repo_dir / file_path).resolve()
            if str(target).startswith(str(repo_dir.resolve())):
                code = target.read_text(encoding="utf-8", errors="ignore")
                context_parts.append(f"\n## 当前关注的文件：{file_path}\n```\n{code[:10000]}\n```")
        except Exception:
            pass

    context = "\n".join(context_parts) if context_parts else "（暂无仓库上下文）"

    system_prompt = f"""你是一个专业的代码学习助手，帮助用户理解代码仓库。

以下是当前仓库的信息：

{context}

请遵守以下规则：
1. 用中文回答，简洁清晰
2. 结合仓库上下文给出具体分析，不要泛泛而谈
3. 如果用户问的问题与当前仓库无关，也可以正常回答
4. 涉及到代码结构时，说明文件之间的依赖关系
5. 回答尽量结构化，适当使用列表和标题"""

    cfg = get_provider(provider)
    if not cfg["available"]:
        return _local_answer(question, file_path, repo_dir)

    # ── 构建消息列表 ──
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        for h in history[-10:]:  # 最多保留最近 10 轮
            role = h.get("role", "user")
            content = h.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": question})

    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            json={
                "model": cfg["model"],
                "messages": messages,
                "temperature": 0.4,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _build_tree_summary(repo_dir: Path, prefix: str = "", max_depth: int = 3) -> list[str]:
    """构建文件树摘要（限制深度和数量）。"""
    IGNORE = {".git", "node_modules", "dist", "build", "__pycache__", ".next", ".venv", "venv", ".idea", "conda-env"}
    lines: list[str] = []
    try:
        entries = sorted(repo_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return lines

    depth = prefix.count("│") + prefix.count("├") + prefix.count("└")
    if depth >= max_depth:
        return lines

    count = 0
    for entry in entries:
        if entry.name in IGNORE or entry.name.startswith("."):
            continue
        if count >= 30:
            lines.append(f"{prefix}... (更多文件)")
            break
        if entry.is_dir():
            lines.append(f"{prefix}📁 {entry.name}/")
            children = _build_tree_summary(entry, prefix + "  ", max_depth)
            lines.extend(children[:10])
        else:
            lines.append(f"{prefix}📄 {entry.name}")
        count += 1
    return lines


def _local_answer(question: str, file_path: str | None, repo_dir: Path) -> str:
    """没有 API Key 时的本地回答。"""
    name = repo_dir.name
    parts = ["## 本地回答模式\n", f"当前仓库：`{name}`", f"你的问题：{question}"]
    if file_path:
        parts.append(f"\n相关文件：`{file_path}`")
    parts.append("\n\n> ⚠️ 未配置可用的 API Key，无法生成 AI 回答。请设置 `DEEPSEEK_API_KEY` 或 `KIMI_API_KEY` 环境变量。")
    return "\n".join(parts)
