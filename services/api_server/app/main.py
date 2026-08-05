"""
FastAPI Application Entry Point
Chạy: python -m services.api_server.app.main
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.api_server.app.config import HOST, PORT
from services.api_server.app.routers import predict, enrich

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Loan Application & Credit Risk API",
    description="API thu thập thông tin khoản vay và tính toán điểm tín dụng (ML Core)",
    version="1.0.0",
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(predict.router)
app.include_router(enrich.router)


# ── Health / Root ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Loan Collection & Credit Risk API",
        "status": "online",
        "docs": f"http://{HOST}:{PORT}/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}


# ── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Starting API on http://{HOST}:{PORT}")
    print(f"📖 Swagger Docs: http://{HOST}:{PORT}/docs")
    uvicorn.run("services.api_server.app.main:app", host=HOST, port=PORT, reload=True)
