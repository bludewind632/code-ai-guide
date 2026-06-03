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

# ── 节点类型推断规则（按优先级排列，越靠前优先级越高）──
NODE_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("database",  ["redis", "postgres", "mysql", "mongo", "sqlite", "database", "db", "pg", "mariadb", "couchdb", "cassandra", "neo4j", "dynamodb", "firestore", "supabase"]),
    ("external",  ["api", "http_client", "client", "openai", "anthropic", "gemini", "llm", "deepseek", "kimi", "external", "webhook", "sdk", "gateway", "proxy"]),
    ("storage",   ["storage", "s3", "blob", "minio", "file", "filesystem", "cache", "localstorage", "sessionstorage"]),
    ("service",   ["service", "handler", "controller", "server", "router"]),
    ("component", ["component", "util", "helper", "middleware", "hook", "plugin", "module", "provider", "context"]),
    ("client",    ["main", "app", "index", "page", "layout", "entry", "bootstrap", "cli"]),
]

# ── Mermaid 节点样式（暗色主题配色）──
NODE_STYLES: dict[str, str] = {
    "client":    "fill:#1e40af,stroke:#60a5fa,stroke-width:2px,color:#e0e7ff",
    "service":   "fill:#7c2d12,stroke:#f97316,stroke-width:2px,color:#ffedd5",
    "component": "fill:#3f3f46,stroke:#a1a1aa,stroke-width:2px,color:#e4e4e7",
    "database":  "fill:#1e3a8a,stroke:#3b82f6,stroke-width:2px,color:#dbeafe",
    "storage":   "fill:#6b21a8,stroke:#a855f7,stroke-width:2px,color:#f3e8ff",
    "external":  "fill:#0f766e,stroke:#14b8a6,stroke-width:2px,color:#ccfbf1",
    "default":   "fill:#374151,stroke:#9ca3af,stroke-width:2px,color:#e5e7eb",
}


def _infer_node_type(path: str, file_info: dict[str, Any] | None = None) -> str:
    """根据文件路径和内容推断节点类型."""
    p = path.replace("\\", "/").lower()
    parts = p.split("/")
    # 取文件名（去掉后缀）和路径各部分作为检查目标
    filename = parts[-1].rsplit(".", 1)[0] if "." in parts[-1] else parts[-1]
    # 构建检查词列表：完整路径 + 文件名 + 路径各部分
    candidates = [p, filename] + parts
    for ntype, keywords in NODE_TYPE_RULES:
        for kw in keywords:
            for c in candidates:
                if kw in c:
                    return ntype
    return "component"


def _is_core_file(path: str) -> bool:
    p = path.replace("\\", "/").lower()
    return not any(p.startswith(prefix) for prefix in TEST_PREFIXES)


def _top_module(path: str) -> str:
    parts = path.replace("\\", "/").split("/")
    return parts[0] if len(parts) > 1 else "."


# ── 语义化分组：类型 → 显示标签和排列顺序 ──
TYPE_GROUP_LABELS: dict[str, str] = {
    "client":    "入口 & 客户端",
    "service":   "核心服务",
    "component": "组件 & 工具",
    "database":  "数据存储",
    "storage":   "文件存储",
    "external":  "外部服务",
}
TYPE_GROUP_ORDER: list[str] = ["client", "service", "component", "database", "storage", "external"]


def _short_name(path: str) -> str:
    """Show last 2 path segments for readability."""
    p = path.replace("\\", "/")
    parts = p.split("/")
    if len(parts) <= 2:
        return p
    return "/".join(parts[-2:])


def generate_mermaid(files: list[dict[str, Any]]) -> str:
    if not files:
        return 'flowchart TB\n  A["No analyzable files found"]'

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

    # 5) Group by inferred node type, ordered logically
    groups: dict[str, list[dict]] = {}
    for f in ranked:
        ntype = _infer_node_type(f["path"], f)
        groups.setdefault(ntype, []).append(f)

    # ── 初始化配置：直线、合理间距 ──
    lines: list[str] = [
        "%%{init: {'flowchart': {'curve': 'linear', 'nodeSpacing': 30, 'rankSpacing': 120, 'padding': 20}, 'themeVariables': {'fontSize': '24px'}}}%%",
        "flowchart TB",
    ]

    # ── classDef 样式定义（替代逐节点 style）──
    for ntype, style in NODE_STYLES.items():
        if ntype == "default":
            continue
        lines.append(f"  classDef {ntype} {style}")

    # ── 节点 & 子图 ──
    typed_ids: dict[str, list[str]] = {}
    for ntype in TYPE_GROUP_ORDER:
        members = groups.get(ntype, [])
        if not members:
            continue
        label = TYPE_GROUP_LABELS.get(ntype, ntype)
        ids: list[str] = []
        if len(members) == 1:
            f = members[0]
            safe = _short_name(f["path"]).replace('"', "'")
            nid = node_id[f["path"]]
            lines.append(f'  {nid}["{safe}"]')
            ids.append(nid)
        else:
            lines.append(f"  subgraph \"{label}\"")
            lines.append("    direction TB")
            for f in members:
                safe = _short_name(f["path"]).replace('"', "'")
                nid = node_id[f["path"]]
                lines.append(f'    {nid}["{safe}"]')
                ids.append(nid)
            lines.append("  end")
        typed_ids[ntype] = ids

    # ── 边（仅选中节点间，每节点最多 3 条出边）──
    edge_count: dict[str, int] = {}
    MAX_EDGES_PER_NODE = 3
    for src, tgt in sorted(edges_set):
        if src in selected and tgt in selected:
            if edge_count.get(src, 0) >= MAX_EDGES_PER_NODE:
                continue
            lines.append(f"  {node_id[src]} --> {node_id[tgt]}")
            edge_count[src] = edge_count.get(src, 0) + 1

    # ── class 批量应用（一行一个类型）──
    for ntype in TYPE_GROUP_ORDER:
        ids = typed_ids.get(ntype, [])
        if ids:
            lines.append(f"  class {','.join(ids)} {ntype}")

    return "\n".join(lines)


def find_import_target(import_name: str, files: list[dict[str, Any]]) -> str | None:
    normalized = import_name.replace(".", "/")
    for file in files:
        path = file["path"].replace("\\", "/")
        if path.endswith(normalized + ".py") or path.endswith(normalized + ".js") or path.endswith(normalized + ".ts"):
            return file["path"]
    return None


def generate_graph_json(files: list[dict[str, Any]]) -> dict[str, Any]:
    """生成结构化 JSON 架构图数据，供前端灵活渲染."""
    if not files:
        return {"nodes": [], "edges": [], "cycles": []}

    core = [f for f in files if _is_core_file(f["path"])]
    path_set = {f["path"] for f in core}
    import_count: dict[str, int] = {f["path"]: 0 for f in core}
    edges_set: set[tuple[str, str]] = set()

    for f in core:
        for imp in f.get("imports", []):
            target = find_import_target(imp, files)
            if target and target != f["path"] and target in path_set:
                import_count[target] = import_count.get(target, 0) + 1
                edges_set.add((f["path"], target))

    ranked = sorted(core, key=lambda f: import_count.get(f["path"], 0), reverse=True)[:MAX_NODES]
    selected = {f["path"] for f in ranked}

    # ── 构建节点列表 ──
    nodes: list[dict[str, Any]] = []
    for idx, f in enumerate(ranked):
        ntype = _infer_node_type(f["path"], f)
        nodes.append({
            "id": f"N{idx}",
            "path": f["path"],
            "label": _short_name(f["path"]),
            "type": ntype,
            "language": f.get("language", "Unknown"),
            "class_count": len(f.get("classes", [])),
            "func_count": len(f.get("functions", [])),
            "import_count": import_count.get(f["path"], 0),
            "group": ntype,
            "group_label": TYPE_GROUP_LABELS.get(ntype, ntype),
            "style": NODE_STYLES.get(ntype, NODE_STYLES["default"]),
        })

    # ── 构建边列表 ──
    edges: list[dict[str, Any]] = []
    edge_count: dict[str, int] = {}
    MAX_EDGES_PER_NODE = 3
    for src, tgt in sorted(edges_set):
        if src in selected and tgt in selected:
            if edge_count.get(src, 0) >= MAX_EDGES_PER_NODE:
                continue
            src_id = next(n["id"] for n in nodes if n["path"] == src)
            tgt_id = next(n["id"] for n in nodes if n["path"] == tgt)
            edges.append({"source": src_id, "target": tgt_id})
            edge_count[src] = edge_count.get(src, 0) + 1

    # ── 构建分组（按类型语义分层，保持顺序）──
    ordered_groups: list[dict[str, Any]] = []
    seen_types: set[str] = set()
    for ntype in TYPE_GROUP_ORDER:
        type_node_ids = [n["id"] for n in nodes if n["group"] == ntype]
        if type_node_ids:
            ordered_groups.append({
                "name": ntype,
                "label": TYPE_GROUP_LABELS.get(ntype, ntype),
                "nodes": type_node_ids,
            })
            seen_types.add(ntype)
    # 兜底：未出现在排序表中的类型
    for n in nodes:
        if n["group"] not in seen_types:
            ordered_groups.append({
                "name": n["group"],
                "label": TYPE_GROUP_LABELS.get(n["group"], n["group"]),
                "nodes": [n["id"]],
            })
            seen_types.add(n["group"])

    # ── 循环依赖检测 ──
    cycles = detect_cycles(nodes, edges)

    return {
        "nodes": nodes,
        "edges": edges,
        "groups": ordered_groups,
        "cycles": cycles,
        "summary": {
            "total_files": len(files),
            "core_files": len(core),
            "shown_nodes": len(nodes),
            "shown_edges": len(edges),
        },
    }


def detect_cycles(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[list[str]]:
    """DFS 检测图中的循环依赖，返回所有找到的环."""
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        adj.setdefault(e["source"], []).append(e["target"])

    all_cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []
    in_stack: set[str] = set()

    def dfs(node_id: str) -> None:
        visited.add(node_id)
        rec_stack.append(node_id)
        in_stack.add(node_id)
        for neighbor in adj.get(node_id, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in in_stack:
                # 找到环：从 rec_stack 中截取
                cycle_start = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start:] + [neighbor]
                all_cycles.append(cycle)
        rec_stack.pop()
        in_stack.discard(node_id)

    for nid in adj:
        if nid not in visited:
            dfs(nid)

    return all_cycles


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
