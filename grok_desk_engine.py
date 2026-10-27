#!/usr/bin/env python3
"""GROK DESK engine: builds calibrated initial state -> state.js (window.GD_STATE).
Tries Coinbase public candles for BTC/ETH/SOL (3s timeout), falls back to a seeded GBM."""
import json, math, random, time, urllib.request
random.seed(4229)
SEED_PX = {'BTC': 80450.72, 'ETH': 3120.40, 'SOL': 182.35}
def fetch(sym):
    try:
        u = f'https://api.exchange.coinbase.com/products/{sym}-USD/candles?granularity=60'
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'grok-desk'}), timeout=3)
        rows = sorted(json.loads(r.read()))[-38:]  # [t, low, high, open, close, vol]
        return [{'t': x[0], 'o': x[3], 'h': x[2], 'l': x[1], 'c': x[4], 'v': x[5]} for x in rows], 'COINBASE'
    except Exception:
        return None, None
def synth(px, n=38, vol=0.0009):
    t0 = int(time.time() // 60 * 60) - n * 60; out = []; p = px * (1 - vol * 3)
    for i in range(n):
        o = p; ticks = [o]
        for _ in range(30): ticks.append(ticks[-1] * math.exp(random.gauss(0.00002, vol / 5.5)))
        p = ticks[-1]
        out.append({'t': t0 + i * 60, 'o': o, 'h': max(ticks), 'l': min(ticks), 'c': p, 'v': random.uniform(5, 40)})
    return out
assets, src = {}, 'SIM'
for s, px in SEED_PX.items():
    c, so = fetch(s)
    if c and len(c) > 10: src = so
    else: c = synth(px)
    rets = [math.log(c[i]['c'] / c[i - 1]['c']) for i in range(1, len(c))]
    mu = sum(rets) / len(rets); sd = math.sqrt(sum((r - mu) ** 2 for r in rets) / max(1, len(rets) - 1))
    assets[s] = {'candles': c, 'px': c[-1]['c'], 'vol1m': max(sd, 4e-4), 'drift1m': mu}
eq, v = [], 315000.0
for i in range(77): v *= math.exp(random.gauss(0.00021, 0.004)); eq.append(round(v, 2))
eq.append(320086.0)
state = {'generated': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'calib_source': src, 'assets': assets,
         'books': {'demo': {'label': '$4.1K BANK', 'bal': 320086.0, 'bank': 4100.0, 'eq': eq, 'tickets': 58794, 'wins': 28809},
                   'owen': {'label': 'OWEN RH L3 BOOK', 'bal': 500.0, 'bank': 500.0, 'eq': [500.0] * 20, 'tickets': 0, 'wins': 0}},
         'kelly_frac': 0.25, 'edge_threshold_c': 1.5, 'mc_draws': 3000, 'run': 4229}
open('state.js', 'w').write('window.GD_STATE=' + json.dumps(state) + ';\n')
print('state.js written · calib', src, {k: round(a['px'], 2) for k, a in assets.items()})
