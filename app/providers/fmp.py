from __future__ import annotations

import logging
import os
import time
from typing import Dict, List, Any, Optional

import requests

FMP_API_KEY = os.getenv("FMP_API_KEY", "").strip()
FMP_BASE = os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com").rstrip("/")
BASE_STABLE = f"{FMP_BASE}/stable"

LOG = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"Accept": "application/json"})
TIMEOUT = (3.05, 20)

# Symbol-level fundamentals change slowly. Cache for hours.
_SYMBOL_CACHE: Dict[str, Dict[str, Any]] = {}
_SUCCESS_TTL = 6 * 3600
_FAILURE_TTL = 45 * 60

# Endpoint-level cooldown.
_ENDPOINT_COOLDOWN: Dict[str, float] = {}
_ENDPOINT_COOLDOWN_TTL = 30 * 60

# Provider-wide cooldown to stop hammering all FMP routes after plan/rate-limit failures.
_PROVIDER_COOLDOWN_UNTIL = 0.0

# Skip company-style fundamentals for common ETF / index-like products.
_ETF_LIKE = {
    "SPY", "QQQ", "IWM", "DIA", "SOXX", "SMH", "VUG", "VTV", "EFA", "EEM", "AGG", "SGOV",
    "XLK", "XLF", "XLE", "XLV", "XLY", "XLP", "XLI", "XLU", "XLB", "XLRE",
    "TLT", "HYG", "LQD", "GLD", "SLV", "ARKK",
}


def _api_key() -> str:
    return (os.getenv("FMP_API_KEY") or "").strip()


def normalize_symbol(sym: str) -> str:
    return sym.upper().strip().replace(".", "-")


def denormalize_symbol(sym: str) -> str:
    return sym.upper().strip().replace("-", ".")


def _extract_error_message(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ("Error Message", "error", "message", "Error", "Information", "Note"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            return _extract_error_message(first)
    if isinstance(payload, str) and payload.strip():
        return payload.strip()
    return None


def _cooldown_active(endpoint: str) -> bool:
    ts = _ENDPOINT_COOLDOWN.get(endpoint)
    return bool(ts and (time.time() - ts) < _ENDPOINT_COOLDOWN_TTL)


def _mark_cooldown(endpoint: str) -> None:
    _ENDPOINT_COOLDOWN[endpoint] = time.time()


def _provider_cooldown_active() -> bool:
    return time.time() < _PROVIDER_COOLDOWN_UNTIL


def _mark_provider_cooldown() -> None:
    global _PROVIDER_COOLDOWN_UNTIL
    _PROVIDER_COOLDOWN_UNTIL = time.time() + _ENDPOINT_COOLDOWN_TTL


def _request_json(
    url: str,
    *,
    params: dict,
    timeout=TIMEOUT,
    symbol: Optional[str] = None,
    endpoint: str = "",
) -> Any:
    if _provider_cooldown_active():
        return None

    if _cooldown_active(endpoint):
        return None

    try:
        r = SESSION.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        LOG.warning("FMP request exception endpoint=%s symbol=%s err=%s", endpoint, symbol, exc)
        return None

    text_snippet = (r.text or "")[:220]

    if r.status_code == 200:
        try:
            payload = r.json()
        except ValueError:
            LOG.warning("FMP invalid JSON endpoint=%s symbol=%s body=%r", endpoint, symbol, text_snippet)
            return None

        err_msg = _extract_error_message(payload)
        if err_msg:
            LOG.warning("FMP API message endpoint=%s symbol=%s msg=%s", endpoint, symbol, err_msg)
            lower = err_msg.lower()
            if any(s in lower for s in ("legacy endpoint", "not supported", "limit", "quota", "upgrade", "payment")):
                _mark_cooldown(endpoint)
                _mark_provider_cooldown()
            return None

        return payload

    if r.status_code in (402, 403, 429):
        LOG.warning(
            "FMP endpoint cooldown endpoint=%s symbol=%s status=%s body=%r",
            endpoint,
            symbol,
            r.status_code,
            text_snippet,
        )
        _mark_cooldown(endpoint)
        _mark_provider_cooldown()
        return None

    LOG.warning(
        "FMP request failed endpoint=%s symbol=%s status=%s body=%r",
        endpoint,
        symbol,
        r.status_code,
        text_snippet,
    )
    return None


def _coerce_first_row(payload: Any, *, endpoint: str, symbol: str) -> dict:
    if isinstance(payload, list):
        if payload:
            row = payload[0]
            if isinstance(row, dict):
                return row or {}
            LOG.warning(
                "FMP unexpected list item endpoint=%s symbol=%s type=%s",
                endpoint,
                symbol,
                type(row).__name__,
            )
            return {}
        LOG.info("FMP empty payload endpoint=%s symbol=%s", endpoint, symbol)
        return {}

    if isinstance(payload, dict):
        if payload:
            return payload
        LOG.info("FMP empty dict payload endpoint=%s symbol=%s", endpoint, symbol)
        return {}

    return {}


def _get_cached(symbol: str) -> Optional[Dict[str, Any]]:
    slot = _SYMBOL_CACHE.get(symbol)
    if not slot:
        return None
    ttl = _SUCCESS_TTL if slot.get("ok") else _FAILURE_TTL
    if (time.time() - slot.get("ts", 0.0)) < ttl:
        return slot
    return None


def _set_cached(symbol: str, ratios: dict, metrics: dict, *, ok: bool) -> None:
    _SYMBOL_CACHE[symbol] = {
        "ts": time.time(),
        "ok": bool(ok),
        "ratios": ratios or {},
        "metrics": metrics or {},
    }


def _fetch_first_row(
    symbol: str,
    *,
    endpoint: str,
    base: str,
    path: str,
    params: Optional[dict] = None,
) -> dict:
    apikey = _api_key()
    if not apikey:
        LOG.warning("Missing FMP_API_KEY (env var not set/loaded)")
        return {}

    s = normalize_symbol(symbol)
    url = f"{base}/{path}"
    q = dict(params or {})
    q.setdefault("apikey", apikey)
    if "{symbol}" in path:
        url = url.format(symbol=s)
    else:
        q.setdefault("symbol", s)

    payload = _request_json(url, params=q, timeout=TIMEOUT, symbol=symbol, endpoint=endpoint)
    return _coerce_first_row(payload, endpoint=endpoint, symbol=symbol)


def _get_fundamentals(symbol: str) -> Dict[str, dict]:
    symbol = denormalize_symbol(symbol)
    normalized = normalize_symbol(symbol)

    if normalized in _ETF_LIKE:
        return {"ratios": {}, "metrics": {}}

    cached = _get_cached(symbol)
    if cached is not None:
        return {"ratios": cached["ratios"], "metrics": cached["metrics"]}

    ratios: Dict[str, Any] = {}
    metrics: Dict[str, Any] = {}

    # Stable non-legacy TTM endpoints
    ratios = _fetch_first_row(
        symbol,
        endpoint="ratios-ttm-stable",
        base=BASE_STABLE,
        path="ratios-ttm",
    )
    metrics = _fetch_first_row(
        symbol,
        endpoint="key-metrics-ttm-stable",
        base=BASE_STABLE,
        path="key-metrics-ttm",
    )

    # Keep this provider lean to reduce rate-limit pressure on Premium plans.
    _set_cached(symbol, ratios, metrics, ok=bool(ratios or metrics))
    return {"ratios": ratios or {}, "metrics": metrics or {}}


def get_profiles(symbols: List[str], chunk: int = 100, sleep_sec: float = 0.12) -> Dict[str, Dict[str, Any]]:
    apikey = _api_key()
    if not apikey:
        LOG.warning("Missing FMP_API_KEY (env var not set/loaded)")
        return {}

    symbols = [s.upper().strip() for s in symbols if s and s.strip()]
    if not symbols:
        return {}

    try:
        url = f"{BASE_STABLE}/profile-bulk"
        payload = _request_json(
            url,
            params={"apikey": apikey},
            timeout=(3.05, 30),
            endpoint="profile-bulk",
        ) or []
        if isinstance(payload, list) and payload:
            want = set(symbols)
            bulk: Dict[str, Dict[str, Any]] = {}
            for row in payload:
                sym = (row.get("symbol") or "").upper().strip()
                if sym in want:
                    bulk[sym] = row
            if bulk:
                return bulk
    except Exception as exc:
        LOG.warning("FMP profile-bulk failed err=%s", exc)

    out: Dict[str, Dict[str, Any]] = {}
    for i in range(0, len(symbols), chunk):
        batch = symbols[i:i + chunk]
        for sym in batch:
            ns = normalize_symbol(sym)
            row = _fetch_first_row(
                sym,
                endpoint="profile",
                base=BASE_STABLE,
                path=f"profile/{ns}",
                params={"apikey": apikey},
            )
            if row:
                key = denormalize_symbol(row.get("symbol") or sym)
                out[key] = row
            time.sleep(sleep_sec)
    return out


def get_ratios_ttm(symbol: str) -> dict:
    return _get_fundamentals(symbol)["ratios"]


def get_key_metrics_ttm(symbol: str) -> dict:
    return _get_fundamentals(symbol)["metrics"]


def clear_fmp_cache() -> None:
    _SYMBOL_CACHE.clear()
    _ENDPOINT_COOLDOWN.clear()
    global _PROVIDER_COOLDOWN_UNTIL
    _PROVIDER_COOLDOWN_UNTIL = 0.0