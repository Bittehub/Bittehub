"""Banc de recherche.

Règles :
- conception = 2014-01-02 → aujourd'hui ; validation = 2004-03-01 → 2013-12-31 (crise de 2008 comprise).
- Chaque simulation sur la conception est consignée dans recherche/essais.jsonl : le nombre d'essais
  sert au Sharpe dégonflé (Bailey & López de Prado, 2014).
- La validation ne tourne qu'une fois, sur la sélection écrite dans recherche/selection.json AVANT
  de la lancer ; le verrou recherche/validation.lock empêche de recommencer.
"""
import datetime as dt
import json
import math
import os
import statistics
import sys

from equipe import data, gardefous, mesures, moteur, strategies

from . import candidats

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
PRIX = os.path.join(RACINE, "donnees", "recherche")
ESSAIS = os.path.join(ICI, "essais.jsonl")
SELECTION = os.path.join(ICI, "selection.json")
VERROU = os.path.join(ICI, "validation.lock")

PERIODES = {"conception": ("2014-01-02", "2026-12-31"), "validation": ("2004-03-01", "2013-12-31")}

# Garde-fous de recherche : ceux de l'équipe, avec plus d'indices larges exemptés du plafond par
# titre (fonds indiciels d'actions ou d'obligations très diversifiés). À faire approuver avant
# d'être appliqué à l'équipe réelle.
INDICES_LARGES_RECHERCHE = ["SPY", "IWM", "EFA", "EEM", "IEF", "TLT", "SHY", "AGG", "LQD", "TIP"]

_prix = None


def prix():
    global _prix
    if _prix is None:
        tickers = sorted(f[:-4] for f in os.listdir(PRIX) if f.endswith(".csv"))
        _prix = data.load_prices(tickers, PRIX, "SPY")
    return _prix


def garde_fous():
    g, _ = gardefous.load(os.path.join(RACINE, "config", "garde-fous.json"))
    return dict(g, indices_larges=INDICES_LARGES_RECHERCHE)


def _enregistrer(nom, fn):
    strategies.STRATEGIES[nom] = (fn, {})


def simuler(nom, fn=None, periode="conception", rebalance_days=21, options=None, consigner=True, params=None,
            strategie=None, univers=None):
    """Valeurs journalières d'une stratégie sur la période, plus ses mesures."""
    if periode == "validation" and not os.environ.get("VALIDATION_AUTORISEE"):
        raise SystemExit("La validation ne se lance que par `python3 -m recherche valider`.")
    p = prix()
    if strategie:
        cle = strategie  # stratégie de l'équipe (equipe/strategies.py), avec ses paramètres
    else:
        cle = "r_" + nom
        _enregistrer(cle, fn or candidats.CANDIDATS[nom])
    debut, fin = PERIODES[periode]
    s, e = p.index_of(debut), sum(1 for d in p.dates if d <= fin)
    par = dict(params or {}, rebalance_days=rebalance_days)
    vals = moteur.simuler(cle, par, univers or sorted(p.closes), p, s, e, garde_fous(), options=options)
    m = mesures_completes(vals, p, s, e)
    if consigner and periode == "conception":
        with open(ESSAIS, "a") as f:
            f.write(json.dumps({"quand": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                "nom": nom, "rebalance_days": rebalance_days, "options": options,
                                "params": params, "strategie": strategie, "sharpe_jour": m["sharpe_jour"], "asymetrie": m["asymetrie"],
                                "aplatissement": m["aplatissement"], "jours": m["jours"]}) + "\n")
    return vals, m


def rendements_tresor(p, s, e):
    shy = [p.px("SHY", k) for k in range(s, e)]
    return mesures.rendements(shy)


def mesures_completes(vals, p, s, e):
    r = mesures.rendements(vals)
    rf = rendements_tresor(p, s, e)
    ex = [a - b for a, b in zip(r, rf)]
    n = len(r)
    m_ex = sum(ex) / n
    sd = math.sqrt(sum((x - m_ex) ** 2 for x in ex) / (n - 1)) or 1e-12
    z = [(x - m_ex) / sd for x in ex]
    skew = sum(x ** 3 for x in z) / n
    kurt = sum(x ** 4 for x in z) / n
    base = mesures.resume(vals)
    annees = {}
    for k in range(s, e):
        annees.setdefault(p.dates[k][:4], []).append(vals[k - s])
    par_annee = {a: v[-1] / v[0] - 1 for a, v in annees.items() if len(v) > 20}
    # Stabilité : Sharpe sur trois tiers de la période.
    tiers = [r[j * n // 3:(j + 1) * n // 3] for j in range(3)]
    rft = [rf[j * n // 3:(j + 1) * n // 3] for j in range(3)]
    return {
        "rendement": base["rendement"], "annualise": base["annualise"], "vol": base["vol"],
        "drawdown_max": base["drawdown_max"],
        "sharpe": m_ex / sd * math.sqrt(252), "sharpe_jour": m_ex / sd,
        "asymetrie": skew, "aplatissement": kurt, "jours": n,
        "pire_annee": min(par_annee.values()) if par_annee else 0.0,
        "sharpe_tiers": [mesures.sharpe([a - b for a, b in zip(t, u)]) for t, u in zip(tiers, rft)],
        "calmar": base["annualise"] / base["drawdown_max"] if base["drawdown_max"] else 0.0,
    }


def sharpe_degonfle(sr, t, skew, kurt, srs_essais):
    """Probabilité que le vrai Sharpe soit positif, une fois corrigé du nombre d'essais (Bailey &
    López de Prado, 2014). sr et srs_essais sont des Sharpe journaliers."""
    n = len(srs_essais)
    nd = statistics.NormalDist()
    if n < 2:
        sr0 = 0.0
    else:
        v = statistics.variance(srs_essais)
        g = 0.5772156649
        sr0 = math.sqrt(v) * ((1 - g) * nd.inv_cdf(1 - 1 / n) + g * nd.inv_cdf(1 - 1 / (n * math.e)))
    denom = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr ** 2))
    return nd.cdf((sr - sr0) * math.sqrt(t - 1) / denom), sr0


def essais():
    if not os.path.exists(ESSAIS):
        return []
    with open(ESSAIS) as f:
        return [json.loads(l) for l in f if l.strip()]


def equipe(series, rebalance=21, poids=None):
    """Valeur d'une équipe d'agents à partir de leurs valeurs journalières. Avec rebalance, le
    capital est remis à parts égales entre agents tous les `rebalance` jours (solidarité) ;
    sans, chaque agent garde son capital (comme aujourd'hui)."""
    noms = list(series)
    poids = poids or {n: 1 / len(noms) for n in noms}
    n = len(series[noms[0]])
    parts = {a: poids[a] / series[a][0] for a in noms}
    out = []
    for k in range(n):
        v = sum(parts[a] * series[a][k] for a in noms)
        out.append(v)
        if rebalance and k and k % rebalance == 0:
            parts = {a: poids[a] * v / series[a][k] for a in noms}
    return [x / out[0] for x in out]


def ligne(nom, m):
    t = m["sharpe_tiers"]
    return ("%-34s an %+5.1f%%  vol %4.1f%%  sharpe %5.2f  dd %5.1f%%  calmar %4.2f  pire an %+6.1f%%  "
            "tiers %5.2f %5.2f %5.2f" % (nom, m["annualise"] * 100, m["vol"] * 100, m["sharpe"], m["drawdown_max"] * 100,
                                        m["calmar"], m["pire_annee"] * 100, t[0], t[1], t[2]))
