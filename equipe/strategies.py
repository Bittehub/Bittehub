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


def momentum_ajuste(prices, i, univers, p):
    """Le chasseur : les top_n meilleurs rendements sur lookback jours, divisés par leur volatilité.
    Un titre qui monte régulièrement passe devant un titre qui monte autant mais en dents de scie."""
    scores = []
    for t in univers:
        h = prices.hist(t, i, p["lookback"] + 1)
        if h is None:
            continue
        perf = h[-1] / h[0] - 1
        if p["filtre_absolu"] and perf <= 0:
            continue
        vol = _std(_rets(h))
        if vol > 0:
            scores.append((perf / vol, t))
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


def double_momentum(prices, i, univers, p, refuge=None):
    """Le pilier : tout sur l'indice large qui a le plus monté sur lookback jours, s'il a monté ;
    sinon tout sur le refuge (obligataire). C'est le « dual momentum » classique."""
    perfs = []
    for t in univers:
        if t == refuge:
            continue
        h = prices.hist(t, i, p["lookback"] + 1)
        if h is not None:
            perfs.append((h[-1] / h[0] - 1, t))
    if not perfs:
        return {}
    perf, best = max(perfs)
    if perf > 0:
        return {best: 1.0}
    return {refuge: 1.0} if refuge else {}


M = 21  # jours de cotation par mois


def _w13612(prices, i, t):
    """Momentum « 13612W » de Keller : (12·r1 + 4·r3 + 2·r6 + r12) / 4, en mois de 21 jours."""
    h = prices.hist(t, i, 12 * M + 1)
    if h is None:
        return None
    r = [h[-1] / h[-1 - k * M] - 1 for k in (1, 3, 6, 12)]
    return (12 * r[0] + 4 * r[1] + 2 * r[2] + r[3]) / 4


def _sma12(prices, i, t):
    """Prix rapporté à la moyenne de ses 13 derniers prix mensuels, le dernier compris."""
    h = prices.hist(t, i, 12 * M + 1)
    if h is None:
        return None
    return h[-1] / (sum(h[-1 - k * M] for k in range(13)) / 13)


def _meilleurs(scores, k):
    return [t for _, t in sorted(((s, t) for t, s in scores.items() if s is not None), reverse=True)[:k]]


# Univers de Keller (2022), avec les équivalents anciens : VWO→EEM, VEA/VGK→EFA, BND→AGG, BIL→SHY.
BAA_CANARIS = ["SPY", "EEM", "EFA", "AGG"]
BAA_OFFENSIF = ["SPY", "QQQ", "IWM", "EFA", "EWJ", "EEM", "VNQ", "DBC", "GLD", "TLT", "HYG", "LQD"]
BAA_DEFENSIF = ["TIP", "DBC", "SHY", "IEF", "TLT", "LQD", "AGG"]


def baa(prices, i, univers, p):
    """La vigie (Bold Asset Allocation, Keller 2022) : si les 4 canaris (actions US, émergents,
    monde, obligations) ont un momentum positif, les top_offensif meilleurs de 12 actifs au ratio
    SMA12 ; sinon les top_defensif meilleurs de 7 actifs défensifs, remplacés par des bons du Trésor
    s'ils font moins bien qu'eux."""
    canaris = [_w13612(prices, i, t) for t in BAA_CANARIS]
    if None in canaris:
        return {}
    if all(c > 0 for c in canaris):
        best = _meilleurs({t: _sma12(prices, i, t) for t in BAA_OFFENSIF}, p["top_offensif"])
        return {t: 1.0 / len(best) for t in best}
    sc = {t: _sma12(prices, i, t) for t in BAA_DEFENSIF}
    ref = sc.get("SHY")
    w = {}
    for t in _meilleurs(sc, p["top_defensif"]):
        dest = t if ref is None or sc[t] >= ref else "SHY"
        w[dest] = w.get(dest, 0.0) + 1.0 / p["top_defensif"]
    return w


ALL_WEATHER = {"SPY": 0.30, "TLT": 0.40, "IEF": 0.15, "GLD": 0.075, "DBC": 0.075}


def all_weather(prices, i, univers, p):
    """Le rempart : l'approximation publique du portefeuille « All Weather » de Bridgewater.
    Un actif pas encore coté voit sa part répartie entre les autres."""
    w = {t: x for t, x in ALL_WEATHER.items() if prices.hist(t, i, 1) is not None}
    tot = sum(w.values())
    return {t: x / tot for t, x in w.items()}


STRATEGIES = {
    "momentum": (momentum, {
        "lookback": (20, 252, int), "skip": (0, 21, int), "top_n": (1, 5, int),
        "rebalance_days": (5, 42, int), "filtre_absolu": (0, 1, int)}),
    "momentum_ajuste": (momentum_ajuste, {
        "lookback": (20, 252, int), "top_n": (1, 5, int), "rebalance_days": (5, 42, int),
        "filtre_absolu": (0, 1, int)}),
    "reversion": (reversion, {
        "lookback": (5, 60, int), "trend_sma": (50, 250, int), "top_n": (1, 5, int),
        "z_entree": (0.5, 3.0, float), "rebalance_days": (3, 21, int)}),
    "defensif": (defensif, {
        "vol_lookback": (20, 250, int), "vol_cible": (0.04, 0.15, float), "rebalance_days": (5, 42, int)}),
    "tendance": (tendance, {
        "sma": (50, 250, int), "max_actifs": (2, 10, int), "rebalance_days": (5, 42, int)}),
    "double_momentum": (double_momentum, {
        "lookback": (63, 252, int), "rebalance_days": (5, 42, int)}),
    "baa": (baa, {
        "top_offensif": (1, 12, int), "top_defensif": (1, 7, int), "rebalance_days": (5, 42, int)}),
    "all_weather": (all_weather, {"rebalance_days": (5, 63, int)}),
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


def targets(strategie, prices, i, univers, params, options=None):
    """options vient de la config de l'agent : "refuge" (pour le pilier) ; "parking" est traité
    par moteur.cibles, pas ici."""
    if strategie == "double_momentum":
        return double_momentum(prices, i, univers, params, (options or {}).get("refuge"))
    return STRATEGIES[strategie][0](prices, i, univers, params)
