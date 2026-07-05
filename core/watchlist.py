"""Ticker-level watchlist: which names to track, and their sector ETF for context."""

WATCHLIST = {
    "JPM": "XLF",
    "ZION": "XLF",
    "DE": "XLI",
    "VST": "XLU",
    "MU": "XLK",
    # Added to seed the synthesis slice with real material: both had confirmed
    # open-market insider clusters (3+ distinct buyers within our 12-day window)
    # as of 2026-07, in sectors we already track -- so there is an actual
    # informed-money read to reconcile against sector context, not five quiet
    # names. Discovered via OpenInsider, validated through our own EDGAR pipeline.
    "KMX": "XLY",   # CarMax -- 5 insiders bought late June 2026
    "LILA": "XLC",  # Liberty Latin America -- cluster incl. John Malone
}
