import os
import httpx

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

SEVERITY_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
}


async def send_telegram(analysis: dict, incident_id: str):
    if not BOT_TOKEN or not CHAT_ID:
        return

    severity = analysis.get("severity", "medium")
    emoji = SEVERITY_EMOJI.get(severity, "⚪")
    recurrence = analysis.get("recurrence_count", 0)
    memory_line = (
        f"📚 *{recurrence} prior incidents* — {analysis.get('pattern_summary', '')}"
        if recurrence > 0
        else "🆕 First occurrence in memory"
    )

    text = (
        f"{emoji} *{severity.upper()} ALERT* `#{incident_id}`\n\n"
        f"{analysis.get('summary', '')}\n\n"
        f"{memory_line}\n\n"
        f"💡 {analysis.get('recommendation', '')}"
    )

    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
            },
            timeout=10,
        )
