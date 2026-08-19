"""
Sibyl Memory client — thin wrappers around sibyl-memory-cli SDK.
Tiers: HOT (working context), WARM (token profiles), COLD (incident journal), REFERENCE (metadata)
"""
import os
import uuid
from datetime import datetime, UTC

# sibyl-memory-cli exposes a Python API after `sibyl init`
# Import defensively so the app starts even if not yet installed
try:
    from sibyl import memory as sibyl
    SIBYL_AVAILABLE = True
except ImportError:
    SIBYL_AVAILABLE = False
    sibyl = None

DB_PATH = os.getenv("SIBYL_DB_PATH", "~/.sibyl/memory.db")


def _check():
    if not SIBYL_AVAILABLE:
        raise RuntimeError("sibyl-memory-cli not installed. Run: pip install 'sibyl-memory-cli[mcp]'")


async def recall_token(token: str, alert_type: str = "", include_all_tiers: bool = False) -> dict:
    """Pull HOT + WARM + COLD memory for a token to build analysis context."""
    _check()

    query = f"{token} {alert_type}".strip()

    hot = sibyl.search(query=query, tier="HOT", limit=5)
    warm = sibyl.search(query=f"token:{token}", tier="WARM", limit=3)
    cold = sibyl.search(query=f"token:{token} incident", tier="COLD", limit=10)

    result = {"hot": hot, "warm": warm, "cold": cold}

    if include_all_tiers:
        ref = sibyl.search(query=f"token:{token} baseline", tier="REFERENCE", limit=3)
        result["reference"] = ref

    return result


async def store_incident(alert: dict, analysis: dict) -> str:
    """Write new incident to HOT (active) and COLD (journal) tiers."""
    _check()

    incident_id = str(uuid.uuid4())[:8]
    now = datetime.now(UTC).isoformat()

    # HOT: active working context (short TTL)
    sibyl.store(
        content=f"[ACTIVE] {alert['symbol']} {alert['alert_type']} — {analysis.get('summary', '')}",
        tier="HOT",
        metadata={"token": alert["token"], "incident_id": incident_id, "ts": now},
    )

    # COLD: permanent incident journal
    sibyl.store(
        content=(
            f"INCIDENT {incident_id} | {now}\n"
            f"Token: {alert['symbol']} ({alert['token']})\n"
            f"Type: {alert['alert_type']} | Value: {alert['value']} | Threshold: {alert['threshold']}\n"
            f"Analysis: {analysis.get('full_text', '')}\n"
            f"Recurrence: {analysis.get('recurrence_count', 0)} prior incidents"
        ),
        tier="COLD",
        metadata={"token": alert["token"], "incident_id": incident_id, "ts": now, "resolved": False},
    )

    # WARM: update token profile with latest spike data
    _upsert_token_profile(alert, analysis, incident_id)

    return incident_id


def _upsert_token_profile(alert: dict, analysis: dict, incident_id: str):
    """Update WARM-tier token profile with new incident data."""
    existing = sibyl.search(query=f"token_profile:{alert['token']}", tier="WARM", limit=1)

    count = 1
    if existing:
        # naive increment — real impl would parse the stored count
        count = analysis.get("recurrence_count", 0) + 1

    sibyl.store(
        content=(
            f"TOKEN_PROFILE {alert['token']}\n"
            f"Symbol: {alert['symbol']}\n"
            f"Total {alert['alert_type']} incidents: {count}\n"
            f"Last incident: {incident_id}\n"
            f"Pattern: {analysis.get('pattern_summary', 'insufficient data')}"
        ),
        tier="WARM",
        metadata={"token": alert["token"], "type": "token_profile"},
    )


async def resolve_incident(incident_id: str, outcome: str, notes: str):
    """Mark incident resolved in COLD journal."""
    _check()

    sibyl.store(
        content=f"RESOLVED {incident_id} | outcome={outcome} | {notes}",
        tier="COLD",
        metadata={"incident_id": incident_id, "resolved": True, "outcome": outcome},
    )


async def memory_stats() -> dict:
    """Return per-tier record counts for /memory/stats."""
    if not SIBYL_AVAILABLE:
        return {"error": "sibyl not installed"}

    tiers = ["HOT", "WARM", "COLD", "REFERENCE", "ARCHIVE"]
    stats = {}
    for tier in tiers:
        try:
            results = sibyl.search(query="*", tier=tier, limit=1000)
            stats[tier.lower()] = len(results)
        except Exception:
            stats[tier.lower()] = None

    return {"tiers": stats, "db_path": DB_PATH}
