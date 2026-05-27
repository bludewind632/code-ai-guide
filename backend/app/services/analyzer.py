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


MAX_NODES = 30
TEST_PREFIXES = ("test_", "tests/", "docs_src/", "docs/", "scripts/", "benchmarks/")


def _is_core_file(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return not any(p.startswith(prefix) for prefix in TEST_PREFIXES)


def _top_module(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    return parts[0] if len(parts) > 1 else "."


def _short_name(path: str) -> str:
    """Show last 2 path segments for readability."""
    p = path.replace("\\", "/")
    parts = p.split("/")
    if len(parts) <= 2:
        return p
    return "/".join(parts[-2:])


def generate_mermaid(files: list[dict[str, Any]]) -> str:
    if not files:
        return 'graph TD\n  A["No analyzable files found"]'

    # 1) Keep only core source files (no tests, docs, scripts)
    core = [f for f in files if _is_core_file(f["path"])]

    # 2) Score by connectivity: how many other core files import this one
    path_set = {f["path"] for f in core}
    import_count: dict[str, int] = {f["path"]: 0 for f in core}
    edges_set: set[tuple[str, str]] = set()

    for f in core:
        for imp in f.get("imports", []):
            target = find_import_target(imp, files)
            if target and target != f["path"] and target in path_set:
                import_count[target] = import_count.get(target, 0) + 1
                edges_set.add((f["path"], target))

    # 3) Sort by connectivity, pick top N
    ranked = sorted(core, key=lambda f: import_count.get(f["path"], 0), reverse=True)[:MAX_NODES]
    selected = {f["path"] for f in ranked}

    # 4) Build node id map
    node_id: dict[str, str] = {}
    for idx, f in enumerate(ranked):
        node_id[f["path"]] = f"N{idx}"

    # 5) Group by top-level module for subgraphs
    groups: dict[str, list[dict]] = {}
    for f in ranked:
        mod = _top_module(f["path"])
        groups.setdefault(mod, []).append(f)

    lines = ["graph TD"]
    used_ids: set[str] = set()

    for mod, members in groups.items():
        if len(members) == 1:
            f = members[0]
            safe = _short_name(f["path"]).replace('"', "'")
            nid = node_id[f["path"]]
            lines.append(f'  {nid}["{safe}"]')
            used_ids.add(nid)
        else:
            lines.append(f"  subgraph {mod}")
            for f in members:
                safe = _short_name(f["path"]).replace('"', "'")
                nid = node_id[f["path"]]
                lines.append(f'    {nid}["{safe}"]')
                used_ids.add(nid)
            lines.append("  end")

    # 6) Add edges (only between selected nodes), limit per node
    edge_count: dict[str, int] = {}
    MAX_EDGES_PER_NODE = 3
    for src, tgt in sorted(edges_set):
        if src in selected and tgt in selected:
            if edge_count.get(src, 0) >= MAX_EDGES_PER_NODE:
                continue
            lines.append(f"  {node_id[src]} --> {node_id[tgt]}")
            edge_count[src] = edge_count.get(src, 0) + 1

    return "\n".join(lines)


def find_import_target(import_name: str, files: list[dict[str, Any]]) -> str | None:
    normalized = import_name.replace(".", "/")
    for file in files:
        path = file["path"].replace("\\", "/")
        if path.endswith(normalized + ".py") or path.endswith(normalized + ".js") or path.endswith(normalized + ".ts"):
            return file["path"]
    return None


def generate_learning_path(files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """生成分阶段的学习路径，包含阶段描述、优先级等丰富元数据。"""

    # ── 阶段定义：按阅读顺序排列 ──
    STAGES = [
        {"name": "入口 & 配置", "order": 1,
         "keywords": ["main", "app", "index", "config", "settings", "env", "bootstrap"]},
        {"name": "路由 & 控制器", "order": 2,
         "keywords": ["router", "controller", "route", "handler", "endpoint", "middleware", "api"]},
        {"name": "核心服务", "order": 3,
         "keywords": ["service", "core", "logic", "manager", "processor", "engine",
                      "pipeline", "analyzer", "generator", "repo_service", "llm_service"]},
        {"name": "数据模型", "order": 4,
         "keywords": ["model", "schema", "entity", "type", "dto", "interface", "domain", "models"]},
        {"name": "工具 & 辅助", "order": 5,
         "keywords": ["util", "helper", "common", "lib", "utils", "tool", "constant",
                      "exception", "error", "base"]},
    ]

    # ── 分类函数：将文件归入对应阶段 ──
    def classify(file: dict[str, Any]) -> tuple[int, str]:
        path = file["path"].lower()
        for stage in STAGES:
            for kw in stage["keywords"]:
                if kw in path:
                    return (stage["order"], stage["name"])
        return (99, "其他模块")

    # ── 描述生成：根据文件内容生成说明 ──
    def describe(file: dict[str, Any], stage_name: str) -> str:
        parts = []
        funcs = file.get("functions", [])
        classes = file.get("classes", [])
        imports = file.get("imports", [])

        desc_map = {
            "入口 & 配置": "项目启动入口",
            "路由 & 控制器": "处理请求路由",
            "核心服务": "核心业务逻辑",
            "数据模型": "数据结构定义",
            "工具 & 辅助": "通用工具模块",
            "其他模块": "补充模块",
        }
        parts.append(desc_map.get(stage_name, "补充模块"))

        details = []
        if classes:
            details.append(f"{len(classes)}个类")
        if funcs:
            details.append(f"{len(funcs)}个函数")
        if imports:
            details.append(f"依赖{len(imports)}个模块")
        if details:
            parts.append("，".join(details))

        return " · ".join(parts)

    # ── 预构建导入映射：import_name → file_path（只做一次）──
    import_to_file: dict[str, str] = {}
    for f in files:
        path = f["path"].replace("\\", "/")
        # 注册文件路径本身
        import_to_file[path] = f["path"]
        # 注册去掉后缀的路径
        for suffix in (".py", ".js", ".ts"):
            if path.endswith(suffix):
                import_to_file[path[:-len(suffix)]] = f["path"]

    # ── 一次性计算所有文件的被依赖数 ──
    dep_count_map: dict[str, int] = {f["path"]: 0 for f in files}
    for f in files:
        for imp in f.get("imports", []):
            normalized = imp.replace(".", "/")
            target = import_to_file.get(normalized)
            if not target:
                # 尝试模糊匹配
                for key, val in import_to_file.items():
                    if key.endswith("/" + normalized) or key.endswith(normalized + ".py") or key.endswith(normalized + ".js") or key.endswith(normalized + ".ts"):
                        target = val
                        break
            if target and target != f["path"]:
                dep_count_map[target] = dep_count_map.get(target, 0) + 1

    # ── 计分 & 分类 ──
    scored: list[dict[str, Any]] = []
    for f in files:
        stage_order, stage_name = classify(f)
        dep_count = dep_count_map.get(f["path"], 0)
        func_count = len(f.get("functions", []))
        class_count = len(f.get("classes", []))

        # 优先级 = 被依赖数×10 + 类数×5 + 函数数×2 + 阶段系数
        priority = dep_count * 10 + class_count * 5 + func_count * 2
        priority += max(0, 100 - stage_order * 15)

        scored.append({
            "file_path": f["path"],
            "stage": stage_name,
            "stage_order": stage_order,
            "priority": priority,
            "description": describe(f, stage_name),
        })

    # ── 排序：先按阶段顺序，再按优先级 ──
    scored.sort(key=lambda x: (x["stage_order"], -x["priority"]))

    # ── 选取每个阶段的 Top N 文件 ──
    STAGE_LIMITS = {1: 3, 2: 4, 3: 5, 4: 4, 5: 3, 99: 2}
    result: list[dict[str, Any]] = []
    stage_counts: dict[int, int] = {}

    for item in scored:
        so = item["stage_order"]
        limit = STAGE_LIMITS.get(so, 2)
        if stage_counts.get(so, 0) < limit:
            stage_counts[so] = stage_counts.get(so, 0) + 1
            result.append(item)

    # ── 补齐至约 18 条 ──
    result_paths = {r["file_path"] for r in result}
    remaining = [s for s in scored if s["file_path"] not in result_paths]
    remaining.sort(key=lambda x: -x["priority"])
    for item in remaining:
        if len(result) >= 18:
            break
        result.append(item)

    result.sort(key=lambda x: (x["stage_order"], -x["priority"]))
    return result


TREE_IGNORE = {".git", "node_modules", "dist", "build", "__pycache__", ".next", ".venv", "venv", ".idea", "conda-env", ".pytest_cache", "egg-info", ".mypy_cache", ".tox"}
TREE_MAX_FILES_PER_DIR = 30


def generate_annotated_tree(repo_path: Path, files: list[dict[str, Any]]) -> str:
    """生成带注释的项目文件树（├─ └─ │ 格式）。"""

    # ── 构建注释查找表 ──
    annotations: dict[str, str] = {}
    for f in files:
        classes = [c["name"] for c in f.get("classes", [])]
        funcs = [fn["name"] for fn in f.get("functions", [])]
        parts: list[str] = []
        if classes:
            shown = classes[:3]
            suffix = f" 等{len(classes)}个类" if len(classes) > 3 else ""
            parts.append(", ".join(shown) + suffix)
        if funcs:
            shown = funcs[:3]
            suffix = f" 等{len(funcs)}个函数" if len(funcs) > 3 else ""
            parts.append(", ".join(shown) + suffix)
        if parts:
            annotations[f["path"]] = "、".join(parts)

    def _make_annotation(rel_path: str) -> str:
        anno = annotations.get(rel_path, "")
        return f"  # {anno}" if anno else ""

    # ── 递归遍历生成树 ──
    def walk(path: Path, prefix: str) -> list[str]:
        lines: list[str] = []
        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return lines

        # 过滤忽略的目录/文件
        visible = [e for e in entries if e.name not in TREE_IGNORE and not e.name.startswith(".")]
        if len(visible) > TREE_MAX_FILES_PER_DIR:
            visible = visible[:TREE_MAX_FILES_PER_DIR]
            has_more = True
        else:
            has_more = False

        for i, entry in enumerate(visible):
            is_last = (i == len(visible) - 1) and not has_more
            connector = "└── " if is_last else "├── "

            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                lines.extend(walk(entry, prefix + extension))
            else:
                rel = str(entry.relative_to(repo_path)).replace("\\", "/")
                anno = _make_annotation(rel)
                lines.append(f"{prefix}{connector}{entry.name}{anno}→{rel}")

        if has_more:
            lines.append(f"{prefix}└── ... ({len(entries) - TREE_MAX_FILES_PER_DIR} 个更多文件)")

        return lines

    # ── 根目录 ──
    root_name = repo_path.name
    result_lines = [f"{root_name}/"]
    result_lines.extend(walk(repo_path, ""))
    return "\n".join(result_lines)
