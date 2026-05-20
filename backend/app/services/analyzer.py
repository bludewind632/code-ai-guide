import ast
import re
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {".py", ".js", ".jsx", ".ts", ".tsx"}
IGNORE_PARTS = {".git", "node_modules", "dist", "build", "__pycache__", ".next", ".venv", "venv"}


def should_scan(path: Path) -> bool:
    return path.suffix in SUPPORTED_SUFFIXES and not any(part in IGNORE_PARTS for part in path.parts)


def analyze_repo(repo_path: Path) -> list[dict[str, Any]]:
    results = []
    for file in repo_path.rglob("*"):
        if file.is_file() and should_scan(file):
            rel = str(file.relative_to(repo_path))
            text = file.read_text(encoding="utf-8", errors="ignore")
            if file.suffix == ".py":
                info = analyze_python(text)
            else:
                info = analyze_js_ts(text)
            info["path"] = rel
            info["language"] = language_from_suffix(file.suffix)
            results.append(info)
    return results


def language_from_suffix(suffix: str) -> str:
    return {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "React JSX",
        ".ts": "TypeScript",
        ".tsx": "React TSX",
    }.get(suffix, "Unknown")


def analyze_python(source: str) -> dict[str, Any]:
    data: dict[str, Any] = {"classes": [], "functions": [], "imports": []}
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return data

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            data["classes"].append({"name": node.name, "line": node.lineno})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            data["functions"].append({"name": node.name, "line": node.lineno})
        elif isinstance(node, ast.Import):
            for n in node.names:
                data["imports"].append(n.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            data["imports"].append(module)
    return data


def analyze_js_ts(source: str) -> dict[str, Any]:
    class_names = re.findall(r"class\s+([A-Za-z_$][\w$]*)", source)
    function_names = re.findall(r"function\s+([A-Za-z_$][\w$]*)\s*\(", source)
    arrow_names = re.findall(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", source)
    imports = re.findall(r"import\s+(?:.+?\s+from\s+)?['\"]([^'\"]+)['\"]", source)

    return {
        "classes": [{"name": name, "line": 0} for name in class_names],
        "functions": [{"name": name, "line": 0} for name in function_names + arrow_names],
        "imports": imports,
    }


def generate_mermaid(files: list[dict[str, Any]]) -> str:
    lines = ["graph TD"]
    module_ids: dict[str, str] = {}

    for idx, file in enumerate(files):
        path = file["path"]
        module_id = f"F{idx}"
        module_ids[path] = module_id
        safe_label = path.replace('"', "'")
        lines.append(f'  {module_id}["{safe_label}"]')

    for idx, file in enumerate(files):
        imports = file.get("imports", [])[:8]
        for imp in imports:
            target = find_import_target(imp, files)
            if target and target != file["path"]:
                lines.append(f"  F{idx} --> {module_ids[target]}")

    if len(lines) == 1:
        lines.append('  A["No analyzable files found"]')
    return "\n".join(lines)


def find_import_target(import_name: str, files: list[dict[str, Any]]) -> str | None:
    normalized = import_name.replace(".", "/")
    for file in files:
        path = file["path"].replace("\\", "/")
        if path.endswith(normalized + ".py") or path.endswith(normalized + ".js") or path.endswith(normalized + ".ts"):
            return file["path"]
    return None


def generate_learning_path(files: list[dict[str, Any]]) -> list[str]:
    priority_keywords = ["main", "app", "index", "server", "router", "controller", "service", "model", "schema"]

    def score(file: dict[str, Any]) -> int:
        path = file["path"].lower()
        points = 0
        for i, kw in enumerate(priority_keywords):
            if kw in path:
                points += 100 - i * 8
        points += len(file.get("functions", [])) * 2
        points += len(file.get("classes", [])) * 3
        return points

    ranked = sorted(files, key=score, reverse=True)
    return [f["path"] for f in ranked[:10]]
