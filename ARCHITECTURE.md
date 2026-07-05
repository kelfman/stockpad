# StockPad — System Decomposition

Companion to [README.md](README.md). The README describes the product and design vision; this document breaks the system into separate projects that interface together, so no single piece has to be fully built (or fully understood) before another can start.

Boundaries here are drawn on genuine differences — lifecycle (how often something runs and how it's deployed), ownership of meaning (who decides what data *means* vs who just fetches it), and rate of change (what you'll rewrite weekly vs what should barely change once it works) — not on topic area alone. A bug fix doesn't need a new project; a component with a different deploy cadence or a different reason to change does.

---

## The projects

### 1. `connectors` — gets raw data in, nothing else

A scheduled batch runner for everything pulled on a cadence: daily price bars (Polygon), EDGAR filings, 13F, AAII, sector ETF flows, options flow pulls, alt-data (LinkedIn headcount, job postings, patents, Google Trends).

There is deliberately no streaming mode. The tool reads the market at a weeks-to-quarters resolution (see README), and daily cadence covers that fully. If intraday data ever earns a place, a long-running stream process is the seam to add as a separate entry point — don't build it speculatively.

**Emits:** `RawObservation` — deliberately dumb, no interpretation:

```json
{
  "source": "unusual_whales",
  "ticker": "XYZ",
  "observed_at": "2026-07-05T14:32:00Z",
  "retrieved_at": "2026-07-05T14:32:04Z",
  "payload": { "...": "vendor-specific, unmodified" }
}
```

**Why separate:** vendor APIs change on their own schedule and break independently of everything downstream. When a vendor changes their response shape, you fix one file — signal logic and everything above it is untouched.

---

### 2. `documents` — long-form text → retrievable knowledge

Ingests filings, earnings transcripts, news, Reddit DD; chunks, embeds, stores in pgvector; serves semantic search and filing-to-filing diffs.

**Interface:**
```
search(ticker, query) → passages[]
diff(ticker, formType) → language changes vs prior filing
```

**Why separate:** a completely different tech lifecycle (embedding models, chunking strategy) from time-series signal data, and useful standalone — "what has management said about margin pressure across six quarters" shouldn't require any live signal state to answer.

---

### 3. `signals` — the interpretation layer

**This is the most important boundary in the system.** Reads `RawObservation`s, applies the descriptor heuristics (e.g. 3+ insiders buying within 30 days = a confirmed bullish cluster at the 98th percentile of that name's history), and produces the *only* object type everything downstream is allowed to consume. The shape is generic across grains — a sector-level signal and a ticker-level signal are the same object with a different `subject_type`:

```json
{
  "subject_type": "sector",
  "subject": "XLF",
  "source": "relative_strength_ratio",
  "direction": "bullish",
  "percentile_vs_history": 88,
  "confirmed": true,
  "descriptor": "XLF/SPY ratio bottomed and has curled upward for 3 consecutive weeks",
  "as_of": "2026-07-01",
  "staleness": "fresh"
}
```

```json
{
  "subject_type": "ticker",
  "subject": "XYZ",
  "source": "insider_form4",
  "direction": "bullish",
  "percentile_vs_history": 98,
  "confirmed": true,
  "descriptor": "3 insiders bought within a 12-day window, first cluster buy in 18 months",
  "as_of": "2026-06-20",
  "staleness": "fresh"
}
```

`percentile_vs_history` is where the underlying measurement sits within that signal's own history — a measured quantity, with the comparison window defined per source. `confirmed` is the per-source threshold call (e.g. 3 consecutive weeks for a turn). What no signal carries is a *weight*: combining across signals downstream is a count, never a sum.

Sector rotation logic (relative strength ratio turns, breadth, flow acceleration) lives here too, as sector-level signals rather than a separate project — it's the same job at a different granularity: raw data in, qualitative read out. Because sector rotation is the first area being built (see Build order below), the `subject_type` split needs to exist from the first `core` commit rather than being retrofitted once a ticker-level signal shows up.

One consequence of the dashboard's time-scrubbing and drill-down promises: `signals` serves the current descriptor *and* the derived series behind it (the full RS-Ratio/RS-Momentum track, breadth history). That's still interpretation-layer output — derived, not raw — so it doesn't breach the seal on raw observations.

**Why separate:** this is the only place the "descriptors, not scores" discipline from the README is enforced *in code*, not just by convention. If `synthesis` or `dashboard` could reach past this layer to raw numbers, it becomes possible — at 2am, wanting "just a quick composite score" — to quietly reintroduce fake precision. Enforce it structurally: nothing downstream gets a connection to raw observations, only to signals.

---

### 4. `synthesis` — the AI reconciliation layer

Takes a ticker's current signals, sector context, and retrieved documents; calls Claude; returns the plain-English thesis.

**Interface:**
```
GET /synthesis/{ticker}
→ { thesis, conflicts[], confidence_read }
```

**Why separate:** prompt and reconciliation logic will iterate weekly; it shouldn't be entangled with ingestion code that should barely change once a connector works. Also the one place worth explicitly enforcing "timestamp every claim" — a 90-day-stale 13F signal should never get narrated with the same apparent confidence as a same-day options print.

---

### 5. `log` — the research log

The epistemic check on everything above. Records dated, falsifiable reads — what you think is happening, what should follow if you're right, and a date by which it should show up — with a snapshot of the signal state that informed the read. When a read's horizon passes it comes due for grading against what actually happened, before hindsight can rewrite it. No positions, no P&L: the unit of record is a read, not a trade.

**Interface:**
```
POST /reads          { subject, thesis, expectation, horizon_date, signals_snapshot }
GET /reads/due       → reads past their horizon date, not yet graded
PATCH /reads/{id}    { outcome_note, grade }   # right | mixed | wrong
```

**Why separate:** it's the mechanism that keeps the rest of the system honest, so it must not depend on the AI layer or a scraper being healthy to keep working. Deliberately the dumbest, most durable component in the system. Starts life as a dated markdown file today; becomes a service only when the dashboard needs to read it.

---

### 6. `dashboard` — pure consumer

React + D3. Fans out to `signals`, `synthesis`, `documents`, and `log` directly. No aggregator/BFF layer for now — one user, four small APIs, not worth the extra deployable until it's genuinely annoying not to have one.

---

### 7. `core` — shared contract, not a service

Just the `Signal`, `RawObservation`, and `Read` type definitions, the ticker/sector taxonomy, and the direction enum (`bullish | bearish | neutral`). Every project imports this so the contract can't drift between them.

---

## Build order

1. `log` — start today, as a dated markdown file of falsifiable reads; no code, and nothing else blocks on it
2. `core` — trivial, needed by everything; ship the `Signal` shape generalized (`subject_type: sector | ticker`) from the start, not retrofitted later
3. `connectors` (batch: daily sector ETF closes via Polygon for relative-strength ratios vs SPY; ETF flow data via ETF.com/VettaFi scrape after)
4. `signals` — get one real sector-level descriptor (relative-strength ratio turn) flowing end to end, then extend across all 11 GICS sectors
5. `dashboard` — a ranked table of sectors by momentum + RS trend, no D3 yet
6. `connectors` + `signals` (ticker-level: Form 4 insider cluster buys — free, same shape as the sector signals from step 4)
7. `documents` + `synthesis` — now that a sector-level and a ticker-level signal both exist, reconcile them: the first real synthesis output is the "sector tailwind confirmed" / "sector rotation working against it" example already in the README
8. `connectors` (paid options flow — last, once the system has proven useful without it)

Every step after the first has to clear the same bar: it changes what the system tells you about the market the week it lands. A step that only produces plumbing is mis-scoped. The value is also not evenly distributed — `synthesis` is the differentiated core (nothing off the shelf reconciles filing language against positioning against sector context), while the connectors and the RRG math are commodity, worth building in-house mainly for what the construction teaches. Build the commodity parts cheap and resist gold-plating them.

This supersedes the README's Build Phases section, which has been updated to match. Sector rotation was picked as area #1 over Form 4 deliberately — it's the area worth building real intuition for first, not just the cheapest one to stand up. The payoff of the `subject_type`-generic contract from step 2: adding the ticker-level signal in step 6 touches zero code from steps 2-5.

---

## Deployment reality check

Don't stand these up as seven separately-deployed services. Run it as a monorepo — one Postgres instance, one repo, each project as its own package/directory with its own entry point — and only split into actually-separate deployments when an operational need forces it (the batch connector wanting to run on a cloud scheduler instead of a laptop is the likely first candidate).

The value of the split right now is **interface discipline** (no cheating past `signals` to raw numbers) and **independent iteration speed** (rewrite the AI prompts without touching the EDGAR parser) — not infrastructure isolation. Literal microservices would be premature for a system built and operated by one person.
