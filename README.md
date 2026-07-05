# StockPad — Market Intelligence Dashboard
## Project Brief & Architecture Seed Document

---

## Project Vision

Build a personal market intelligence dashboard that aggregates data across market signals, long-form sources, and qualitative intelligence layers — synthesised by AI into a clear, honest read of what's actually happening in a name or sector, and why. This is a tool for building market understanding, not a trading system: no entry/exit calls, no trade tracking. The insight is meant to inform choices made elsewhere, not to make them.

The tool reads the market at a **weeks-to-quarters resolution** — the horizon at which understanding compounds, and the horizon of the choices it will inform. Anything that only matters intraday (execution timing, tape reading) is out of scope by design, not by omission.

The core problem most dashboards fail to solve: they aggregate data without a *thesis layer*. The goal is a system that tells you where informed money is, where sentiment is, and what the technicals say — then uses AI to reconcile conflicts between those layers into a plain-English picture of what's going on.

---

## The Three-Layer Mental Model

Think in three groups when reading the market:

1. **Informed money** — insiders, institutions, options flow. Watch what they *do*, not what they say. This is the group most worth understanding.
2. **Reactive money** — trend-following funds, momentum ETFs. They amplify moves already in motion.
3. **The herd** — retail, late FOMO buyers. By the time they're in, the move is usually mature. Their crowding is often an *exit* signal, not an entry.

The system's job: see group 1 moving before group 2 amplifies it and the narrative catches up — and recognise group 3 piling in for what it is: a sign the move is mature.

---

## Data Sources — Full Inventory

### Layer 1: Market Signals

| Source | Signal | Lag | Cost |
|---|---|---|---|
| Polygon.io / Alpaca | Price, volume, OHLC (daily bars) | EOD | Free tier |
| Unusual Whales | Options flow, dark pool prints | Minutes | ~$50-60/mo |
| Tradier | Options flow (lighter) | Minutes | Cheaper alt |
| FINRA short interest | Short interest, days-to-cover | Bi-monthly | Free |
| Fintel / Ortex | Real-time short data | Daily | Paid |
| CBOE put/call ratio | Equity P/C, index P/C | Daily | Free |
| AAII sentiment survey | Bull/bear spread | Weekly | Free |
| CNN Fear & Greed | Composite sentiment | Daily | Free |

**Options flow is Tier 1** — not for its speed, but for what it reveals. Large call sweeps on a quietly consolidating ticker, 2 standard deviations above average activity, is informed positioning showing its hand before any narrative exists. Read it for *who is positioned and how*, not as a timing trigger.

---

### Layer 2: Long-Form Documents

| Source | Signal type | Access |
|---|---|---|
| SEC EDGAR (10-K, 10-Q, 8-K) | Filing language, risk factor changes | Free API |
| SEC EDGAR Form 4 | Insider transactions | Free API |
| SEC EDGAR 13F | Institutional positioning (quarterly) | Free API |
| Earnings call transcripts | Management tone, guidance language | Scrape / Refinitiv |
| Analyst reports | PT changes, estimate revisions, rating changes | Broker access / SA |
| FOMC minutes / Fed communications | Macro regime | Free |
| News full articles | Story development ahead of price | NewsAPI ~$50/mo |
| Reddit DD posts (r/SecurityAnalysis) | Thesis development | Free API |
| Investor day / conference presentations | Forward guidance, IR pages | Scrape |

**AI processing for long-form:**
- **Delta analysis** — diff current 10-Q vs prior 10-Q, surface meaningful language changes
- **Tone mapping** — management confidence, hedging frequency, forward-looking language density
- **Thesis extraction** — from analyst reports or DD posts: bull thesis, bear thesis, key assumptions
- **Contradiction detection** — management says demand is strong but capex guidance cut
- **Catalyst identification** — what events does the filing suggest are coming

---

### Layer 3: Qualitative Intelligence

| Source | Signal type | Lag | Cost |
|---|---|---|---|
| 13F filings (EDGAR) | Institutional positioning delta | 45-90 days | Free |
| Tegus / AlphaSense | Expert network call transcripts | Days-weeks | ~$500+/mo |
| People Data Labs API | LinkedIn headcount by department | Real-time | Affordable |
| Job postings scrape | Hiring direction = investment direction | Real-time | Scrape / Thinknum |
| USPTO patent API | R&D direction signals | Weeks | Free |
| OpenInsider | Insider cluster buys | Real-time | Free |
| Google Trends | Retail crowding / late-stage detection | Daily | Free |
| SimilarWeb API | Web traffic as demand proxy | Weekly | Paid |
| Glassdoor / Blind | Employee sentiment pre-earnings | Variable | Scrape (ToS grey) |

**Key 13F managers to track** (publicly known records):
- Druckenmiller (Duquesne Family Office)
- Ackman (Pershing Square)
- Tepper (Appaloosa)
- Burry (Scion — concentrated, contrarian)
- Einhorn (Greenlight)
- Pabrai (Pabrai Funds — Buffett-style, concentrated)
- Klarman (Baupost — rare filer, high conviction)

**13F signal logic:**
- New positions = high conviction entry
- Position sizing increase = adding conviction
- Simultaneous exit by multiple managers = meaningful distribution
- Multi-quarter build = long-term conviction; won't fold on a 5% dip

**Alternative data signals worth building:**
- LinkedIn headcount: Engineering hiring surge = product investment. Sales team shrinking = demand problem.
- Job postings: 40 ML engineer roles = building seriously, not exploring
- Patent cluster filings in a new area = R&D direction shift before any announcement
- Google Trends spike on a ticker = late-stage retail crowding (often an exit signal)

**Financial journalists to track (byline-level, not just publication):**
- David Faber (CNBC) — M&A scoops
- WSJ Heard on the Street — activist situations, corporate governance
- Semafor Business / The Information — tech sector
- Reuters Breaking Views — deal flow

Track *when* a journalist who covers a sector starts publishing "scene-setter" pieces — something is usually developing.

---

## Layer 4: Sector Rotation

Institutions don't sell and sit in cash — they *rotate*. The sector being bought starts showing relative strength before the broader narrative catches up. The goal is to see redeployment happening, not read about it after.

### Primary Signals

| Source | Signal | Lag | Cost |
|---|---|---|---|
| ETF.com / VettaFi | Sector ETF daily/weekly net flows | Daily | Free / scrapeable |
| Polygon.io daily bars | Sector ETF relative strength vs SPY (computed in-house) | EOD | Free tier |
| Finviz heatmap | Breadth within sectors (how many names participating) | Real-time | Free |
| Stockcharts | Sector breadth indicators | Daily | Free tier |
| CBOE VIX | Risk-on/risk-off regime | Real-time | Free |

**Flow acceleration matters more than absolute size** — a sector seeing increasing inflows over 2-3 consecutive weeks is more meaningful than a single large day.

**Price/flow divergence** — a sector ETF with flat or declining price but rising inflows = quiet accumulation.

**Relative strength ratio turn** — plot XLF/SPY, XLK/SPY etc. on a weekly chart. The *turn* in the ratio (bottoming and curling upward) is the rotation signal, not the absolute level.

**Breadth confirmation** — an ETF up 3% driven by 4 of 20 names is concentrated and fragile. 15 of 20 names participating = genuine rotation.

### Sector Leading Indicators

Each sector has specific data that tends to lead price:

| Sector ETF | Leading signal |
|---|---|
| XLF — Financials | Yield curve steepening, credit spreads narrowing |
| XLE — Energy | Oil futures curve, rig count, inventory data |
| XLB — Materials | Copper price, China PMI |
| XLI — Industrials | ISM manufacturing, freight/shipping rates |
| XLK — Technology | Semiconductor book-to-bill ratio, earnings revision momentum |
| XLV — Healthcare | FDA calendar, clinical trial readouts |
| XLY — Consumer Disc | Retail sales, credit card spend data |
| XLP — Consumer Staples | Defensive inflows (risk-off signal) |
| XLU — Utilities | Rate expectations (inverse), defensive positioning |
| XLRE — Real Estate | Rate expectations, housing starts |
| XLC — Communications | Ad spend data, streaming subscriber trends |

Knowing these lets you anticipate rotation *before* ETF flows confirm it — e.g. yield curve steepening + credit spread tightening → financials rotation likely incoming.

### Business Cycle Framework

Sectors rotate with the economic cycle in a historically consistent pattern (not a rigid clock, but a useful prior):

```
Early cycle    → Financials, Consumer Discretionary, Industrials
Mid cycle      → Technology, Materials, Energy
Late cycle     → Energy, Materials, Healthcare
Recession      → Utilities, Consumer Staples, Healthcare
```

Cycle position indicators: Fed policy direction, yield curve shape, credit conditions, ISM manufacturing PMI.

### Tactical Rotation Signals

- **Risk-on/off ratio** — XLY/XLP ratio rising = risk appetite. Falling = defensive rotation. More sensitive than VIX alone.
- **Earnings season rotation** — sectors reporting strong results early in season often see inflows rotate to the next sector up to report
- **Commodity-driven** — oil spike → XLE + XLB. Rate move → XLF (up) and XLRE (direction depends on move size)
- **Dollar strength** — strong USD hurts multinationals (XLK, XLI global revenue), helps domestic-focused sectors

### How Sector Rotation Weights Individual Ticker Signals

Sector rotation is a **context multiplier** on per-ticker signals, not a standalone signal. A strong insider buy on an energy name means more when XLE flows are accelerating. The same signal in a sector showing outflows and deteriorating relative strength warrants caution.

AI synthesis output example: *"This signal is in a sector currently seeing institutional inflows and improving relative strength — sector tailwind confirmed"* vs *"Strong ticker signal but sector rotation is working against it — worth treating with more scepticism until the sector context turns."*

---

## Signal Descriptors

Two kinds of honesty govern how signals are represented, and they pull in opposite directions:

- **Precision of measurement** — often genuinely high. "RS ratio rising 5 consecutive weeks" and "3 insiders bought within 12 days, largest cluster in 18 months" are measured facts. Showing them continuously isn't false precision; it's the truth.
- **Confidence in interpretation** — genuinely low. Whether that cluster buy *means* something bullish, and how much, is uncalibrated judgment.

The discipline: **precise about what was measured, humble about what it means.** Coarseness is not a costume for humility — quantizing a measured value into four steps discards information without adding honesty.

Each data source produces a **descriptor** with three parts:

1. **Direction** — bullish / bearish / neutral. A genuine category, not a coarsened number.
2. **Measured extremity** — where the current reading sits within the signal's *own history*, as a percentile. No invented calibration required: "call activity at the 96th percentile of this name's 2-year range" is a measurement, not an opinion. Signals that require a threshold call also carry a **confirmed** flag — a turn either has its 3 consecutive weeks or it doesn't.
3. **Plain-English read** — the primary carrier of meaning and the only place interpretation lives. All the humility goes here, where it can hold nuance no number can: "sweeps can be hedges, not directional bets."

What stays forbidden is **combining signals into composite scores**. A weight like "+0.8 for insider cluster buy" implies a calibration that doesn't exist — invented precision, not measured precision. Cross-signal confluence is always a count ("3 of 5 sources bullish"), never a weighted sum. Until the research log accumulates enough graded reads to ground weights in real outcomes, nothing gets to pretend otherwise.

Examples:

| Signal | Direction | Read |
|---|---|---|
| Insider cluster buy (3 insiders, 12 days) | Bullish | 98th pctile of cluster activity vs this name's history — rare and hard to fake |
| Unusual call sweeps | Bullish | 96th pctile vs 2-year range — notable, but sweeps can be hedges, not directional bets |
| Short interest rising into price strength | Bearish | 71st pctile — worth flagging, easy to misread without more context |
| AAII bears >40% (contrarian) | Bullish | 93rd pctile of bearishness — extremes have preceded bounces, but timing is loose |
| Reddit mention volume spike | Bearish (crowding) | 97th pctile — a lagging tell that retail has arrived, not a timing signal |
| 13F: multiple top managers added position | Bullish | 45-90 days stale — describe as "was true last quarter," not "is true now" |
| Management hedging language increase QoQ | Bearish | Hedging density at 88th pctile of the last 8 calls — needs the actual quotes surfaced |
| Sector RS ratio turn, confirmed | Bullish (context) | Momentum at 90th pctile of trailing year, 5 weeks rising — a tailwind, not meaningful in isolation |
| Sector breadth >70% names participating | Bullish (context) | Confirms a move is broad rather than concentrated |

The point of the descriptor is to stay honest about *why* something looks the way it does and *how unusual it actually is* — while refusing to collapse many signals into one number that looks more rigorous than it is.

Quantification of *meaning* isn't off the table permanently — see [Open Questions](#open-questions--future-directions) for what would have to be true first.

---

## AI Synthesis Layer

The most valuable AI function is **reconciling conflicting signals**, not just summarising them.

**Example synthesis output:**

> "Management has used the phrase 'normalising demand environment' three times in the last two calls — language that historically precedes guide-downs. Options flow is showing unusual put activity 30 days out. Insiders were net sellers last month. Technically the stock is sitting on key support that has held twice before. That combination — deteriorating fundamentals against technical support — is the kind of tension worth watching heading into the next print."

**What the AI layer does:**
- Summarises current signal confluence across all layers
- Identifies conflicts (strong insider buying but bearish options flow — why?)
- Generates plain-English thesis: informed money direction, sentiment positioning, technical setup
- Flags **regime context** — is the broader market risk-on or risk-off? Read signals in that light
- Runs **narrative detection** — what's the story driving the ticker right now
- Helps sharpen research log entries — turning a loose read into a falsifiable expectation with a date attached
- Over time: "historically when these signals aligned, here's what tended to happen"

**Vector store for long-form retrieval:**
Store all documents (10-Ks, transcripts, expert calls, articles) as embeddings. Enables queries like:
"What has management said about gross margin pressure across the last 6 quarters?"
— retrieval across entire document history for a ticker, not just the latest filing.

---

## Visualisation Layer

The best traders have internalised *patterns* — they feel when something is wrong before they can articulate why. Visualisation is how you build that pattern recognition faster than experience alone allows. The goal is to encode signal in visual dimensions the eye picks up without conscious effort: spatial relationships, motion, colour gradients, flow.

Most market tools present tables and line charts because they're easy to build. This system does better.

---

### Core Visualisations

**Sector Rotation Wheel**
A circular diagram with the 11 GICS sectors positioned around it indicating cycle phase (early/mid/late/recession). Each sector node sized by flow momentum, coloured by relative strength trend. Animatable — scrub back through time and watch sectors move around the clock. Interactive: click any sector node to drill into constituent stocks and their individual signal descriptors.

**Money Flow River (Sankey)**
Capital moving *between* sectors week over week. Flow width = volume of rotation. Colour = direction (inflow green, outflow amber). You see the river of money shifting in a single glance — far more visceral than a table of numbers. Hover any flow to see the underlying ETF data and top constituent movers.

**Relative Strength Heat Grid**
Rows = sectors (or individual watchlist tickers). Columns = weeks (52-week rolling window). Cell colour = relative strength vs SPY that week. Hot colours outperforming, cool underperforming. Momentum streaks, reversals, and mean-reversion patterns become immediately visible as waves across the grid. Time-scrubbable.

**Signal Confluence Radar**
Per ticker. Six axes: options flow, insider activity, sentiment, technicals, sector tailwind, qualitative intelligence. Each axis plots the signal's percentile within its own history — a measured position, not an invented score, and continuous enough that shapes actually differ (four-notch axes would render every ticker as the same blob). Axis colour encodes direction; unconfirmed signals render hollow. The shape is still not a composite — no area calculation, no single number summarising it. Full and symmetric = broad confluence. Lopsided = mixed signals worth investigating. Hover any axis to see the underlying data and the plain-English read behind it. Compare two tickers side by side.

**Market Breadth Waterfall**
All constituents of an index or sector as vertical bars, sorted by performance, above/below a waterline. When most bars are above waterline = broad participation. When a few tall bars hold the index up while most are below = deteriorating internals hiding behind index strength. Animatable over time — watch the waterfall evolve through a cycle.

**Insider Transaction Timeline**
Per ticker. A timeline with dots for each Form 4 filing, sized by transaction value, coloured by buy/sell/exercise, overlaid directly on the price chart. Immediately see whether insiders bought into weakness or sold into strength. Cluster buys highlighted. Shows historically whether insider activity preceded moves for that specific name.

**13F Portfolio Evolution**
For each tracked manager — a treemap of their portfolio, sized by position weight, coloured by quarter-over-quarter change (building = green, trimming = amber, exited = grey). Animate across quarters to watch the portfolio reshape. Zoom into a sector to see concentration. Compare two managers' positioning on the same name.

**Volatility Surface**
3D surface showing implied volatility across strikes and expiries. Skew, term structure, and unusual IV spikes are immediately visible spatially in a way that tables of IV numbers never convey. Rotatable, zoomable. Overlay historical surface from prior earnings to compare current positioning.

**Regime Dashboard**
Single-page morning brief. Yield curve shape (visual, not just a number), credit spread trend, VIX term structure, sector rotation wheel position, risk-on/off ratio (XLY/XLP), and the AI-derived cycle phase estimate — all in one view. Walk in each morning and know the weather in under 10 seconds.

---

### Interaction Model

Visualisations are only as useful as the interactions they support. Every view should support:

**Time scrubbing** — a global timeline slider that replays any view historically. Watch rotation, breadth, and signal confluence evolve together. This is how intuition is built: seeing the same pattern play out repeatedly across different periods until you recognise it instantly in the present.

**Drill-down everywhere** — every aggregate is clickable. Sector → constituents. Manager portfolio → individual positions. Signal descriptor → raw underlying data. Nothing is a dead end.

**Cross-filtering** — selecting a sector in the rotation wheel filters the watchlist heatmap to show only tickers in that sector. Clicking a time period in the heat grid updates all other views to that window. Everything is connected.

**Overlay anything** — drag price onto the insider timeline. Drag the sector rotation phase onto a ticker chart. Drag macro regime onto the breadth waterfall. Correlations become visible without requiring statistical literacy.

**Scenario / Parameter Playground** — the centrepiece interactive feature. Load any ticker with its current signals. For each parameter (short interest, sector flow momentum, insider activity, sentiment, earnings tone), drag a slider through that signal's *own historical range* — the slider is honest because every position on it is a value the signal has actually taken, not a point on an invented scale. The confluence radar and AI narrative update live as you move. Lets you answer: "what would need to be true for the read on this name to change?" and "which signals matter most for this name?" Builds genuine intuition for signal sensitivity while keeping the inputs anchored to measured reality.

---

### Charting Libraries

| Use case | Library |
|---|---|
| Rotation wheel, Sankey, heat grid, custom layouts | D3.js — maximum control |
| Price/volume charts, candlesticks | TradingView lightweight-charts |
| Volatility surface (3D) | Plotly.js or Three.js |
| Radar/spider charts, treemaps | D3.js or Recharts |
| Animation and transitions | Framer Motion |
| Component container | React |

D3.js is the non-negotiable choice for the custom visualisations. Nothing else provides this level of control over spatial encoding. It has a learning curve but the output is unreplicable with charting libraries.

---

## Design System

### Philosophy

Minimal. Light. Intentional. The aesthetic serves the data — every design decision either makes signals clearer or gets out of the way. No decoration that doesn't encode information. No colour used for beauty alone.

The reference world is professional trading terminals, but stripped of their 1990s density and rebuilt with modern type and spatial generosity. Think Bloomberg if it were designed today by someone who cared about craft — reworked for daylight rather than the trading-floor dark.

### Colour Palette

```
Background         #EEF1F6   Cool light blue-grey — not stark white, keeps the "system" undertone from the original dark palette
Surface            #FFFFFF   Cards, panels — one step lighter than the background
Surface raised     #E3E8F0   Hover states, active panels
Border             #C7CFDC   Subtle structure, never decorative
Text primary       #10151F   Near-black — crisp against light backgrounds
Text secondary     #566072   Labels, metadata, axis text
Accent             #2955D8   Electric blue — primary interactive element, key signals
Bullish            #0E8F6F   Green with teal bias — darkened from the dark-mode value to hold contrast on a light background
Bearish            #D6432E   Coral red — same hue family as the dark-mode value, darkened for the same reason
Warning / neutral  #C67C0E   Amber — mixed signals, pending confirmation
Dim                #9AA3B4   Inactive, low-confidence signals
```

The single aesthetic risk carries over unchanged: the accent is electric blue rather than the expected green (bullish) or the terminal amber. Blue reads as "information" — it's the colour of the system itself, separate from the bullish/bearish polarity. This makes the interactive layer feel distinct from the data layer, which is a meaningful UX decision.

Bullish/bearish are meaningfully darker and more saturated than a naive invert of the old dark-mode hues — light backgrounds need more contrast to hit the same legibility threshold for graphical elements (IBM's Carbon Design System documents this same effect in their own light-theme data-viz palette). Red/green colour-blindness affects roughly 8% of men — not addressed with a colour change here, but worth pairing signal pills with a shape/icon cue later if that becomes a real usability issue.

### Typography

```
Display / headlines   Inter — weight 600-700, tight tracking (-0.02em)
Data / numbers        JetBrains Mono — monospaced, aligns decimal columns naturally, tabular figures (tnum) enabled
Body / prose          Inter — weight 400, relaxed line height (1.6)
Labels / metadata     Inter — weight 500, uppercase, wide tracking (0.08em), 11px
```

Numbers are always monospaced. This is non-negotiable for financial data — proportional fonts make columns unreadable at a glance.

### Layout Principles

Dense but not cluttered. Information-rich panels separated by generous negative space. No rounded corners on data elements (cards, tables, chart panels) — sharp edges read as precision. Subtle rounded corners only on interactive elements (buttons, tags, pills).

Grid: 12-column, 24px gutters. Panels snap to the grid. Nothing floats.

Hierarchy via weight and colour, never size alone. A secondary metric next to a primary metric uses text-secondary colour at the same size — not a smaller font. This keeps the layout clean while maintaining clear information hierarchy.

### Motion

Purposeful, never decorative. Three categories:

- **Data transitions** — when values update, numbers count up/down rather than jumping. Chart lines draw rather than appear. Duration: 300-600ms, ease-out.
- **Navigation** — panel transitions slide rather than fade. Directional motion encodes spatial relationship (drilling down slides right, going back slides left).
- **Time scrubbing** — smooth 60fps animation as the timeline slider moves. This is the most important animation in the system — it needs to feel like scrubbing video, not updating a chart.

Respect `prefers-reduced-motion`. All animations degrade gracefully to instant transitions.

### Component Vocabulary

A small, consistent set of components used throughout — never invent a new pattern when an existing one works:

- **Signal pill** — small rounded tag showing signal direction (bullish/bearish/neutral colour), with fill opacity encoding the reading's percentile vs the signal's own history and a hollow outline until confirmed. Hover reveals the measured value. Used everywhere a signal needs inline representation.
- **Range gauge** — a horizontal bar marking where the current reading sits within the signal's own historical range, percentile shown as a number beside it. Continuous, because the measurement is real; the interpretation caveats live in the descriptor text, not the geometry.
- **Stat block** — label (uppercase, tracking, secondary colour) above value (mono, primary colour). Used for every numeric metric.
- **Panel** — surface-coloured card with border, no shadow. The atomic layout unit.
- **Feed item** — timestamp left, event description right, signal pill far right. Used in the signal feed and activity streams.

---

```
┌──────────────────────────────────────────────────────────┐
│                    DATA INGESTION                        │
│  Market data (batch) │ Documents │ Alt-data scrapers     │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                   SIGNAL GENERATION                      │
│   Normalise → Describe (direction + percentile) → Store  │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│              VECTOR STORE (long-form docs)               │
│         Chunk → Embed → Pinecone / pgvector              │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                   AI SYNTHESIS                           │
│  Signal confluence + RAG retrieval → Thesis + Descriptor │
└──────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────┐
│                      DASHBOARD UI                        │
│  Watchlist heatmap │ Ticker deep-dive │ Signal feed      │
│  Sector rotation heatmap │ Research log                  │
└──────────────────────────────────────────────────────────┘
```

**Tech stack recommendation:**
- **Backend** — Python + FastAPI (data processing, signal scoring, Claude API calls)
- **Frontend** — React + D3.js (custom visualisations) + TradingView lightweight-charts (price/OHLC) + Framer Motion (animation)
- **Database** — PostgreSQL + TimescaleDB extension (time-series price + signal history)
- **Vector store** — Supabase pgvector (keeps it in the Postgres stack) or Pinecone
- **AI** — Claude API with structured prompts, JSON output for signal layer
- **Fonts** — Inter + JetBrains Mono (both free, Google Fonts / self-hosted)

See [ARCHITECTURE.md](ARCHITECTURE.md) for how this pipeline breaks down into separate, independently-buildable projects and the interface contracts between them.

---

## Dashboard UI Views

**1. Watchlist Heatmap**
All tracked tickers assessed by overall signal confluence — a count of aligned signals, never a weighted composite, with each signal's extremity vs its own history visible on drill-down. Colour-coded bullish/bearish/neutral. Sortable by confluence count, signal change, volume anomaly. At a glance: where signal activity is concentrated right now.

**2. Ticker Deep-Dive**
Click any name → full breakdown:
- Each signal layer individually (options flow, insider, sentiment, technicals, qualitative)
- AI synthesis paragraph
- Chart with annotated key levels
- Recent filing/news/expert call summaries

**3. Signal Feed**
Running feed of notable events across the watchlist:
- New insider Form 4 filed
- Unusual options sweep detected
- Short interest spike
- New 13F position added by tracked manager
- Earnings transcript posted + tone analysis

**4. Sector Rotation Heatmap**
All 11 GICS sectors assessed by: flow momentum + relative strength trend + breadth participation. Colour-coded and updated daily. Shows which sectors are in accumulation, distribution, or neutral. Feeds a regime indicator (cycle phase estimate) that puts per-ticker signals in context — e.g. "this insider buy is in a sector currently under distribution."

**5. Research Log**
The system's epistemic check. A dated log of falsifiable reads: what you think is happening, what should follow if you're right, and a date by which it should show up. The system snapshots the current signal state alongside each entry, then resurfaces the entry when its horizon passes — so reality grades the read (right / mixed / wrong) before hindsight can rewrite it. No positions, no P&L: the unit of record is a read, not a trade. Without this, understanding drifts into confident storytelling; with it, the system builds a record of which kinds of reads — and which signals — actually deserve trust.

---

## Build Phases

Sequenced as end-to-end vertical slices rather than by data layer — each slice should produce one real signal flowing all the way to the dashboard before the next slice starts. See [ARCHITECTURE.md](ARCHITECTURE.md#build-order) for the same plan organized by deployable unit; this is the product-facing view of the same order.

Two standing rules for every slice:

- **It ships understanding, not just pipeline** — each slice must change what the system tells you about the market the week it lands. A slice that only produces infrastructure is mis-scoped.
- **Know why each piece is being built** — the AI synthesis layer is the differentiated core; nothing off the shelf reconciles filing language against positioning against sector context. The RRG math, heatmaps, and connectors are commodity — worth building in-house mainly for what the construction teaches. Build them cheap and resist gold-plating.

### Day 0 — Research Log (before any code)
Start the research log immediately as a dated markdown file. The discipline precedes the tooling: every later slice makes the reads better-informed, but none of them block writing the first one today.

### Phase 0 — Design System (Week 0-1, parallel with everything below)
- Establish colour tokens, typography, and component vocabulary in code
- Build static mockups of the key views: sector rotation heatmap, ticker deep-dive, rotation wheel
- Validate the aesthetic before building real data into it
- D3.js sandbox: prototype the rotation wheel and heat grid with dummy data to validate the feel

### Slice 1 — Sector Rotation, end to end (Week 1-2)
Sector rotation over "one ticker, every layer" or "Form 4 first" — it's the area worth building real intuition for first, not just the cheapest one to stand up. It also forces the shared signal contract to be entity-generic (sector or ticker) from day one instead of retrofitting it once a ticker-level signal shows up.
- Daily sector ETF closes (Polygon) → relative strength ratios vs SPY, computed in-house
- Sector ETF flow ingestion (ETF.com / VettaFi scrape)
- Sector breadth — computable in-house from constituent closes via Polygon's grouped-daily endpoint (Finviz as a visual cross-check, not a dependency)
- One real sector-level descriptor (relative strength ratio turn) flowing end to end, then extended across all 11 GICS sectors
- Persist the full weekly series, not just the latest snapshot — the time-scrubbing promise needs history accumulating from day one
- Sector rotation heatmap UI — a ranked table first, no D3 yet; the Rotation Wheel is a visual upgrade on the same signal, not a prerequisite for it

### Slice 2 — One Ticker-Level Signal (Week 3)
- SEC EDGAR Form 4 parser (insider transactions) — free, dead-simple cluster-buy heuristic
- Insider cluster-buy descriptor, same signal shape as the sector-level ones from Slice 1
- Basic watchlist UI showing ticker signals alongside sector context

### Slice 3 — AI Synthesis (Week 4-5)
Now that a sector-level and a ticker-level signal both exist, there's something real to reconcile.
- Claude API synthesis layer — combines sector context + ticker signal into the plain-English read (the "sector tailwind confirmed" vs "sector rotation working against it" example above is the target output)
- Long-form document pipeline: EDGAR 10-K/10-Q + earnings transcripts, vector store for retrieval
- Ticker deep-dive UI

### Slice 4 — Breadth (Week 6+)
Fill in the remaining data sources now that the interfaces are proven, roughly free before paid:
- StockTwits / Reddit sentiment scoring, AAII weekly CSV, CBOE put/call ratio, Google Trends
- 13F parser (same EDGAR API as Form 4 — quick win alongside it)
- LinkedIn headcount via People Data Labs, job postings ingestion
- Options flow integration (Unusual Whales API — start paying here, once the rest of the system already works without it)

---

## Quick Wins to Pull Forward

**Research log** — a markdown file and the discipline to write dated, falsifiable reads. Zero infrastructure. Start today.

**Design system prototype** — before any real data, build the rotation wheel and signal radar with dummy data. Validate the feel early. D3.js with hardcoded values takes a day and tells you whether the visual language is right before you've invested weeks in the pipeline.

**EDGAR 13F parsing** — free, same API as Form 4, high signal. Build alongside the insider transaction parser in Slice 2.

**OpenInsider** — free aggregator for insider cluster buys. Can use as a reference while building the raw EDGAR parser.

**Google Trends** — free, zero infrastructure. Add as a crowding/late-stage detection signal early.

**AAII sentiment CSV** — free weekly download, trivial to ingest. Useful at extremes as a contrarian signal.

---

## Key Principles

- **Sector rotation is a context multiplier** — a strong ticker signal in a sector seeing institutional inflows is worth more than the same signal in a sector under distribution
- **Visualisation is how intuition is built** — time-scrubbing through historical data until patterns are recognisable at a glance is the point, not just displaying current state
- **Design serves the data** — every visual decision either makes signals clearer or gets out of the way. No decoration that doesn't encode information.
- **Numbers are always monospaced** — proportional fonts make financial columns unreadable at a glance
- **Options flow and price/volume divergence reveal positioning** — read them for who is positioned and how ahead of events, not as timing triggers
- **Convergence across weak signals** is more powerful than any single strong signal
- **Precise about what was measured, humble about what it means** — show the measured value and its percentile vs the signal's own history; keep all interpretation in words. Coarseness is not a costume for humility.
- **Confluence is a count, not a composite** — "3 of 5 sources bullish" is honest arithmetic; a weighted score is invented calibration
- **Long-form explains; market data corroborates** — filings and transcripts carry the story, positioning and price show whether the market believes it. A good read needs both.
- **The herd reacts to price.** Informed money moves first. The goal is to see informed money moving.
- **This is a research tool, not a trading system** — no entry/exit calls, no trade tracking. The output is understanding, meant to inform decisions made elsewhere, not to make them.
- **Resolution matches the decision horizon** — weeks to quarters. Daily data is fast enough; execution-timing tools serve trades, not understanding, and stay out of scope by design
- **Every read gets a date and a grade** — write down what you think is happening, what should follow, and by when; let reality grade it. Understanding that is never tested degrades into confident storytelling.
- **A slice ships understanding, not just pipeline** — if a build phase doesn't change what you know about the market the week it lands, it's mis-scoped
- **Expensive data last** — validate the system works with free sources before paying for options flow or expert transcripts

---

## Open Questions / Future Directions

- **When (if ever) to weight signals** — measurement is already numeric (each signal's percentile vs its own history), but the system deliberately ships without *meaning* weights or composite scores (see [Signal Descriptors](#signal-descriptors)): inventing "+0.8 for insider cluster buy" before any outcome data exists is false precision, not rigor. The research log is the only credible path to calibration: once enough reads are graded, patterns like "insider clusters preceded correct reads more often than sentiment extremes did" become checkable. Qualitative calibration comes first; numeric weights only if the record ever gets deep enough to support them — one person's log may never get there, and that's fine.
- Sector rotation leading indicators: automate ingestion of ISM, yield curve, credit spreads to anticipate rotation before ETF flows confirm
- Crypto extension: same architecture applies but different data sources (on-chain data, exchange flows, funding rates)
- Alert system: push notifications when signal confluence crosses threshold on a watchlist ticker, when a sector rotation turn is detected, or when a research log entry comes due for grading

---

*Document generated from design conversation — covers crowd timing, signal architecture, data source inventory (market, long-form, qualitative, sector rotation), AI synthesis design, research log, visualisation layer, design system, and phased build plan.*
