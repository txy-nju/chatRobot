from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.feishu import router as feishu_router
from app.api.admin import router as admin_router
from app.api.oauth import router as oauth_router
from app.database import init_db
from app.services.personal import assistant

app = FastAPI(title="ChatRobot", version="1.0.0")

# API routes
app.include_router(feishu_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(oauth_router, prefix="/api")

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

# Serve Web UI static files
web_dir = Path(__file__).parent / "web"
if web_dir.exists():
    app.mount("/", StaticFiles(directory=str(web_dir), html=True), name="web")


@app.on_event("startup")
async def startup():
    await init_db()
    await assistant.start()


@app.on_event("shutdown")
async def shutdown():
    await assistant.stop()
