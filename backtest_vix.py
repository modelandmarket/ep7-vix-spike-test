#!/usr/bin/env python3
"""EP7: Does a VIX spike predict a forward SPY rally? (Quant Test)

Falsifiable rule tested:
  TRIGGER : VIX daily close >= T (T in {25, 30, 40})
  ENTRY   : buy SPY at that day's close (VIX settles 16:15 ET, so a close
            trigger is tradeable at the close — no lookahead)
  EXIT    : first of (VIX close < 20, hold for H calendar days)
Baselines:
  1. Buy & hold SPY over the same window
  2. All-days entry distribution (same H-day horizon, no condition)
  3. Calm-entry: VIX close <= 15 (the contrarian claim "fear is cheap")

Outputs: per-threshold trigger stats, forward returns 1/4/12 months,
per-episode episode table, regime split, saved CSVs in this dir.
"""
import warnings; warnings.filterwarnings("ignore")
import yfinance as yf
import pandas as pd
import numpy as np
import os

HERE = os.path.dirname(os.path.abspath(__file__))

vix = yf.download("^VIX", start="1990-01-01", interval="1d", progress=False, auto_adjust=False)
spy = yf.download("SPY",  start="1990-01-01", interval="1d", progress=False, auto_adjust=False)
# yfinance mixed-tz pitfall: normalize both to tz-naive before aligning
for df in (vix, spy):
    df.index = df.index.tz_localize(None) if df.index.tz is not None else df.index
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

vix["vix"] = vix["Close"].astype(float)
spy["close"] = spy["Close"].astype(float)

m = pd.DataFrame({"vix": vix["vix"], "close": spy["close"]}).dropna()
# SPY data starts 1993; VIX from 1990 — effective window starts at SPY's first bar
start = m.index[0]
print(f"Window: {start.date()} -> {m.index[-1].date()}  ({len(m)} trading days)")

def fwd_ret(close, dates, horizon_td):
    """Return from close at date -> close ~horizon_td trading days later."""
    idx = m.index.get_indexer(dates, method="nearest")
    end_idx = np.clip(idx + horizon_td, 0, len(m) - 1)
    c0, c1 = m["close"].values[idx], m["close"].values[end_idx]
    return c1 / c0 - 1.0

def episodes_at(trigger_bool, exit_fn):
    """Walk trigger days, group into non-overlapping episodes."""
    episodes = []
    i, n = 0, len(m)
    idx = m.index
    close = m["close"].values
    v = m["vix"].values
    t = m.index.to_numpy()
    trig = trigger_bool.to_numpy()
    i = 0
    while i < n:
        if trig[i]:
            entry_i = i
            # exit: VIX < 20 or H=63 trading days (~3 months)
            j = i
            while j < n and v[j] >= 20.0 and (j - i) < 63:
                j += 1
            exit_i = min(j, n - 1)
            episodes.append({
                "entry_date": t[entry_i], "exit_date": t[exit_i],
                "vix_entry": v[entry_i],
                "ret_episode": close[exit_i] / close[entry_i] - 1,
                "hold_days": int((pd.Timestamp(t[exit_i]) - pd.Timestamp(t[entry_i])).total_seconds() // 86400),
                "regime": pd.Timestamp(t[entry_i]).year,
            })
            i = exit_i + 1
        else:
            i += 1
    return pd.DataFrame(episodes)

bh_ret = m["close"].iloc[-1] / m["close"].iloc[0] - 1
bh_cagr = (m["close"].iloc[-1] / m["close"].iloc[0]) ** (252 / len(m)) - 1

# all-days distribution for horizons
horizons = {"1M": 21, "3M": 63, "12M": 252}
all_days = pd.DataFrame({h: fwd_ret(m["close"], m.index, n) for h, n in horizons.items()})
all_days.index = m.index

out = {}
print(f"\nB&H over window: total {bh_ret:.1%}, CAGR {bh_cagr:.2%}\n")
hdr = f"{'T':>3} | {'trig_days':>9} | {'ep':>4} | {'ep_med':>7} | {'ep_min':>7} | {'ep_max':>7} | " + \
      " | ".join([f"f{h} (med/mean/hit%)" for h in horizons])
print(hdr)
for T in [25, 30, 40]:
    trig = m["vix"] >= T
    trig_days_raw = int(trig.sum())
    # collapse consecutive trigger days: keep first day of each spike
    trig2 = trig & ~trig.shift(1, fill_value=False)
    trig_days = m.index[trig2]
    fwd = pd.DataFrame({h: fwd_ret(m["close"], trig_days, n) for h, n in horizons.items()})
    fwd.index = trig_days
    eps = episodes_at(trig2, None)
    stats = " | ".join([
        f"{fwd[h].median():.1%}/{fwd[h].mean():.1%}/{(fwd[h]>0).mean():.0%}"
        for h in horizons])
    print(f"{T:>3} | {trig_days_raw:>9} | {len(trig_days):>4} | {eps['ret_episode'].median():>6.1%} | "
          f"{eps['ret_episode'].min():>6.1%} | {eps['ret_episode'].max():>6.1%} | {stats}")
    # calm comparison at same horizon
    calm = m["vix"] <= 15
    calm_days = m.index[calm]
    fwdc = pd.DataFrame({h: fwd_ret(m["close"], calm_days, n) for h, n in horizons.items()})
    calm_line = " | ".join([f"{fwdc[h].median():.1%}/{fwdc[h].mean():.1%}/{(fwdc[h]>0).mean():.0%}" for h in horizons])
    all_line  = " | ".join([f"{all_days[h].median():.1%}/{all_days[h].mean():.1%}/{(all_days[h]>0).mean():.0%}" for h in horizons])
    print(f"     calm(<=15): n={len(calm_days)}: {calm_line}")
    print(f"     all-days  : n={len(all_days)}: {all_line}")
    eps.to_csv(os.path.join(HERE, f"episodes_T{T}.csv"), index=False)
    fwd.to_csv(os.path.join(HERE, f"fwd_T{T}.csv"))

# regime split for T=30
trig = (m["vix"] >= 30) & ~(m["vix"] >= 30).shift(1, fill_value=False)
eps30 = episodes_at(trig, None)
eps30["era"] = pd.cut(eps30["entry_date"], bins=[pd.Timestamp("1993-01-01"), pd.Timestamp("2000-01-01"),
                     pd.Timestamp("2010-01-01"), pd.Timestamp("2020-01-01"), pd.Timestamp("2027-01-01")],
                     labels=["1993-99", "2000-09", "2010-19", "2020-26"])
print("\nT=30 episodes by era:")
print(eps30.groupby("era", observed=True)["ret_episode"].agg(n="count", median="median", min="min", max="max").round(4))

# worst episodes table (T=30)
print("\nT=30 worst 5 episodes (entry -> episode return):")
print(eps30.nsmallest(5, "ret_episode")[["entry_date","exit_date","vix_entry","ret_episode","hold_days"]].to_string(index=False))
print("\nT=30 best 5:")
print(eps30.nlargest(5, "ret_episode")[["entry_date","exit_date","vix_entry","ret_episode","hold_days"]].to_string(index=False))
print("\nSaved: episodes_T{25,30,40}.csv, fwd_T{25,30,40}.csv")
