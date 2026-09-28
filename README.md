# Cori 🐦‍⬛

> **This repository is archived.** Cori now lives inside CORTX:
> **[danbuildss/cortx → `agent/cori`](https://github.com/danbuildss/cortx/tree/main/agent/cori)**.
>
> Cori is CORTX's autonomous reliability agent. Today it discovers paid x402
> services (starting with the Coinbase CDP Bazaar), checks them for free, and
> queues good candidates for human review. It never pays for anything and never
> holds a wallet key. Design: [`docs/CORI_SCOUT_V0_SPEC.md`](https://github.com/danbuildss/cortx/blob/main/docs/CORI_SCOUT_V0_SPEC.md).
>
> What follows is the original hackathon scaffold (Aug 2026), kept for
> reference. It was never deployed.

---

## What it does

1. **Receives** alert webhooks from CORTX (the scaffold's examples below use token alerts; CORTX's real alerts are paid-API reliability incidents)
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
| `X402_PAY_TO_ADDRESS` | Base address that receives `/analyze` payments. A payment gate only needs a receiving address; never put a private key on an agent server. |
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
