"""
/analyze endpoint — x402 payment gated.
Clients must pay USDC on Base before getting a deep analysis.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from agent.memory.client import recall_token
from agent.llm.analyze import deep_analyze

router = APIRouter()


class AnalyzeRequest(BaseModel):
    token: str
    symbol: str
    question: str = ""


@router.post("/analyze")
async def analyze(request: Request, payload: AnalyzeRequest):
    # x402 payment verification — header set by x402 middleware after payment confirmed
    payment_verified = request.headers.get("X-Payment-Verified", "false") == "true"
    if not payment_verified:
        # Return 402 with x402 payment details
        raise HTTPException(
            status_code=402,
            detail={
                "x402": True,
                "amount": "0.10",
                "currency": "USDC",
                "network": "base",
                "description": "Deep token analysis with memory context",
            },
        )

    memory = await recall_token(payload.token, include_all_tiers=True)
    result = await deep_analyze(payload.token, payload.symbol, payload.question, memory)
    return result
