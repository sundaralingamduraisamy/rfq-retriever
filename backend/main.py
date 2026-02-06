import uuid
import uvicorn
import signal
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel
from settings import settings
from database import db

# Configure logging before importing other modules
from logging_config import setup_logging
setup_logging()

# Import API Routers
from api import documents, rfqs, generator

# Lifespan Events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if db:
        print("🔄 Checking Database Tables...")
        db.create_tables()
    yield
    # Shutdown
    if db:
        print("🔄 Closing database connections...")
        db.close_all()
    print("✅ Shutdown complete")

# App Initialization
app = FastAPI(title=settings.APP_TITLE, lifespan=lifespan)
SERVER_INSTANCE_ID = str(uuid.uuid4())

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Mounts
app.mount("/exports", StaticFiles(directory="exports"), name="exports")
app.mount("/rfq_pdf", StaticFiles(directory="exports"), name="rfq_pdf")

# Include Routers
app.include_router(documents.router)
app.include_router(rfqs.router)
app.include_router(generator.router)

# ----------------------------------------------------------------
# Auth & Config (Minimal App-Level endpoints)
# ----------------------------------------------------------------

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/api/config")
def get_config():
    return {
        "appName": settings.APP_NAME,
        "appRole": settings.APP_ROLE,
        "instanceId": SERVER_INSTANCE_ID
    }

@app.post("/api/login")
def login(creds: LoginRequest):
    if creds.username == settings.APP_USER and creds.password == settings.APP_PASSWORD:
        return {
            "token": "valid-session",
            "user": {
                "name": settings.APP_NAME,
                "role": settings.APP_ROLE
            },
            "instanceId": SERVER_INSTANCE_ID
        }
    raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.get("/")
def root():
    return {"message": "RFQ Deep Agent Running (PostgreSQL + PgVector)"}


if __name__ == "__main__":
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down gracefully...")
        raise KeyboardInterrupt
    
    signal.signal(signal.SIGINT, signal_handler)
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
