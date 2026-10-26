"""Stratégies publiées, avec leurs paramètres d'origine.

Chaque fonction rend des poids cibles à partir des prix d'AVANT le jour i (prices.hist), comme les
stratégies de l'équipe. Un mois vaut 21 jours de cotation. Les ETF lancés tardivement sont
remplacés par leur équivalent plus ancien, partout et sur toutes les périodes (pas de regard vers le
futur) : VWO→EEM, VEA/VGK→EFA, BND→AGG, BIL→SHY, GSG→DBC.
"""
import math

M = 21  # jours de cotation par mois


def _std(xs):
    n = len(xs)
    if n < 2:
        return 0.0
    m = sum(xs) / n
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))


def _rets(h):
    return [h[k] / h[k - 1] - 1 for k in range(1, len(h))]


def perf(prices, i, t, n):
    h = prices.hist(t, i, n + 1)
    return None if h is None else h[-1] / h[0] - 1


def w13612(prices, i, t):
    """Momentum « 13612W » de Keller : (12·r1 + 4·r3 + 2·r6 + r12) / 4."""
    h = prices.hist(t, i, 12 * M + 1)
    if h is None:
        return None
    p0 = h[-1]
    r = [p0 / h[-1 - k * M] - 1 for k in (1, 3, 6, 12)]
    return (12 * r[0] + 4 * r[1] + 2 * r[2] + r[3]) / 4


def sma12(prices, i, t):
    """Prix rapporté à la moyenne des 13 derniers prix mensuels (le dernier compris) : BAA de Keller."""
    h = prices.hist(t, i, 12 * M + 1)
    if h is None:
        return None
    pts = [h[-1 - k * M] for k in range(13)]
    return h[-1] / (sum(pts) / 13)


def sma(prices, i, t, n):
    h = prices.hist(t, i, n)
    return None if h is None else (h[-1], sum(h) / n)


def vol(prices, i, t, n):
    h = prices.hist(t, i, n + 1)
    return None if h is None else _std(_rets(h)) * math.sqrt(252)


def _top(scores, k):
    scores = [(s, t) for t, s in scores.items() if s is not None]
    return [t for _, t in sorted(scores, reverse=True)[:k]]


def _eq(ts, poids=1.0):
    return {t: poids / len(ts) for t in ts} if ts else {}


def _add(*ws):
    out = {}
    for w in ws:
        for t, x in w.items():
            out[t] = out.get(t, 0.0) + x
    return out


# --- Références -------------------------------------------------------------------------------

def spy(prices, i, u, p):
    return {"SPY": 1.0}


def classique_60_40(prices, i, u, p):
    return {"SPY": 0.6, "IEF": 0.4}


# --- Filtres de tendance ----------------------------------------------------------------------

def ptj_200(prices, i, u, p):
    """Paul Tudor Jones / Faber : actions si le S&P 500 est au-dessus de sa moyenne 200 jours,
    sinon obligations à 7-10 ans."""
    s = sma(prices, i, "SPY", 200)
    if s is None:
        return {}
    return {"SPY": 1.0} if s[0] > s[1] else {"IEF": 1.0}


def gtaa5(prices, i, u, p):
    """Faber (2007), « A Quantitative Approach to Tactical Asset Allocation » : 5 classes d'actifs à
    20 %, chacune gardée seulement au-dessus de sa moyenne 10 mois, sinon bons du Trésor."""
    w = {}
    for t in ("SPY", "EFA", "IEF", "VNQ", "DBC"):
        s = sma(prices, i, t, 10 * M)
        w[t if s and s[0] > s[1] else "SHY"] = w.get(t if s and s[0] > s[1] else "SHY", 0.0) + 0.2
    return w


# --- Momentum dual (Antonacci) ----------------------------------------------------------------

def gem(prices, i, u, p):
    """Antonacci (2014), « Global Equities Momentum » : le meilleur de S&P 500 / monde hors
    États-Unis sur 12 mois s'il bat les bons du Trésor, sinon obligations agrégées."""
    r = {t: perf(prices, i, t, 12 * M) for t in ("SPY", "EFA", "SHY")}
    if None in r.values():
        return {}
    best = "SPY" if r["SPY"] >= r["EFA"] else "EFA"
    return {best: 1.0} if r[best] > r["SHY"] else {"AGG": 1.0}


# --- Keller -----------------------------------------------------------------------------------

DAA_RISQUE = ["SPY", "IWM", "QQQ", "EFA", "EWJ", "EEM", "VNQ", "DBC", "GLD", "TLT", "HYG", "LQD"]
DAA_CASH = ["SHY", "IEF", "LQD"]


def vaa_g4(prices, i, u, p):
    """Keller & Keuning (2017), VAA-G4 : le meilleur actif risqué si les 4 ont un 13612W positif,
    sinon le meilleur actif « cash »."""
    risque = {t: w13612(prices, i, t) for t in ("SPY", "EFA", "EEM", "AGG")}
    cash = {t: w13612(prices, i, t) for t in DAA_CASH}
    if None in risque.values():
        return {}
    if all(s > 0 for s in risque.values()):
        return {_top(risque, 1)[0]: 1.0}
    return {_top(cash, 1)[0]: 1.0}


def daa(prices, i, u, p):
    """Keller & Keuning (2018), DAA-G12 : canaris EEM et AGG ; 0, 1 ou 2 canaris négatifs donnent
    0 %, 50 % ou 100 % dans le meilleur actif cash, le reste dans les 6 meilleurs actifs risqués."""
    canaris = [w13612(prices, i, t) for t in ("EEM", "AGG")]
    if None in canaris:
        return {}
    part_cash = sum(1 for c in canaris if c <= 0) / 2
    risque = _top({t: w13612(prices, i, t) for t in DAA_RISQUE}, 6)
    cash = _top({t: w13612(prices, i, t) for t in DAA_CASH}, 1)
    return _add(_eq(risque, 1 - part_cash), _eq(cash, part_cash))


BAA_OFFENSIF = ["SPY", "QQQ", "IWM", "EFA", "EWJ", "EEM", "VNQ", "DBC", "GLD", "TLT", "HYG", "LQD"]
BAA_DEFENSIF = ["TIP", "DBC", "SHY", "IEF", "TLT", "LQD", "AGG"]


def _baa_defensif(prices, i):
    sc = {t: sma12(prices, i, t) for t in BAA_DEFENSIF}
    ref = sc.get("SHY")
    picks = _top(sc, 3)
    return _add(*[{(t if ref is None or sc[t] >= ref else "SHY"): 1 / 3} for t in picks])


def _baa(prices, i, offensif, k):
    canaris = [w13612(prices, i, t) for t in ("SPY", "EEM", "EFA", "AGG")]
    if None in canaris:
        return {}
    if all(c > 0 for c in canaris):
        return _eq(_top({t: sma12(prices, i, t) for t in offensif}, k))
    return _baa_defensif(prices, i)


def baa_equilibre(prices, i, u, p):
    """Keller (2022), BAA équilibré : canaris SPY, VWO, VEA, BND ; offensif = les 6 meilleurs de 12
    au ratio SMA12 ; défensif = les 3 meilleurs de 7, bons du Trésor s'ils font moins bien."""
    return _baa(prices, i, BAA_OFFENSIF, 6)


def baa_agressif(prices, i, u, p):
    """Keller (2022), BAA agressif : offensif = le meilleur de QQQ, VWO, VEA, BND."""
    return _baa(prices, i, ["QQQ", "EEM", "EFA", "AGG"], 1)


# --- Portefeuilles permanents -----------------------------------------------------------------

def all_weather(prices, i, u, p):
    """Approximation publique du portefeuille « All Weather » de Bridgewater (R. Dalio)."""
    return {"SPY": 0.30, "TLT": 0.40, "IEF": 0.15, "GLD": 0.075, "DBC": 0.075}


def parite_risque(prices, i, u, p):
    """Parité de risque sans levier : poids inverses de la volatilité 3 mois."""
    v = {t: vol(prices, i, t, 3 * M) for t in ("SPY", "EFA", "TLT", "IEF", "GLD", "DBC")}
    v = {t: x for t, x in v.items() if x}
    tot = sum(1 / x for x in v.values())
    return {t: (1 / x) / tot for t, x in v.items()}


# --- Momentum de série temporelle (AQR / Man AHL, version sans vente à découvert) --------------

TSMOM_U = ["SPY", "IWM", "EFA", "EEM", "VNQ", "TLT", "IEF", "LQD", "GLD", "DBC"]


def tsmom(prices, i, u, p):
    """Moskowitz, Ooi & Pedersen (2012), version longue seulement : chaque actif dont le rendement
    12 mois bat les bons du Trésor reçoit un poids inversement proportionnel à sa volatilité, pour
    viser environ 12 % de volatilité par actif / N ; le reste en bons du Trésor."""
    rf = perf(prices, i, "SHY", 12 * M)
    if rf is None:
        return {}
    w = {}
    dispo = [t for t in TSMOM_U if prices.hist(t, i, 12 * M + 1) is not None]
    for t in dispo:
        r, v = perf(prices, i, t, 12 * M), vol(prices, i, t, 3 * M)
        if r is not None and v and r > rf:
            w[t] = min(0.25, (0.12 / v) / len(dispo))
    reste = 1.0 - sum(w.values())
    if reste > 0:
        w["SHY"] = w.get("SHY", 0.0) + reste
    return w


# --- Gestion de la volatilité (Moreira & Muir, 2017) ------------------------------------------

def vol_geree_spy(prices, i, u, p):
    """S&P 500 dont l'exposition est réduite quand la volatilité du dernier mois dépasse 15 %,
    le reste en bons du Trésor. Jamais de levier."""
    v = vol(prices, i, "SPY", M)
    if v is None:
        return {}
    x = min(1.0, 0.15 / v) if v > 0 else 1.0
    return {"SPY": x, "SHY": 1 - x}


CANDIDATS = {
    "spy": spy, "60_40": classique_60_40, "ptj_200": ptj_200, "gtaa5": gtaa5, "gem": gem,
    "vaa_g4": vaa_g4, "daa": daa, "baa_equilibre": baa_equilibre, "baa_agressif": baa_agressif,
    "all_weather": all_weather, "parite_risque": parite_risque, "tsmom": tsmom,
    "vol_geree_spy": vol_geree_spy,
}


def agents_actuels():
    """Les 4 agents de l'équipe, tels que configurés (config/equipe.json), sans évolution."""
    import json
    import os
    from equipe import strategies
    cfg = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                      "config", "equipe.json")))
    out = {}
    for n, a in cfg["agents"].items():
        par = strategies.clamp(a["strategie"], a["parametres"])
        out[n] = {"strategie": a["strategie"], "params": par, "univers": a.get("univers", cfg["univers"]),
                  "options": a.get("options"), "rebalance_days": par["rebalance_days"]}
    return out


# --- Rotation sectorielle (Faber, 2010, « Relative Strength Strategies for Investing ») --------

SECTEURS = ["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY"]


def secteurs(prices, i, u, p):
    """Les 3 secteurs américains au meilleur momentum moyen (1, 3, 6 et 12 mois), chacun gardé
    seulement au-dessus de sa moyenne 10 mois, sinon bons du Trésor."""
    sc = {}
    for t in SECTEURS:
        r = [perf(prices, i, t, k * M) for k in (1, 3, 6, 12)]
        if None not in r:
            sc[t] = sum(r) / 4
    w = {}
    for t in _top(sc, 3):
        s = sma(prices, i, t, 10 * M)
        dest = t if s and s[0] > s[1] else "SHY"
        w[dest] = w.get(dest, 0.0) + 1 / 3
    return w


# --- Accelerating Dual Momentum (EngineeredPortfolio, 2018) -----------------------------------

def adm(prices, i, u, p):
    """Le meilleur de S&P 500 / monde hors États-Unis selon la somme des rendements 1, 3 et 6 mois,
    s'il est positif ; sinon obligations longues."""
    sc = {}
    for t in ("SPY", "EFA"):
        r = [perf(prices, i, t, k * M) for k in (1, 3, 6)]
        if None in r:
            return {}
        sc[t] = sum(r)
    best = _top(sc, 1)[0]
    return {best: 1.0} if sc[best] > 0 else {"TLT": 1.0}


CANDIDATS.update({"secteurs": secteurs, "adm": adm})
