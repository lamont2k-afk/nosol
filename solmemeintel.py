import os, time, json, random
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# ---------- CONFIG ----------
USE_MOCK = False          # flip to True to go back to demo data
USE_DEXSCREENER = True    # free, no key needed
SCAN_INTERVAL_SEC = 300   # 5 min between scans in production

# ---------- DEXSCREENER FEED (free, no API key) ----------
def fetch_dexscreener_solana(limit=10):
    """Pull trending/new Solana pairs from DexScreener. No key required."""
    if not HAS_REQUESTS:
        return []
    try:
        # Search for pump.fun pairs on Solana - catches fresh launches
        r = requests.get(
            "https://api.dexscreener.com/latest/dex/search?q=pump.fun",
            headers={"User-Agent": "SolMemeIntel/1.0"},
            timeout=20,
        )
        if r.status_code != 200:
            print(f"  DexScreener status {r.status_code}")
            return []
        pairs = r.json().get("pairs", [])
        out = []
        for p in pairs:
            if p.get("chainId") != "solana":
                continue
            bt = p.get("baseToken", {})
            liq = (p.get("liquidity") or {}).get("usd") or 0
            mcap = p.get("marketCap") or 0
            txns = p.get("txns") or {})
            h24 = txns.get("h24") or {})
            buys = h24.get("buys") or 0
            sells = h24.get("sells") or 0
            created = p.get("pairCreatedAt") or 0
            age_min = max(1, int((time.time() * 1000 - created) / 60000)) if created else 9999
            # DexScreener doesn't expose dev/sniper/top10 directly - those need
            # GMGN or on-chain parsing. We flag what we can see.
            flags = []
            if liq < 10000:
                flags.append("liquidity_under_10k")
            if liq < 30000:
                flags.append("liquidity_under_30k")
            if buys and sells and sells > buys * 2:
                flags.append("sell_pressure")
            out.append({
                "symbol": bt.get("symbol", "?"),
                "address": bt.get("address", ""),
                "age_min": age_min,
                "mcap": mcap,
                "liquidity": liq,
                "dev_pct": None,      # not available from DexScreener
                "snipers": None,      # not available
                "top10_pct": None,    # not available
                "buys_24h": buys,
                "sells_24h": sells,
                "risk_flags": flags,
                "source": "dexscreener",
            })
        out.sort(key=lambda x: x["age_min"])
        return out[:limit]
    except Exception as e:
        print(f"  DexScreener error: {e}")
        return []

# ---------- MOCK DATA (fallback) ----------
def mock_gmgn_launches():
    return [
        {"symbol": "PEPE2", "age_min": 60, "mcap": 185000, "liquidity": 45000,
         "dev_pct": 4, "snipers": 3, "top10_pct": 22, "risk_flags": []},
        {"symbol": "AIAGENT", "age_min": 25, "mcap": 120000, "liquidity": 18000,
         "dev_pct": 9, "snipers": 6, "top10_pct": 38, "risk_flags": ["liquidity_under_30k"]},
        {"symbol": "WIF2", "age_min": 15, "mcap": 80000, "liquidity": 8500,
         "dev_pct": 22, "snipers": 11, "top10_pct": 61,
         "risk_flags": ["top10_over_50pct", "dev_over_20pct", "liquidity_under_10k"]},
    ]

def mock_x_narratives():
    return [
        {"theme": "AI agents", "mentions": 340, "kol_mentions": 12, "momentum": "accelerating"},
        {"theme": "cat memes", "mentions": 210, "kol_mentions": 5, "momentum": "flat"},
        {"theme": "political", "mentions": 90, "kol_mentions": 2, "momentum": "declining"},
        {"theme": "anime", "mentions": 150, "kol_mentions": 7, "momentum": "emerging"},
    ]

# ---------- RISK ENGINE ----------
def risk_flags(token):
    flags = list(token.get("risk_flags", []))
    # Only apply thresholds when the data actually exists
    if token.get("top10_pct") is not None and token["top10_pct"] > 50:
        flags.append("top10_over_50pct")
    if token.get("dev_pct") is not None and token["dev_pct"] > 20:
        flags.append("dev_over_20pct")
    if token.get("snipers") is not None and token["snipers"] > 10:
        flags.append("high_sniper_count")
    return list(set(flags))

def is_confirmed_scam(flags):
    # Requires all three signals - only possible with GMGN-level data
    return ("top10_over_50pct" in flags and "dev_over_20pct" in flags
            and "liquidity_under_10k" in flags)

# ---------- SCORING ----------
def score_token(token, flags):
    s = 50
    # Freshness: newer = higher (cap at 30 for tokens under 1 min old)
    age = token.get("age_min") or 9999
    s += max(0, 30 - min(age, 60) / 2)
    # Liquidity quality
    liq = token.get("liquidity") or 0
    s += min(20, liq / 5000)
    # Dev penalty (only if known)
    if token.get("dev_pct") is not None:
        s -= token["dev_pct"]
    # Concentration penalty (only if known)
    if token.get("top10_pct") is not None:
        s -= token["top10_pct"] / 2
    # Risk penalty
    s -= len(flags) * 5
    # Buy/sell pressure bonus/penalty
    buys = token.get("buys_24h") or 0
    sells = token.get("sells_24h") or 0
    if buys + sells > 0:
        ratio = buys / (buys + sells)
        if ratio > 0.6:
            s += 5
        elif ratio < 0.4:
            s -= 5
    return max(0, min(100, round(s)))

# ---------- MAIN LOOP ----------
def main():
    mode = "MOCK" if USE_MOCK else "LIVE (DexScreener)"
    print(f"SolMemeIntel starting - {mode} mode")
    print(f"Scanning every {SCAN_INTERVAL_SEC}s. Ctrl+C to stop.")
    if not HAS_REQUESTS and not USE_MOCK:
        print("WARNING: requests library not installed. Run: pip install requests")
        print("Falling back to mock data.")
    while True:
        if USE_MOCK or not HAS_REQUESTS:
            launches = mock_gmgn_launches()
            narratives = mock_x_narratives()
        else:
            launches = fetch_dexscreener_solana(limit=10)
            narratives = []  # X feed still mocked
            if not launches:
                print("  No live data returned - check connection or rate limits")
        print(f"--- SCAN {datetime.now():%H:%M:%S} ---")
        for t in launches:
            flags = risk_flags(t)
            sc = score_token(t, flags)
            status = "NO TRADE" if is_confirmed_scam(flags) else f"SCORE {sc}/100"
            dev = f"{t['dev_pct']}%" if t.get("dev_pct") is not None else "n/a"
            top10 = f"{t['top10_pct']}%" if t.get("top10_pct") is not None else "n/a"
            print(f"  {t['symbol']:8s} mcap=${t['mcap']:>9,.0f} liq=${t['liquidity']:>8,.0f} "
                  f"age={t['age_min']:>5}m dev={dev:>4} top10={top10:>4} "
                  f"flags={flags or '-'} -> {status}")
        for n in narratives:
            if n["momentum"] in ("accelerating", "emerging") and n["kol_mentions"] >= 5:
                print(f"  {n['momentum'].upper()} - {n['theme']} "
                      f"({n['mentions']} mentions, {n['kol_mentions']} KOLs)")
        print()
        time.sleep(SCAN_INTERVAL_SEC)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped. Bot never touched a wallet - research only.")
