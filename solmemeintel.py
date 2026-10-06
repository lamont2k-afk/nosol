import os, time, json, random
from datetime import datetime

# ---------- CONFIG ----------
USE_MOCK_GMGN = True
USE_MOCK_X = True
USE_MOCK_BIRDEYE = True
SCAN_INTERVAL_SEC = 5  # short for testing; use 300 in production

# ---------- MOCK DATA ----------
def mock_gmgn_launches():
    return [
        {"symbol": "PEPE2", "age_min": 60, "mcap": 185000, "liquidity": 45000,
         "dev_pct": 4, "snipers": 3, "top10_pct": 22, "risk_flags": []},
        {"symbol": "AIAGENT", "age_min": 25, "mcap": 120000, "liquidity": 18000,
         "dev_pct": 9, "snipers": 6, "top10_pct": 38, "risk_flags": ["liquidity_under_30k"]},
        {"symbol": "WIF2", "age_min": 15, "mcap": 80000, "liquidity": 8500,
         "dev_pct": 22, "snipers": 11, "top10_pct": 61, "risk_flags": ["top10_over_50pct", "dev_over_20pct", "liquidity_under_10k" {"theme": "AI agents", "mentions": 340, "kol_mentions": 12, "momentum": "accelerating"},
        {"theme": "cat memes", "mentions": 210, "kol_mentions": 5, "momentum": "flat"},
        {"theme": "political", "mentions": 90, "kol_mentions": 2, "momentum": "declining"},
        {"theme": "anime", "mentions": 150, "kol_mentions": 7, "momentum": "emerging"},
    ]

def mock_birdeye(symbol):
    return {"symbol": symbol, "price": round(random.uniform(0.00001, 0.01), 8),
            "volume_5m": random.randint(1000, 50000), "holders": random.randint(50, 2000)}

# ---------- RISK ENGINE ----------
def risk_flags(token):
    flags = list(token.get("risk_flags", [ "top10_pct"] > 50: flags.append("top10_over_50pct")
    if token > 20: flags.append("dev_over_20pct")
    if token < 10000: flags.append("liquidity_under_10k")
    if token < 30000: flags.append("liquidity_under_30k")
    if token > 10: flags.append("high_sniper_count")
    return list(set(flags))

def is_confirmed_scam(flags):
    return ("top10_over_50pct" in flags and "dev_over_20pct" in flags and "liquidity_under_10k" in flags)

# ---------- SCORING ----------
def score_token(token, flags):
    s = 50
    s += max(0, 30 - token / 2)          # freshness
    s +=