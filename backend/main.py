from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS, validate
from routes.analyze import router as analyze_router
from routes.auth import router as auth_router
from routes.dashboard import router as dashboard_router
from services.dynamo import ensure_tables

validate()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_tables()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router)
app.include_router(auth_router)
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}
