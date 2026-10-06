# SolMemeIntel

Solana meme-coin market intelligence and research agent. Scans live Solana pairs, scores tokens across multiple dimensions, flags rug-risk signals, and alerts on emerging narratives.

**Research only - this bot never executes trades or touches a wallet.**

## Quick Start

```bash
pip install requests
python solmemeintel.py
```

## Configuration

Edit the top of `solmemeintel.py`:

- `USE_MOCK = False` - live DexScreener data (default). Set `True` for demo data.
- `SCAN_INTERVAL_SEC = 300` - seconds between scans. Use `5` for testing.

## What It Does

- Pulls fresh Solana pairs from DexScreener (free, no API key)
- Scores each token 0-100 across freshness, liquidity, risk flags, and buy/sell pressure
- Flags liquidity under $10K/$30K, sell pressure, and (with GMGN data) dev/sniper concentration
- Prints a scan summary every interval; Ctrl+C to stop

## Data Sources

| Source | Status | Cost |
|--------|--------|------|
| DexScreener | Wired (live) | Free |
| GMGN | Not yet - needs paid API key | Paid |
| X/Twitter | Mocked | Paid |
| Birdeye | Not yet | Paid |

## Safety

- No wallet, no private key, no transaction signing anywhere in this repo
- The bot only reads public market data and prints analysis
