import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


async def explain_code(file_path: str, code: str) -> str:
    if not DEEPSEEK_API_KEY:
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
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": "deepseek-chat",
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

当前没有配置 DeepSeek API Key，所以返回基础解释。

文件：`{file_path}`

代码行数：{len(lines)}

建议阅读方式：

1. 先看 import，了解依赖。
2. 再看类和函数定义。
3. 找入口函数，例如 main、app、handler、router。
4. 结合架构图查看它与其他文件的关系。
"""
