from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalyzeRequest, AnalyzeResponse, ExplainRequest
from app.services.repo_service import clone_or_update, build_file_tree, get_repo_path, read_file
from app.services.analyzer import analyze_repo, generate_mermaid, generate_learning_path
from app.services.llm_service import explain_code

app = FastAPI(title="Repo Insight MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health():
    return {"status": "ok", "name": "Repo Insight MVP"}


@app.post("/api/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        repo_id, repo_path = clone_or_update(str(req.repo_url))
        tree = build_file_tree(repo_path)
        files = analyze_repo(repo_path)
        mermaid = generate_mermaid(files)
        learning_path = generate_learning_path(files)
        return AnalyzeResponse(
            repo_id=repo_id,
            tree=tree,
            files=files,
            mermaid=mermaid,
            learning_path=learning_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/explain")
async def explain(req: ExplainRequest):
    try:
        repo_path = get_repo_path(req.repo_id)
        code = read_file(repo_path, req.file_path)
        explanation = await explain_code(req.file_path, code)
        return {"file_path": req.file_path, "explanation": explanation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
