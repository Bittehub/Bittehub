"""Améliorations du moteur testées comme des surcouches applicables à n'importe quelle stratégie."""
import math

from equipe import moteur

from . import candidats


def vol_portefeuille(prices, i, w, n=21):
    """Volatilité annualisée qu'aurait eue le portefeuille w sur les n derniers jours."""
    hs = {t: prices.hist(t, i, n + 1) for t in w if w[t] > 0}
    hs = {t: h for t, h in hs.items() if h is not None}
    if not hs:
        return None
    port = [sum(w[t] * (hs[t][k] / hs[t][k - 1] - 1) for t in hs) for k in range(1, n + 1)]
    return candidats._std(port) * math.sqrt(252)


def surcouche(cible, vol_cible=None, cash=None, n=21, cash_min=0.02):
    """cible(prices, i) -> poids. vol_cible : réduit l'exposition si la volatilité récente du
    portefeuille dépasse la cible (jamais de levier). cash : actif où placer ce qui reste."""
    def fn(prices, i, u, p):
        w = dict(cible(prices, i))
        if vol_cible and w:
            v = vol_portefeuille(prices, i, w, n)
            if v:
                k = min(1.0, vol_cible / v)
                w = {t: x * k for t, x in w.items()}
        reste = 1.0 - cash_min - sum(w.values())
        if cash and reste > 1e-6 and prices.hist(cash, i, 1) is not None:
            w[cash] = w.get(cash, 0.0) + reste
        return w
    return fn


def cible_agent(agent, g):
    return lambda prices, i: moteur.cibles(agent["strategie"], agent["params"], agent["univers"],
                                           agent["options"], prices, i, g)


def cible_candidat(nom):
    f = candidats.CANDIDATS[nom]
    return lambda prices, i: f(prices, i, None, {})
