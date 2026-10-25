"""Marché synthétique pour tester la mécanique hors ligne.

Ces séries ne disent RIEN de la rentabilité réelle : elles servent uniquement aux tests et à la
démonstration quand aucune source de prix n'est joignable. Le cache est marqué "synthetique" et les
rapports l'affichent en gros.
"""
import datetime as dt
import math
import random

from . import data

# (bêta actions, bêta taux, bêta or, vol propre annuelle)
PROFILS = {
    "SPY": (1.0, 0.0, 0.0, 0.02), "QQQ": (1.2, 0.0, 0.0, 0.08), "IWM": (1.15, 0.0, 0.0, 0.10),
    "EFA": (0.85, 0.0, 0.1, 0.08), "EEM": (1.0, 0.0, 0.15, 0.14), "TLT": (-0.2, 1.4, 0.0, 0.04),
    "IEF": (-0.1, 0.6, 0.0, 0.02), "GLD": (0.05, 0.2, 1.0, 0.05), "VNQ": (0.9, 0.4, 0.0, 0.10),
    "XLK": (1.2, 0.0, 0.0, 0.10), "XLF": (1.1, -0.1, 0.0, 0.10), "XLE": (0.9, -0.2, 0.3, 0.18),
    "XLV": (0.75, 0.1, 0.0, 0.08), "XLP": (0.55, 0.2, 0.0, 0.07), "XLU": (0.5, 0.4, 0.0, 0.09),
}

# régime : (dérive actions, vol actions, dérive taux, vol taux, proba de rester)
REGIMES = {
    "hausse": (0.12, 0.13, 0.00, 0.07, 0.995),
    "baisse": (-0.30, 0.30, 0.06, 0.10, 0.97),
    "plat": (0.02, 0.17, 0.01, 0.08, 0.99),
}


def generate(tickers, days=1600, seed=7, start="2020-01-02"):
    rng = random.Random(seed)
    d = dt.date.fromisoformat(start)
    dates = []
    while len(dates) < days:
        if d.weekday() < 5:
            dates.append(d.isoformat())
        d += dt.timedelta(days=1)
    regime = "hausse"
    level = {t: 100.0 for t in tickers}
    closes = {t: [] for t in tickers}
    sq = math.sqrt(1 / 252)
    for _ in dates:
        mu_e, vol_e, mu_b, vol_b, stay = REGIMES[regime]
        if rng.random() > stay:
            regime = rng.choice([r for r in REGIMES if r != regime])
        fe = mu_e / 252 + vol_e * sq * rng.gauss(0, 1)
        fb = mu_b / 252 + vol_b * sq * rng.gauss(0, 1)
        fg = 0.04 / 252 + 0.15 * sq * rng.gauss(0, 1)
        for t in tickers:
            be, bb, bg, idio = PROFILS.get(t, (1.0, 0.0, 0.0, 0.10))
            r = be * fe + bb * fb + bg * fg + idio * sq * rng.gauss(0, 1)
            level[t] *= math.exp(r)
            closes[t].append(level[t])
    return dates, closes


def write(tickers, cache_dir, days=1600, seed=7):
    dates, closes = generate(tickers, days, seed)
    for t in tickers:
        data.write_cache(cache_dir, t, dict(zip(dates, closes[t])))
    data.write_meta(cache_dir, {"source": "synthetique", "graine": seed, "jours": days})
    return dates
