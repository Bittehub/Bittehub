"""Les métiers des agents. Chaque stratégie rend des poids cibles à partir des prix d'AVANT le jour i.

PARAMS donne pour chaque paramètre (min, max, type) : l'entraîneur ne peut jamais en sortir.
"""
import math


def _sma(h):
    return sum(h) / len(h)


def _rets(h):
    return [h[k] / h[k - 1] - 1 for k in range(1, len(h))]


def _std(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def momentum(prices, i, univers, p):
    """Le chasseur : les top_n meilleures performances sur lookback jours, hors les skip derniers."""
    scores = []
    for t in univers:
        h = prices.hist(t, i, p["lookback"] + p["skip"] + 1)
        if h is None:
            continue
        perf = h[-1 - p["skip"]] / h[0] - 1
        if p["filtre_absolu"] and perf <= 0:
            continue
        scores.append((perf, t))
    best = [t for _, t in sorted(scores, reverse=True)[:p["top_n"]]]
    return {t: 1.0 / p["top_n"] for t in best}


def reversion(prices, i, univers, p):
    """Le contrarien : les replis les plus profonds (z-score) parmi les titres en tendance haussière."""
    picks = []
    for t in univers:
        h = prices.hist(t, i, max(p["trend_sma"], p["lookback"]))
        if h is None or h[-1] <= _sma(h[-p["trend_sma"]:]):
            continue
        w = h[-p["lookback"]:]
        sd = _std(w)
        if sd == 0:
            continue
        z = (h[-1] - _sma(w)) / sd
        if z < -p["z_entree"]:
            picks.append((z, t))
    best = [t for _, t in sorted(picks)[:p["top_n"]]]
    return {t: 1.0 / p["top_n"] for t in best}


def defensif(prices, i, univers, p):
    """Le gardien : parité de risque (inverse de la vol), réduite pour viser vol_cible."""
    hs = {t: prices.hist(t, i, p["vol_lookback"] + 1) for t in univers}
    hs = {t: h for t, h in hs.items() if h is not None}
    vols = {t: _std(_rets(h)) for t, h in hs.items()}
    vols = {t: v for t, v in vols.items() if v > 0}
    if not vols:
        return {}
    inv = {t: 1 / v for t, v in vols.items()}
    tot = sum(inv.values())
    w = {t: x / tot for t, x in inv.items()}
    rets = {t: _rets(hs[t]) for t in w}
    port = [sum(w[t] * rets[t][k] for t in w) for k in range(p["vol_lookback"])]
    pvol = _std(port) * math.sqrt(252)
    scale = min(1.0, p["vol_cible"] / pvol) if pvol > 0 else 1.0
    return {t: x * scale for t, x in w.items()}


def tendance(prices, i, univers, p):
    """Le navigateur : les titres au-dessus de leur moyenne mobile, les plus éloignés d'abord."""
    up = []
    for t in univers:
        h = prices.hist(t, i, p["sma"])
        if h is None:
            continue
        gap = h[-1] / _sma(h) - 1
        if gap > 0:
            up.append((gap, t))
    best = [t for _, t in sorted(up, reverse=True)[:p["max_actifs"]]]
    return {t: 1.0 / p["max_actifs"] for t in best}


STRATEGIES = {
    "momentum": (momentum, {
        "lookback": (20, 252, int), "skip": (0, 21, int), "top_n": (1, 5, int),
        "rebalance_days": (5, 42, int), "filtre_absolu": (0, 1, int)}),
    "reversion": (reversion, {
        "lookback": (5, 60, int), "trend_sma": (50, 250, int), "top_n": (1, 5, int),
        "z_entree": (0.5, 3.0, float), "rebalance_days": (3, 21, int)}),
    "defensif": (defensif, {
        "vol_lookback": (20, 250, int), "vol_cible": (0.04, 0.15, float), "rebalance_days": (5, 42, int)}),
    "tendance": (tendance, {
        "sma": (50, 250, int), "max_actifs": (2, 10, int), "rebalance_days": (5, 42, int)}),
}


def bounds(strategie):
    return STRATEGIES[strategie][1]


def clamp(strategie, params):
    """Ramène chaque paramètre dans ses bornes et à son type ; ignore les paramètres inconnus."""
    out = {}
    for k, (lo, hi, typ) in bounds(strategie).items():
        v = params[k]
        v = typ(round(v)) if typ is int else round(float(v), 4)
        out[k] = min(hi, max(lo, v))
    return out


def targets(strategie, prices, i, univers, params):
    return STRATEGIES[strategie][0](prices, i, univers, params)
