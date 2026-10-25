"""Le risk manager : des règles en code, pas un agent. Personne dans l'équipe ne peut les assouplir."""
import hashlib
import json


class GardeFousModifies(Exception):
    pass


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    g = json.loads(raw)
    if g.get("mode") != "papier":
        raise SystemExit("Ce prototype ne fait que du papier : mode doit valoir \"papier\".")
    return g, hashlib.sha256(raw).hexdigest()


def verify(path, signed_hash):
    g, h = load(path)
    if signed_hash and h != signed_hash:
        raise GardeFousModifies(
            "config/garde-fous.json a changé depuis sa signature. Si c'est vous, relisez-le puis lancez : "
            "python3 -m equipe garde-fous --approuver")
    return g, h


def clip_targets(w, g, univers):
    """Hors univers retiré, plafond par titre, pas de levier, cash minimum gardé."""
    out = {t: min(max(x, 0.0), g["poids_max_par_titre"]) for t, x in w.items() if t in univers and x > 0}
    cap = 1.0 - g["cash_min"]
    tot = sum(out.values())
    if tot > cap:
        out = {t: x * cap / tot for t, x in out.items()}
    return out


def team_overlay(cibles, fixes, team_equity, g):
    """Solidarité : aucun titre ne dépasse poids_max_equipe_par_titre de l'équipe entière.

    cibles = {agent: {ticker: montant cible}} pour les agents qui rééquilibrent aujourd'hui ;
    fixes = {ticker: montant} déjà détenu par ceux qui ne bougent pas. Les cibles qui font dépasser
    le plafond sont réduites au prorata, pour que l'équipe ne mise pas tout sur le même cheval.
    """
    cap = g["poids_max_equipe_par_titre"] * team_equity
    totals = {}
    for tg in cibles.values():
        for t, v in tg.items():
            totals[t] = totals.get(t, 0.0) + v
    cut = {}
    for t, v in totals.items():
        room = max(0.0, cap - fixes.get(t, 0.0))
        if v > room:
            cut[t] = room / v
    if not cut:
        return cibles, {}
    return ({a: {t: v * cut.get(t, 1.0) for t, v in tg.items()} for a, tg in cibles.items()},
            {t: round(1 - f, 4) for t, f in cut.items()})


def limit_turnover(trades, equity, g):
    """Si la rotation du jour dépasse le plafond, chaque ordre est réduit au prorata."""
    gross = sum(abs(v) for v in trades.values())
    cap = g["rotation_max_par_jour"] * equity
    if gross <= cap or gross == 0:
        return trades, 1.0
    f = cap / gross
    return {t: v * f for t, v in trades.items()}, f
