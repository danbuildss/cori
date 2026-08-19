import hashlib
import hmac
import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agent.memory.client import recall_token, store_incident
from agent.llm.analyze import analyze_alert
from agent.telegram.send import send_telegram

router = APIRouter()

WEBHOOK_SECRET = os.getenv("CORTX_WEBHOOK_SECRET", "")


def verify_hmac(body: bytes, signature: str) -> bool:
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


class AlertPayload(BaseModel):
    token: str
    symbol: str
    alert_type: str        # "price_spike" | "volume_anomaly" | "whale_move"
    value: float
    threshold: float
    timestamp: str
    extra: dict = {}


class ResolvePayload(BaseModel):
    incident_id: str
    outcome: str           # "confirmed" | "false_positive" | "unknown"
    notes: str = ""


@router.post("/alert")
async def receive_alert(request: Request, payload: AlertPayload):
    sig = request.headers.get("X-Cori-Signature", "")
    body = await request.body()
    if WEBHOOK_SECRET and not verify_hmac(body, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Pull relevant memory for this token
    memory = await recall_token(payload.token, payload.alert_type)

    # Analyze with LLM + memory context
    analysis = await analyze_alert(payload.model_dump(), memory)

    # Store the new incident into memory (COLD tier journal + WARM token profile)
    incident_id = await store_incident(payload.model_dump(), analysis)

    # Send to Telegram
    await send_telegram(analysis, incident_id)

    return {"ok": True, "incident_id": incident_id}


@router.post("/resolve")
async def resolve_incident(request: Request, payload: ResolvePayload):
    sig = request.headers.get("X-Cori-Signature", "")
    body = await request.body()
    if WEBHOOK_SECRET and not verify_hmac(body, sig):
        raise HTTPException(status_code=401, detail="Invalid signature")

    from agent.memory.client import resolve_incident as mem_resolve
    await mem_resolve(payload.incident_id, payload.outcome, payload.notes)
    return {"ok": True}
