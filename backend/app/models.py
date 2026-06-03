from pydantic import BaseModel, HttpUrl
from typing import Any, Literal


class AnalyzeRequest(BaseModel):
    repo_url: HttpUrl
    force: bool = False  # 强制重新分析，忽略缓存


class ExplainRequest(BaseModel):
    repo_id: str
    file_path: str
    provider: str = "deepseek"  # deepseek | kimi


class AskRequest(BaseModel):
    repo_id: str
    question: str
    file_path: str | None = None
    history: list[dict[str, str]] = []
    provider: str = "deepseek"  # deepseek | kimi


class LearningPathItem(BaseModel):
    file_path: str
    stage: str
    stage_order: int
    priority: int
    description: str


class AnalyzeResponse(BaseModel):
    repo_id: str
    tree: list[dict[str, Any]]
    files: list[dict[str, Any]]
    mermaid: str
    graph_json: dict[str, Any] = {}
    cycles: list[list[str]] = []
    learning_path: list[LearningPathItem]
    annotated_tree: str
    file_annotations: dict[str, str]


class ConfigResponse(BaseModel):
    providers: list[dict[str, str]]


class HistoryItem(BaseModel):
    repo_id: str
    repo_url: str
    commit_hash: str
    analyzed_at: str


class HistoryResponse(BaseModel):
    history: list[HistoryItem]
