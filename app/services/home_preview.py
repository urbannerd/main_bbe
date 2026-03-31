from datetime import datetime, timezone
import os
import requests

FMP_BASE = "https://financialmodelingprep.com"


def _fmp_key() -> str:
    return (os.getenv("FMP_API_KEY") or "").strip()


def fetch_spy_quote() -> dict:
    api_key = _fmp_key()

    if not api_key:
        return {
            "price": "--",
            "changePercent": "",
            "trend": "Live chart",
            "context": "Missing FMP API key",
            "strength": 30,
        }

    try:
        response = requests.get(
            f"{FMP_BASE}/stable/quote",
            params={"symbol": "SPY", "apikey": api_key},
            timeout=(3.05, 10),
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, list) or not payload:
            raise ValueError("Empty quote payload")

        row = payload[0]
        price = row.get("price")
        change = (
            row.get("changesPercentage")
            or row.get("changePercentage")
            or row.get("change_percent")
            or row.get("changes_percent")
        )
        volume = row.get("volume")

        price_str = f"{price:.2f}" if isinstance(price, (int, float)) else "--"

        if isinstance(change, (int, float)):
            sign = "+" if change >= 0 else ""
            change_str = f"{sign}{change:.2f}%"
        else:
            change_str = ""

        strength = 45
        if isinstance(volume, (int, float)):
            if volume > 50_000_000:
                strength = 80
            elif volume > 20_000_000:
                strength = 65

        return {
            "price": price_str,
            "changePercent": change_str,
            "trend": "Tracking SPY live",
            "context": "Market context for trend, structure, and reaction",
            "strength": strength,
        }

    except Exception as exc:
        return {
            "price": "--",
            "changePercent": "",
            "trend": "Live chart",
            "context": f"Preview unavailable: {type(exc).__name__}",
            "strength": 30,
        }


def fetch_tracked_quotes() -> list[dict]:
    api_key = _fmp_key()
    symbols = ["TSLA", "NVDA", "AAPL"]

    if not api_key:
        return [{"symbol": s, "price": "--"} for s in symbols]

    results = []

    for symbol in symbols:
        try:
            response = requests.get(
                f"{FMP_BASE}/stable/quote",
                params={
                    "symbol": symbol,
                    "apikey": api_key
                },
                timeout=(3.05, 10),
            )

            response.raise_for_status()
            payload = response.json()

            if isinstance(payload, list) and payload:
                price = payload[0].get("price")

                results.append({
                    "symbol": symbol,
                    "price": f"${price:.2f}" if isinstance(price, (int, float)) else "--"
                })
            else:
                results.append({
                    "symbol": symbol,
                    "price": "--"
                })

        except Exception:
            results.append({
                "symbol": symbol,
                "price": "--"
            })

    return results

def build_impulse_snapshot() -> dict:
    quotes = fetch_tracked_quotes()

    rows = []
    labels = {
        "TSLA": {"openLabel": "volume spike", "openTag": "Vol x3"},
        "NVDA": {"openLabel": "momentum", "openTag": "Breakout"},
        "AAPL": {"openLabel": "fade", "openTag": "Reversal"},
    }

    for q in quotes:
        symbol = q["symbol"]
        meta = labels.get(symbol, {"openLabel": "tracked", "openTag": "Tracked"})
        rows.append({
            "symbol": symbol,
            "price": q["price"],
            "openLabel": meta["openLabel"],
            "openTag": meta["openTag"],
            "closedLabel": "after hours",
            "closedTag": "Tracked",
        })

    return {
        "rows": rows,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }


def build_home_preview() -> dict:
    return {
        "spy": fetch_spy_quote(),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
    }