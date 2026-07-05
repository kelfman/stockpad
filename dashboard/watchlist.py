"""Ticker watchlist view: insider cluster signals alongside sector context.

Basic form per Slice 2 -- a table, same spirit as the sector ranked table.
"""


def render(tickers: list[dict], sector_lookup: dict) -> str:
    lines = ["Insider cluster-buy watchlist", ""]

    header = f"{'Ticker':<7}{'Sector':<7}{'Insiders':>9}  {'Pctl':>5}  {'Conf':<6}Sector context"
    lines.append(header)
    lines.append("-" * len(header))
    for t in tickers:
        sig = t["signal"]
        conf = "yes" if sig.confirmed else "--"
        sector_etf = t["sector_etf"]
        sector = sector_lookup.get(sector_etf)
        sector_note = f"{sector_etf} {sector['quadrant']}" if sector else f"{sector_etf} (no sector data)"
        lines.append(
            f"{t['ticker']:<7}{sector_etf:<7}{t['latest_count']:>9}  {t['percentile']:>5}  {conf:<6}{sector_note}"
        )

    lines.append("")
    lines.append("Signals:")
    for t in tickers:
        sig = t["signal"]
        state = "confirmed" if sig.confirmed else "unconfirmed"
        lines.append(f"  [{sig.direction} · {state} · p{sig.percentile_vs_history}] {sig.descriptor}")

    return "\n".join(lines)
