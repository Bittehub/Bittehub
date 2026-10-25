"""Mesures de performance sur une série de valeurs journalières."""
import math


def rendements(vals):
    return [vals[k] / vals[k - 1] - 1 for k in range(1, len(vals)) if vals[k - 1] > 0]


def max_drawdown(vals):
    peak, dd = -1.0, 0.0
    for v in vals:
        peak = max(peak, v)
        if peak > 0:
            dd = max(dd, 1 - v / peak)
    return dd


def sharpe(rets):
    if len(rets) < 2:
        return 0.0
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / (len(rets) - 1))
    return 0.0 if sd == 0 else m / sd * math.sqrt(252)


def score(vals):
    """Ce que l'entraîneur cherche à améliorer : Sharpe, pénalisé par le pire drawdown."""
    return sharpe(rendements(vals)) - 3.0 * max_drawdown(vals)


def correlation(a, b):
    n = min(len(a), len(b))
    a, b = a[-n:], b[-n:]
    if n < 3:
        return 0.0
    ma, mb = sum(a) / n, sum(b) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    va = sum((x - ma) ** 2 for x in a)
    vb = sum((y - mb) ** 2 for y in b)
    return 0.0 if va == 0 or vb == 0 else cov / math.sqrt(va * vb)


def resume(vals, jours_par_an=252):
    if len(vals) < 2 or vals[0] <= 0:
        return {"rendement": 0.0, "annualise": 0.0, "vol": 0.0, "sharpe": 0.0, "drawdown_max": 0.0}
    r = rendements(vals)
    tot = vals[-1] / vals[0] - 1
    ann = (1 + tot) ** (jours_par_an / max(1, len(r))) - 1
    m = sum(r) / len(r)
    vol = math.sqrt(sum((x - m) ** 2 for x in r) / max(1, len(r) - 1)) * math.sqrt(jours_par_an)
    return {"rendement": tot, "annualise": ann, "vol": vol, "sharpe": sharpe(r), "drawdown_max": max_drawdown(vals)}
