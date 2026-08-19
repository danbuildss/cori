"""
LLM analysis layer — builds prompts from memory context, calls Claude.
"""
import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-5"


def _format_memory(memory: dict) -> str:
    """Turn Sibyl memory results into a readable context block."""
    lines = []

    hot = memory.get("hot", [])
    if hot:
        lines.append("## Active context (HOT)")
        for item in hot:
            lines.append(f"- {item.get('content', '')}")

    warm = memory.get("warm", [])
    if warm:
        lines.append("\n## Token profile (WARM)")
        for item in warm:
            lines.append(f"- {item.get('content', '')}")

    cold = memory.get("cold", [])
    if cold:
        lines.append(f"\n## Past incidents (COLD) — {len(cold)} found")
        for item in cold[:5]:
            lines.append(f"- {item.get('content', '')[:200]}")

    if not lines:
        return "No prior memory for this token."

    return "\n".join(lines)


async def analyze_alert(alert: dict, memory: dict) -> dict:
    """
    Fast analysis for incoming webhook alerts.
    Uses Haiku for speed — this runs on every alert.
    """
    memory_context = _format_memory(memory)
    recurrence_count = len(memory.get("cold", []))

    prompt = f"""You are Cori, an AI crypto incident-response agent with memory.

## Alert
Token: {alert['symbol']} ({alert['token']})
Type: {alert['alert_type']}
Value: {alert['value']} (threshold: {alert['threshold']})
Time: {alert['timestamp']}

## Memory context
{memory_context}

## Task
Analyze this alert using the memory context above. Return JSON with:
- summary: one sentence (max 120 chars) for Telegram
- severity: "low" | "medium" | "high" | "critical"
- recurrence_count: number of prior similar incidents from memory
- pattern_summary: brief description of recurring pattern (or "first occurrence")
- recommendation: what the user should watch for or do
- full_text: 2-3 paragraph analysis for storage

Respond ONLY with valid JSON."""

    response = client.messages.create(
        model=HAIKU,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        result = json.loads(response.content[0].text)
    except Exception:
        result = {
            "summary": f"{alert['symbol']} {alert['alert_type']} alert triggered",
            "severity": "medium",
            "recurrence_count": recurrence_count,
            "pattern_summary": "parse error — raw alert",
            "recommendation": "Review manually",
            "full_text": response.content[0].text,
        }

    result["recurrence_count"] = max(result.get("recurrence_count", 0), recurrence_count)
    return result


async def deep_analyze(token: str, symbol: str, question: str, memory: dict) -> dict:
    """
    Deep x402-gated analysis using Sonnet + full memory context.
    """
    memory_context = _format_memory(memory)

    user_q = f"\n\nUser question: {question}" if question else ""

    prompt = f"""You are Cori, an AI crypto analyst with full memory access.

## Token: {symbol} ({token})

## Full memory context
{memory_context}
{user_q}

## Task
Provide a comprehensive analysis of this token's incident history, patterns, and risk profile.
Return JSON with:
- executive_summary: 2-3 sentences
- pattern_analysis: recurring patterns identified from memory
- risk_level: "low" | "medium" | "high" | "critical"
- key_incidents: list of up to 5 most significant past incidents
- recommendation: specific actionable guidance
- confidence: "low" | "medium" | "high" based on memory depth

Respond ONLY with valid JSON."""

    response = client.messages.create(
        model=SONNET,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return json.loads(response.content[0].text)
    except Exception:
        return {"raw": response.content[0].text, "error": "parse error"}
