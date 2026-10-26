"""python3 -m recherche conception | valider"""
import datetime as dt
import json
import os
import sys

from . import banc, candidats


def conception():
    for nom in candidats.CANDIDATS:
        _, m = banc.simuler(nom)
        print(banc.ligne(nom, m), flush=True)


def _serie(membre, periode):
    genre, nom = membre
    if genre == "candidat":
        return banc.simuler(nom, periode=periode, consigner=False)[0]
    a = candidats.agents_actuels()[nom]
    return banc.simuler("agent_" + nom, periode=periode, strategie=a["strategie"], params=a["params"],
                        univers=a["univers"], options=a["options"], rebalance_days=a["rebalance_days"],
                        consigner=False)[0]


def valider():
    """L'unique passage sur la période de validation, pour la sélection écrite à l'avance."""
    if os.path.exists(banc.VERROU):
        sys.exit("La validation a déjà eu lieu (%s). La relancer reviendrait à choisir sur elle." % banc.VERROU)
    with open(banc.SELECTION) as f:
        sel = json.load(f)
    os.environ["VALIDATION_AUTORISEE"] = "1"
    p = banc.prix()
    debut, fin = banc.PERIODES["validation"]
    s, e = p.index_of(debut), sum(1 for d in p.dates if d <= fin)
    with open(banc.VERROU, "w") as f:
        f.write("Validation lancée le %s sur %s → %s\n" % (dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), debut, fin))
    resultats = {}
    for nom, spec in [(sel["principale"]["nom"], sel["principale"])] + list(sel["references"].items()):
        series = {m[1]: _serie(m, "validation") for m in spec["membres"]}
        v = banc.equipe(series, spec["reequilibrage_capital_jours"]) if len(series) > 1 else list(series.values())[0]
        m = banc.mesures_completes(v, p, s, e)
        resultats[nom] = m
        print(banc.ligne(nom, m), flush=True)
        if len(series) > 1:
            for k, sv in series.items():
                print(banc.ligne("   " + k, banc.mesures_completes(sv, p, s, e)), flush=True)
    with open(os.path.join(banc.ICI, "validation.json"), "w") as f:
        json.dump({"periode": [debut, fin], "resultats": resultats}, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    {"conception": conception, "valider": valider}[sys.argv[1] if len(sys.argv) > 1 else "conception"]()
