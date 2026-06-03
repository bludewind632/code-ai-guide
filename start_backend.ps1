$host.ui.RawUI.WindowTitle = "Backend :8000"
cd E:\code-ai-guide\backend
E:\code-ai-guide\backend\conda-env\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
