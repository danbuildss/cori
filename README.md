# Cori 🪶

**AI incident-response agent for CORTX — powered by Sibyl Memory**

Cori watches your CORTX alerts, builds memory across incidents, and sends smarter Telegram briefings over time. The more alerts it sees, the sharper its analysis gets — because it actually remembers.

---

## What it does

1. **Receives** alert webhooks from CORTX (price spikes, volume anomalies, whale moves)
2. **Checks memory** — has this token spiked before? What happened last time?
3. **Analyzes** the current alert in context of past incidents
4. **Delivers** a Telegram message with memory-backed context, not just raw data
5. **Stores** the incident and outcome back into Sibyl Memory for next time

Delete the memory → Cori gives generic alerts. Memory intact → Cori gives context.

---

## Stack

- **Runtime**: Python 3.11 / FastAPI
- **Memory**: [Sibyl Memory](https://github.com/NirDiamant/sibyl-memory) — SQLite + FTS5, zero embeddings
- **LLM**: Claude 3.5 Haiku (analysis), Claude 3.5 Sonnet (complex summaries)
- **Delivery**: Telegram Bot API (shared with CORTX)
- **Payment gate**: x402 protocol on Base mainnet USDC (for `/analyze` endpoint)

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install and init Sibyl Memory
pip install 'sibyl-memory-cli[mcp]'
sibyl init
sibyl setup

# 3. Copy env and fill in values
cp .env.example .env

# 4. Run the agent
uvicorn agent.main:app --reload --port 8000
```

---

## Environment variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `TELEGRAM_BOT_TOKEN` | From @BotFather — same bot as CORTX |
| `TELEGRAM_CHAT_ID` | Target chat / channel ID |
| `CORTX_WEBHOOK_SECRET` | Shared secret from CORTX alert config |
| `X402_PRIVATE_KEY` | Base wallet private key for x402 payments |
| `SIBYL_DB_PATH` | Path to Sibyl Memory SQLite DB (default: `~/.sibyl/memory.db`) |

---

## API

| Endpoint | Auth | Description |
|---|---|---|
| `POST /webhook/alert` | HMAC secret | Receive alert from CORTX, analyze with memory, send Telegram |
| `POST /webhook/resolve` | HMAC secret | Mark incident resolved, store outcome in memory |
| `POST /analyze` | x402 USDC | On-demand deep analysis of any token + memory context |
| `GET /health` | None | Health check |
| `GET /memory/stats` | None | Memory tier stats |

---

## Memory tiers

| Tier | What's stored | Example |
|---|---|---|
| HOT | Active incident context | "SOL spike ongoing — +23% in 4h" |
| WARM | Token profiles, recurrence patterns | "SOL has spiked 3x in 90 days" |
| COLD | Incident journal, outcomes | "2026-08-10: SOL spike → dumped 18h later" |
| REFERENCE | Token metadata, baseline stats | "SOL normal vol range: $2B–$4B" |

---

## Built for Sibyl Memory Hackathon

Sep 1–10, 2026. Memory is load-bearing: remove Sibyl Memory and Cori loses all historical context — alerts become generic, patterns are invisible, recurrence detection breaks.

---

## License

MIT
