import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import tasks, analytics, voice
from backend.app import config
import os

app = FastAPI(
    title="Offline AI Personal Productivity Assistant API",
    description="A privacy-focused local API utilizing custom trained NLP/ML models, offline STT, and vector search.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development; in production restrict to React Vite dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router)
app.include_router(analytics.router)
app.include_router(voice.router)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "Offline AI Personal Productivity Assistant",
        "version": "1.0.0",
        "database": tasks.db.get_db_type(),
        "ml_models_loaded": tasks.ml_service.models_loaded,
        "semantic_embeddings_loaded": tasks.nlp_service.has_embeddings
    }

if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host=config.HOST, port=config.PORT, reload=True)
