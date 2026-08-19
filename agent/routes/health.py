from fastapi import APIRouter
from agent.memory.client import memory_stats

router = APIRouter()


@router.get("/health")
async def health():
    return {"status": "ok", "service": "cori"}


@router.get("/memory/stats")
async def get_memory_stats():
    return await memory_stats()
