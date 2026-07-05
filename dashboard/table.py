"""Sector rotation heatmap, Slice 1 form: a ranked table, no D3 yet.

Ranking is a presentation concern -- signals hands back one descriptor per
sector, dashboard decides how to sort and lay them out for the reader.
"""

QUADRANT_ORDER = {"Leading": 0, "Improving": 1, "Weakening": 2, "Lagging": 3}


def sort_sectors(sectors: list[dict]) -> list[dict]:
    return sorted(sectors, key=lambda s: (QUADRANT_ORDER[s["quadrant"]], -s["rs_momentum"]))


def render(sectors: list[dict], benchmark: str, as_of: str) -> str:
    lines = [f"Sector rotation vs {benchmark} -- as of {as_of}", ""]

    header = (
        f"{'Sector':<7}{'Name':<24}{'Quadrant':<11}{'Wks':>4}  "
        f"{'Heading':<17}{'RS-Ratio':>9}{'RS-Mom':>8}{'Pctl':>6}  {'Conf'}"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for s in sectors:
        conf = "yes" if s["signal"].confirmed else "--"
        lines.append(
            f"{s['ticker']:<7}{s['name']:<24}{s['quadrant']:<11}{s['weeks_in_quadrant']:>4}  "
            f"{s['heading']:<17}{s['rs_ratio']:>9.1f}{s['rs_momentum']:>8.1f}"
            f"{s['momentum_percentile']:>6}  {conf}"
        )

    lines.append("")
    lines.append("Signals:")
    for s in sectors:
        sig = s["signal"]
        state = "confirmed" if sig.confirmed else "unconfirmed"
        lines.append(f"  [{sig.direction} · {state} · p{sig.percentile_vs_history}] {sig.descriptor}")

    return "\n".join(lines)
