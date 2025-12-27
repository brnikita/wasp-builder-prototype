from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import apps

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Wasp Builder API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(apps.router)


@app.get("/health")
def health():
    return {"status": "ok"}

