"""SEC EDGAR connector -- fetches raw Form 4 (insider transaction) filings.

No interpretation happens here: each filing's raw XML goes straight into a
RawObservation. Parsing transaction fields out of it is `signals`' job, same
split as the Polygon connector.

SEC requires a descriptive User-Agent identifying the requester (no API key)
and asks for no more than ~10 requests/second -- see
https://www.sec.gov/os/webmaster-faq#developers
"""

import time
from datetime import date, datetime, timedelta, timezone

import requests

from core.types import RawObservation

USER_AGENT = "Stockpad research tool kane.elfman@gmail.com"
REQUEST_DELAY = 0.15  # seconds between requests -- keeps us well under SEC's ~10 req/s ask
MAX_RETRIES = 3

_HEADERS = {"User-Agent": USER_AGENT}

_cik_cache: dict[str, str] | None = None


def _get(url: str) -> requests.Response:
    delay = 1
    for _ in range(MAX_RETRIES - 1):
        resp = requests.get(url, headers=_HEADERS, timeout=30)
        if resp.status_code in (429, 503):
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
        return resp
    resp = requests.get(url, headers=_HEADERS, timeout=30)
    resp.raise_for_status()
    return resp


def _load_cik_map() -> dict[str, str]:
    global _cik_cache
    if _cik_cache is None:
        resp = _get("https://www.sec.gov/files/company_tickers.json")
        _cik_cache = {row["ticker"]: str(row["cik_str"]) for row in resp.json().values()}
    return _cik_cache


def _cik_for(ticker: str) -> str:
    cik = _load_cik_map().get(ticker)
    if cik is None:
        raise RuntimeError(f"No CIK found for ticker {ticker!r} in SEC's company_tickers.json")
    return cik


def _raw_document_url(cik: str, accession_number: str, primary_document: str) -> str:
    accession_no_dashes = accession_number.replace("-", "")
    # `primaryDocument` from the submissions API often points at an
    # XSL-rendered viewer path (e.g. "xslF345X06/doc4.xml") -- fetching that
    # returns rendered HTML, not the filing. The raw XML sits at the
    # accession root under the same basename.
    filename = primary_document.rsplit("/", 1)[-1]
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{filename}"


def fetch_form4_filings(ticker: str, lookback_days: int) -> list[RawObservation]:
    """Pull raw Form 4 filings for `ticker` from the trailing `lookback_days`."""
    cik = _cik_for(ticker)
    submissions_url = f"https://data.sec.gov/submissions/CIK{int(cik):010d}.json"
    recent = _get(submissions_url).json()["filings"]["recent"]

    cutoff = (date.today() - timedelta(days=lookback_days)).isoformat()
    observations = []
    for i, form in enumerate(recent["form"]):
        if form != "4":
            continue
        report_date = recent["reportDate"][i]
        if report_date < cutoff:
            continue
        doc_url = _raw_document_url(cik, recent["accessionNumber"][i], recent["primaryDocument"][i])
        time.sleep(REQUEST_DELAY)
        doc_resp = _get(doc_url)
        observations.append(
            RawObservation(
                source="sec_edgar_form4",
                ticker=ticker,
                observed_at=report_date,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                payload=doc_resp.text,
            )
        )
    return observations


def fetch_all(tickers: list[str], lookback_days: int) -> dict[str, list[RawObservation]]:
    """Batch entry point: fetch Form 4 filings for every ticker in the watchlist."""
    observations = {}
    for ticker in tickers:
        observations[ticker] = fetch_form4_filings(ticker, lookback_days)
        print(f"fetched {ticker}: {len(observations[ticker])} Form 4 filings", flush=True)
        time.sleep(REQUEST_DELAY)
    return observations
