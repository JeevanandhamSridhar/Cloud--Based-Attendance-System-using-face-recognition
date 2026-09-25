import os
import sys
import uvicorn

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 STARTING SMART ATTENDANCE FASTAPI SERVER")
    print("=" * 60)
    print(" -> REST API Endpoint: http://127.0.0.1:8000")
    print(" -> Swagger UI Docs:   http://127.0.0.1:8000/docs")
    print(" -> ReDoc UI Docs:     http://127.0.0.1:8000/redoc")
    print("=" * 60)
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
