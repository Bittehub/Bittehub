"""L'entraîneur : fait évoluer les réglages des agents, mais seulement sur preuve.

Un candidat (mutation, conseil d'un coéquipier, proposition de Claude) n'est adopté que s'il bat le
réglage actuel sur plusieurs périodes passées distinctes (plis), avec une marge, sans devenir un clone
d'un coéquipier. Tout se fait avec les prix connus à la date d'évaluation, jamais après.
"""
import math
import random

from . import mesures, moteur, strategies

ECHAUFFEMENT = 275  # plus long historique qu'un réglage peut demander (252 + 21 + marge)


def _plis(end, cfg):
    L, k = cfg["longueur_pli"], cfg["plis"]
    s0 = end - k * L
    if s0 < ECHAUFFEMENT:
        return None
    return [(s0 + j * L, s0 + (j + 1) * L) for j in range(k)]


def _t_stat(ecarts):
    """Écart moyen rapporté à sa propre dispersion : un gain qui varie beaucoup d'un pli à l'autre
    ressemble à du bruit, même s'il est gros en moyenne."""
    n = len(ecarts)
    m = sum(ecarts) / n
    var = sum((d - m) ** 2 for d in ecarts) / (n - 1)
    if var == 0:
        return float("inf") if m > 0 else 0.0
    return m / math.sqrt(var / n)


def _eval(agent, params, prices, plis, g):
    scores, rets = [], []
    for s, e in plis:
        vals = moteur.simuler(agent["strategie"], params, agent["univers"], prices, s, e, g,
                              options=agent.get("options"))
        scores.append(mesures.score(vals))
        rets.extend(mesures.rendements(vals))
    return scores, rets


def _mutation(strategie, params, rng):
    b = strategies.bounds(strategie)
    p = dict(params)
    for k in rng.sample(sorted(b), k=min(len(b), rng.choice([1, 1, 2]))):
        lo, hi, typ = b[k]
        if typ is int and hi - lo == 1:
            p[k] = 1 - p[k]
        else:
            step = (hi - lo) * rng.uniform(0.08, 0.3) * rng.choice([-1, 1])
            p[k] = p[k] + step if typ is float else p[k] + (int(round(step)) or rng.choice([-1, 1]))
    return strategies.clamp(strategie, p)


def _candidats(nom, agent, mentor, propositions, rng, n_max):
    """(paramètres, source, hypothèse) : d'abord Claude, puis le mentor, puis des mutations."""
    s, cur = agent["strategie"], agent["parametres"]
    out, vus = [], {tuple(sorted(cur.items()))}

    def add(p, src, hyp=None):
        p = strategies.clamp(s, p)
        key = tuple(sorted(p.items()))
        if key not in vus and len(out) < n_max:
            vus.add(key)
            out.append((p, src, hyp))

    for prop in propositions:
        add(dict(cur, **{k: v for k, v in prop["parametres"].items() if k in cur}),
            "claude:%s" % prop["id"], prop.get("hypothese"))
    if mentor:
        m_nom, m_agent = mentor
        communs = set(cur) & set(m_agent["parametres"])
        if communs:
            p = dict(cur)
            for k in communs:
                p[k] = (cur[k] + m_agent["parametres"][k]) / 2
            add(p, "mentor:%s" % m_nom, "Se rapprocher du réglage de %s sur %s." % (m_nom, ", ".join(sorted(communs))))
    for _ in range(n_max * 3):
        if len(out) >= n_max:
            break
        add(_mutation(s, cur, rng), "mutation")
    return out


def _mentor(nom, etat):
    """Le coéquipier actif le plus performant sur les 63 derniers jours réels."""
    best = None
    for n, a in etat["agents"].items():
        if n == nom or a["en_pause"] or len(a["historique"]) < 64:
            continue
        sc = mesures.score([v for _, v in a["historique"][-64:]])
        if best is None or sc > best[0]:
            best = (sc, n, a)
    return (best[1], best[2]) if best else None


def eligible(agent, prices, i, g):
    if agent["en_pause"]:
        return i - prices.index_of(agent["pause_depuis"]) >= g["pause_min_jours"]
    dates = [d for d in (agent["dernier_changement"], agent.get("derniere_recommandation")) if d]
    return not dates or i - prices.index_of(max(dates)) >= g["jours_min_entre_changements"]


MODES = {True: "auto", False: "non"}


def evoluer(etat, prices, i, g, cfg, propositions, adapter="auto"):
    """Évalue chaque agent éligible après la clôture du jour i. Rend les événements du journal.

    Trois modes :
    - "auto" : un meilleur réglage prouvé est adopté aussitôt ;
    - "conseil" : il est seulement recommandé (événement « recommandation ») ; un humain décide
      avec `python3 -m equipe adopter`. Un agent en pause reprend avec ses réglages actuels ;
    - "non" : rien n'est évalué, sauf la reprise des agents en pause avec leurs réglages actuels
      (sans cela, une équipe figée resterait en cash pour toujours après un coupe-circuit)."""
    mode = MODES.get(adapter, adapter)
    date = prices.dates[i]
    plis = _plis(i + 1, cfg)
    if plis is None:
        return []
    ev = []
    candidats_agents = [n for n, a in etat["agents"].items()
                        if eligible(a, prices, i, g) and (mode != "non" or a["en_pause"])]
    if not candidats_agents:
        return []
    equipiers = {}
    for n, a in etat["agents"].items():
        equipiers[n] = _eval(a, a["parametres"], prices, plis, g)

    for nom in candidats_agents:
        a = etat["agents"][nom]
        rng = random.Random("%s-%s" % (nom, date))
        explorer = mode == "auto" or (mode == "conseil" and not a["en_pause"])
        mes_props = [p for p in propositions if p["agent"] == nom and p["statut"] == "en_attente"] if explorer else []
        cands = (_candidats(nom, a, _mentor(nom, etat), mes_props, rng, g["candidats_max_par_evaluation"])
                 if explorer else [])
        base_scores, _ = equipiers[nom]
        base = sum(base_scores) / len(base_scores)
        best = None
        resultats = {}
        for p, src, hyp in cands:
            sc, rets = _eval(a, p, prices, plis, g)
            ecarts = [x - y for x, y in zip(sc, base_scores)]
            gain = sum(ecarts) / len(ecarts)
            t = _t_stat(ecarts)
            gagnes = sum(1 for d in ecarts if d > 0)
            corr = max([mesures.correlation(rets, equipiers[m][1]) for m in equipiers if m != nom] or [0.0])
            ok = (gagnes >= g["plis_gagnes_min"] and gain >= g["marge_adoption"] and t >= g["t_stat_min"]
                  and corr <= g["correlation_max_entre_agents"])
            r = {"parametres": p, "source": src, "hypothese": hyp, "gain": round(gain, 3), "t": round(t, 2),
                 "plis_gagnes": gagnes, "correlation_max": round(corr, 3), "accepte": ok}
            if src.startswith("claude:"):
                resultats[src.split(":", 1)[1]] = r
            if ok and (best is None or gain > best["gain"]):
                best = r

        for prop in mes_props:
            r = resultats.get(prop["id"])
            retenue = best and best["source"] == "claude:%s" % prop["id"]
            prop["statut"] = ("adoptee" if mode == "auto" else "recommandee") if retenue else "rejetee"
            prop["evaluee_le"] = date
            prop["resultat"] = r and {k: r[k] for k in ("gain", "t", "plis_gagnes", "correlation_max")}

        if a["en_pause"]:
            final = best["parametres"] if best else a["parametres"]
            final_score = base + (best["gain"] if best else 0.0)
            if final_score > 0:
                a["parametres"] = final
                a["en_pause"], a["pause_depuis"], a["dernier_reequilibrage"] = False, None, None
                a["pic"] = a["historique"][-1][1] if a["historique"] else a["capital_initial"]
                if best:
                    a["generation"] += 1
                    a["dernier_changement"] = date
                ev.append({"date": date, "type": "reprise", "agent": nom, "parametres": final,
                           "source": best["source"] if best else "inchange", "score_validation": round(final_score, 3),
                           "texte": "%s reprend le travail : score de validation %.2f sur %d plis."
                                    % (nom, final_score, len(plis))})
            else:
                ev.append({"date": date, "type": "pause_prolongee", "agent": nom, "score_validation": round(final_score, 3),
                           "texte": "%s reste en pause : aucun réglage n'a un score positif sur les plis récents." % nom})
            continue

        if best and mode == "conseil":
            a["derniere_recommandation"] = date
            diff = {k: [a["parametres"][k], best["parametres"][k]] for k in a["parametres"]
                    if a["parametres"][k] != best["parametres"][k]}
            ev.append({"date": date, "type": "recommandation", "agent": nom, "changements": diff,
                       "parametres": best["parametres"], "source": best["source"], "gain": best["gain"],
                       "plis_gagnes": best["plis_gagnes"], "hypothese": best["hypothese"],
                       "texte": "L'entraîneur recommande pour %s (%s) : %s, gain de score %+.2f (t=%.1f), %d/%d plis "
                                "gagnés. À décider par un humain." % (
                                    nom, best["source"], ", ".join("%s %s→%s" % (k, v[0], v[1]) for k, v in diff.items()),
                                    best["gain"], best["t"], best["plis_gagnes"], len(plis))})
        elif best:
            ancien = a["parametres"]
            a["parametres"], a["dernier_changement"] = best["parametres"], date
            a["generation"] += 1
            diff = {k: [ancien[k], best["parametres"][k]] for k in ancien if ancien[k] != best["parametres"][k]}
            ev.append({"date": date, "type": "adoption", "agent": nom, "changements": diff, "source": best["source"],
                       "gain": best["gain"], "plis_gagnes": best["plis_gagnes"], "hypothese": best["hypothese"],
                       "texte": "%s passe en génération %d (%s) : %s, gain de score %+.2f (t=%.1f), %d/%d plis gagnés."
                                % (nom, a["generation"], best["source"],
                                   ", ".join("%s %s→%s" % (k, v[0], v[1]) for k, v in diff.items()),
                                   best["gain"], best["t"], best["plis_gagnes"], len(plis))})
        else:
            ev.append({"date": date, "type": "statu_quo", "agent": nom, "candidats": len(cands),
                       "texte": "%s garde ses réglages : aucun des %d candidats ne fait mieux de façon fiable."
                                % (nom, len(cands))})
    return ev
