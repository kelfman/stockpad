"""Polygon.io connector -- fetches raw daily bars, nothing else.

No interpretation happens here: the raw vendor response goes straight into a
RawObservation. Turning it into a price series and computing anything from
it is `signals`' job (see the README pipeline: Normalise lives in signal
generation, not ingestion).
"""

import os
import time
from datetime import date, datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from core.types import RawObservation

load_dotenv()

POLYGON_API_KEY = os.environ["POLYGON_API_KEY"]

LOOKBACK_DAYS = 400  # comfortably over a year of daily bars once resampled to weekly
MAX_RETRIES = 6


def fetch_daily_bars(ticker: str) -> RawObservation:
    """Pull raw daily bars for `ticker` over the last LOOKBACK_DAYS, unmodified."""
    end = date.today()
    start = end - timedelta(days=LOOKBACK_DAYS)
    url = (
        f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/day/"
        f"{start.isoformat()}/{end.isoformat()}"
    )
    delay = 5
    for _ in range(MAX_RETRIES):
        resp = requests.get(
            url,
            params={"adjusted": "true", "sort": "asc", "limit": 5000, "apiKey": POLYGON_API_KEY},
            timeout=30,
        )
        if resp.status_code == 429:
            time.sleep(int(resp.headers.get("Retry-After", delay)))
            delay *= 2
            continue
        resp.raise_for_status()
        payload = resp.json()
        if payload.get("resultsCount", 0) == 0:
            raise RuntimeError(f"Polygon returned no bars for {ticker}: {payload}")
        last_bar_date = datetime.fromtimestamp(
            payload["results"][-1]["t"] / 1000, tz=timezone.utc
        ).date()
        return RawObservation(
            source="polygon",
            ticker=ticker,
            observed_at=last_bar_date.isoformat(),
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )
    raise RuntimeError(f"Polygon rate limit not cleared after {MAX_RETRIES} retries for {ticker}")


def fetch_all(tickers: list[str]) -> dict[str, RawObservation]:
    """Batch entry point: fetch raw daily bars for every ticker."""
    observations = {}
    for ticker in tickers:
        observations[ticker] = fetch_daily_bars(ticker)
        print(f"fetched {ticker}", flush=True)
    return observations
