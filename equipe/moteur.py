"""Une journée de l'équipe : marquer, protéger, décider, coordonner, exécuter, consigner."""
from . import gardefous, strategies
from .portefeuille import Portefeuille


def nouvel_agent(nom, spec, capital, univers_equipe):
    return {
        "strategie": spec["strategie"],
        "role": spec["role"],
        "univers": spec.get("univers", univers_equipe),
        "options": spec.get("options", {}),
        "parametres": strategies.clamp(spec["strategie"], spec["parametres"]),
        "portefeuille": Portefeuille(capital).to_dict(),
        "capital_initial": capital,
        "historique": [],
        "pic": capital,
        "en_pause": False,
        "pause_depuis": None,
        "dernier_reequilibrage": None,
        "dernier_changement": None,
        "generation": 1,
    }


def _due(agent, prices, i):
    last = agent["dernier_reequilibrage"]
    return last is None or i - prices.index_of(last) >= agent["parametres"]["rebalance_days"]


def _trades(cible, actuel):
    return {t: cible.get(t, 0.0) - actuel.get(t, 0.0) for t in set(cible) | set(actuel)}


def cibles(strategie, params, univers, options, prices, i, g):
    """Poids cibles bornés par les garde-fous. Avec un "parking", la part que la stratégie laisse
    en cash est placée sur cet indice au lieu de dormir."""
    w = gardefous.clip_targets(strategies.targets(strategie, prices, i, univers, params, options), g, univers)
    parking = (options or {}).get("parking")
    if parking and prices.hist(parking, i, 1) is not None:
        reste = 1.0 - g["cash_min"] - sum(w.values())
        if reste > 0:
            w[parking] = w.get(parking, 0.0) + reste
            w = gardefous.clip_targets(w, g, univers)
    return w


def simuler(strategie, params, univers, prices, start, end, g, capital=10000.0, options=None):
    """Un agent seul, sur les jours [start, end) : sert à l'entraîneur pour comparer des réglages."""
    pf = Portefeuille(capital)
    vals, last = [], None
    for i in range(start, end):
        if last is None or i - last >= params["rebalance_days"]:
            v = pf.valeur(prices, i)
            w = cibles(strategie, params, univers, options, prices, i, g)
            trades, f = gardefous.limit_turnover(
                _trades({t: x * v for t, x in w.items()}, pf.notionnels(prices, i)), v, g)
            pf.executer(trades, prices, i, g)
            if f >= 1.0:
                last = i
        vals.append(pf.valeur(prices, i))
    return vals


def jour(etat, prices, i, g):
    """Fait tourner le jour i (décisions sur les prix d'avant i, exécution à la clôture de i).
    Rend la liste des événements du journal."""
    date = prices.dates[i]
    ev = []
    agents = etat["agents"]
    pfs = {n: Portefeuille.from_dict(a["portefeuille"]) for n, a in agents.items()}
    vals = {n: pfs[n].valeur(prices, i) for n in agents}
    team_eq = sum(vals.values())

    # 1. Coupe-circuit : un agent qui perd drawdown_max depuis son pic passe en cash et en pause.
    for n, a in agents.items():
        a["pic"] = max(a["pic"], vals[n])
        dd = 1 - vals[n] / a["pic"]
        if not a["en_pause"] and dd >= g["drawdown_max_agent"]:
            fills = pfs[n].liquider(prices, i, g)
            a["en_pause"], a["pause_depuis"] = True, date
            ev.append({"date": date, "type": "coupe_circuit", "agent": n, "drawdown": round(dd, 4),
                       "ordres": fills,
                       "texte": "%s perd %.1f %% depuis son pic : tout en cash, pause et rééducation."
                                % (n, dd * 100)})

    # 2. Chaque agent actif et dû propose ses cibles, bornées par les garde-fous.
    voulues, fixes = {}, {}
    for n, a in agents.items():
        if not a["en_pause"] and _due(a, prices, i):
            w = cibles(a["strategie"], a["parametres"], a["univers"], a.get("options"), prices, i, g)
            voulues[n] = {t: x * vals[n] for t, x in w.items()}
        else:
            for t, v in pfs[n].notionnels(prices, i).items():
                fixes[t] = fixes.get(t, 0.0) + v

    # 3. Coordination d'équipe : plafond de concentration commun.
    voulues, coupes = gardefous.team_overlay(voulues, fixes, team_eq, g)
    if coupes:
        ev.append({"date": date, "type": "concentration", "reductions": coupes,
                   "texte": "L'équipe était trop concentrée ; cibles réduites sur %s."
                            % ", ".join(sorted(coupes))})

    # 4. Exécution, sous plafond de rotation.
    for n, cible in voulues.items():
        a = agents[n]
        trades, f = gardefous.limit_turnover(_trades(cible, pfs[n].notionnels(prices, i)), vals[n], g)
        fills = pfs[n].executer(trades, prices, i, g)
        if f >= 1.0:
            a["dernier_reequilibrage"] = date
        if fills:
            ev.append({"date": date, "type": "ordres", "agent": n, "ordres": fills,
                       "poids_cibles": {t: round(v / vals[n], 4) for t, v in cible.items()},
                       "rotation_reduite": round(f, 4) if f < 1 else None})

    # 5. Consigner les valeurs de fin de journée.
    for n, a in agents.items():
        a["portefeuille"] = pfs[n].to_dict()
        a["historique"].append([date, round(pfs[n].valeur(prices, i), 2)])
    ref = etat["reference"]
    ref["historique"].append([date, round(ref["parts"] * prices.px(ref["ticker"], i), 2)])
    etat["equipe"]["historique"].append([date, round(sum(a["historique"][-1][1] for a in agents.values()), 2)])
    etat["au"] = date
    return ev
