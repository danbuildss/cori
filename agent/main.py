import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

from agent.routes import webhook, analyze, health

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Sibyl Memory is initialized at process start via CLI (`sibyl init`)
    # Nothing to set up here — the DB path is read from SIBYL_DB_PATH env var
    yield


app = FastAPI(title="Cori", version="0.1.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(webhook.router, prefix="/webhook")
app.include_router(analyze.router)
