# M&M EP7 — "When the VIX hits 40: Buy or Run?" (33 years of data)

Everything from Model & Market Episode 7, made reproducible. Every number shown
in the video can be regenerated from this repo, or checked live in TradingView
with the included Pine Script.

**This is market research, not financial advice.** A backtest is not proof.

---

## What we tested

A falsifiable rule, formalized from the popular "buy the dip when the VIX
spikes" claim:

- **Trigger:** on any trading day, if the CBOE VIX *closes* at or above a
  threshold T (we test 25, 30, 40)
- **Entry:** buy SPY at that day's close (VIX settles 16:15 ET, so a close
  trigger is tradeable at the close — no lookahead)
- **Question asked:** what did SPY return over the following 12 months?

Window: **1993–2026** (the full VIX era; SPY data starts 1993).

## The numbers (as shown in the video)

| Trigger | Episodes | Days above | Median 12-mo SPY return | Hit rate (up in 12m) |
|---|---|---|---|---|
| VIX ≥ 25 | 161 | — | +10.5% | 64% |
| VIX ≥ 30 | 84 | — | +16.0% | 74% |
| **VIX ≥ 40** | **33** | **208** | **+26.5%** | **88%** |

Baselines for context:

- Any random day (all-days): median +12.3%, up 80%
- Calm days (VIX ≤ 15): median +12.0%, up 87%
- Buy & hold SPY 1993–2026: ≈ +1660% total (≈ 12% CAGR)

**The honest read (this is the point of the episode):** the edge is *not*
being right more often (80% → 88% is marginal). It is that when fear is
extreme, the *payout* is far bigger (median +26.5% vs +12.0% calm).

**The caveat, also shown:** three of the four worst 12-month losses landed in
the 2008–09 cluster, and 33 events in 33 years is a small sample — roughly one
a year, with a third of them in a single bad decade.

## Verify it yourself in TradingView

1. Open TradingView → Pine Editor (bottom bar)
2. Copy `pine/vix_spike_test.pine` into the editor → **Save**
3. **Add to chart** on an **SPY daily** chart
4. Open the **Strategy Tester** tab

You should get the same direction: **13 trades since 2014, ~69% winners,
profit factor ≈ 2.74.**

> Note: TradingView's `TVC:VIX` history starts in 2014, so that run is shorter
> than the full 33-year study above — that is disclosed in the video. Also,
> `TVC:VIX` and other VIX feeds can differ on borderline days (exactly 40.0),
> so your trade count may differ by 1–2.

## Reproduce the 33-year backtest locally

```bash
pip install yfinance pandas numpy
python backtest_vix.py
```

`backtest_vix.py` re-downloads `^VIX` and `SPY` from yfinance, re-runs the
trigger/event-study, and prints the same per-threshold table plus per-episode
lists. The CSVs in `data/` are the exact frames used to render the video
(`vix_long.csv`, `spy_long.csv`, `win_2008.csv`, `t40_event_dates.csv`).

Data sources: CBOE VIX and SPY via yfinance; VIX was independently
cross-verified against a second feed. A backtest is not proof.

## Files

| Path | What it is |
|---|---|
| `pine/vix_spike_test.pine` | TradingView strategy — run it yourself |
| `backtest_vix.py` | The 33-year event-study backtest (self-contained) |
| `data/vix_long.csv` | Daily CBOE VIX, 1990–2026 |
| `data/spy_long.csv` | Daily SPY close, 1993–2026 |
| `data/win_2008.csv` | The 2008 case-study window (SPY + VIX) |
| `data/t40_event_dates.csv` | The 33 distinct VIX≥40 episode start dates |

## Series

Model & Market tests one market rule at a time — a falsifiable claim, real
data, and an honest caveat. Next episode: the rule or indicator you ask for in
the comments.
