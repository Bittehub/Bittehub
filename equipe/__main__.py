"""python3 -m equipe <commande> : voir --help."""
import argparse
import datetime as dt
import json
import os
import shutil
import sys

from . import data, gardefous, rapport, strategies, synthetique
from .equipe import Chemins, avancer, charger_config, charger_prix, creer, ecrire_json, lire_json, sauver


def _journal_recent(path, n=400):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        lines = f.readlines()[-n:]
    return [json.loads(l) for l in lines if l.strip()]


def _ecrire_rapports(ch, etat, prefixe, titre):
    ev = _journal_recent(ch.journal)
    savoir = lire_json(ch.savoir, [])
    os.makedirs(ch.rapports, exist_ok=True)
    md = os.path.join(ch.rapports, prefixe + ".md")
    page = os.path.join(ch.rapports, prefixe + ".html")
    with open(md, "w") as f:
        f.write(rapport.markdown(etat, ev, savoir))
    with open(page, "w") as f:
        f.write(rapport.tableau_de_bord(etat, ev, savoir, titre))
    return md, page


def _garde_fous(ch, etat):
    try:
        return gardefous.verify(ch.garde_fous, etat["garde_fous_sha"])
    except gardefous.GardeFousModifies as e:
        sys.exit("ARRÊT : %s" % e)


def cmd_telecharger(ch, a):
    _, tickers = charger_config(ch)
    failed = data.fetch_all(tickers, ch.prix, a.source, a.depuis)
    if failed:
        sys.exit("Échec pour %s. Vérifiez l'accès réseau à la source « %s »." % (", ".join(failed), a.source))


def cmd_synthetique(ch, a):
    _, tickers = charger_config(ch)
    if os.path.exists(ch.prix) and data.read_meta(ch.prix).get("source") not in (None, "synthetique"):
        sys.exit("donnees/prix contient de vraies données ; je ne les écrase pas.")
    dates = synthetique.write(tickers, ch.prix, a.jours, a.graine)
    print("Marché SYNTHÉTIQUE écrit : %d jours (%s → %s). Pour tester la mécanique, pas la rentabilité."
          % (len(dates), dates[0], dates[-1]))


def cmd_init(ch, a):
    if os.path.exists(ch.etat) and not a.forcer:
        sys.exit("Une équipe existe déjà dans %s (--forcer pour repartir de zéro)." % ch.etat_dir)
    if a.forcer and os.path.exists(ch.etat_dir):
        shutil.rmtree(ch.etat_dir)
    prices = charger_prix(ch)
    etat = creer(ch, prices)
    sauver(ch, etat, [], [])
    print("Équipe créée : %d agents × %s $, en cash. Premier jour de trading : le prochain jour de cotation "
          "après %s." % (len(etat["agents"]), lire_json(ch.config)["capital_par_agent"], prices.dates[-1]))


def cmd_quotidien(ch, a):
    etat = lire_json(ch.etat)
    if not etat:
        sys.exit("Pas d'équipe. Lancez : python3 -m equipe init")
    g, _ = _garde_fous(ch, etat)
    cfg, _ = charger_config(ch)
    prices = charger_prix(ch)
    if etat["source_donnees"] != prices.source:
        sys.exit("L'équipe a été créée sur des données « %s » mais le cache contient « %s »."
                 % (etat["source_donnees"], prices.source))
    props = lire_json(ch.propositions, [])
    ev, n = avancer(etat, prices, g, cfg, props, a.jusqu_a, evolution=not a.sans_evolution)
    sauver(ch, etat, ev, props)
    md, page = _ecrire_rapports(ch, etat, "dernier", "Équipe de trading")
    print("%d jour(s) traité(s), à jour au %s. %d événement(s)." % (n, etat["au"], len(ev)))
    for e in ev:
        if e["type"] != "ordres":
            print(" ·", e.get("texte", e["type"]))
    print("Rapport : %s\nTableau de bord : %s" % (md, page))


def _backtest(ch, nom, debut, fin, evolution, prices):
    bt = Chemins(ch.racine, etat=os.path.join("backtests", nom))
    bt.rapports = ch.rapports
    if os.path.exists(bt.etat_dir):
        shutil.rmtree(bt.etat_dir)
    g, _ = gardefous.load(ch.garde_fous)
    cfg, _ = charger_config(ch)
    etat = creer(ch, prices, debut=debut)
    props = []
    print("Backtest « %s » (%s)…" % (nom, "avec évolution" if evolution else "réglages figés"))
    ev, _ = avancer(etat, prices, g, cfg, props, fin, evolution=evolution, log=print)
    sauver(bt, etat, ev, props)
    md, page = _ecrire_rapports(bt, etat, "backtest-" + nom, "Backtest « %s »" % nom)
    return etat, md, page


def cmd_backtest(ch, a):
    """Rejoue l'équipe sur le passé, dans un dossier à part. Avec --comparer, rejoue aussi la même
    équipe aux réglages figés : c'est le seul moyen honnête de savoir si l'évolution sert à quelque chose."""
    prices = charger_prix(ch)
    etat, md, page = _backtest(ch, a.nom, a.debut, a.fin, not a.sans_evolution, prices)
    print(open(md).read())
    print("Tableau de bord : %s" % page)
    if not a.comparer:
        return
    fige, md_f, page_f = _backtest(ch, a.nom + "-fige", a.debut, a.fin, False, prices)
    s, sf = rapport.synthese(etat), rapport.synthese(fige)
    lignes = ["", "## L'évolution a-t-elle servi ?", "",
              "| | Rendement | Sharpe | Drawdown max |", "|---|---:|---:|---:|"]
    for nom, m in (("Équipe qui évolue", s["equipe"]), ("Même équipe, réglages figés", sf["equipe"]),
                   ("Référence %s" % s["reference_ticker"], s["reference"])):
        lignes.append("| %s | %+.1f %% | %.2f | %.1f %% |" % (nom, m["rendement"] * 100, m["sharpe"], m["drawdown_max"] * 100))
    d = s["equipe"]["sharpe"] - sf["equipe"]["sharpe"]
    lignes += ["", "Écart de Sharpe dû à l'évolution : %+.2f. %s" % (d, (
        "Sur un seul historique, un écart de cette taille peut être de la chance : à confirmer sur d'autres "
        "périodes et en papier.") if abs(d) < 0.3 else (
        "Écart net, mais un seul historique ne prouve rien : à confirmer en papier sur plusieurs mois."))]
    with open(md, "a") as f:
        f.write("\n".join(lignes) + "\n")
    print("\n".join(lignes))
    print("Réglages figés : %s" % page_f)


def cmd_rapport(ch, a):
    etat = lire_json(ch.etat)
    md, page = _ecrire_rapports(ch, etat, "dernier", "Équipe de trading")
    print(open(md).read())


def cmd_garde_fous(ch, a):
    etat = lire_json(ch.etat)
    g, h = gardefous.load(ch.garde_fous)
    if not a.approuver:
        print(json.dumps(g, indent=2, ensure_ascii=False))
        print("Signature enregistrée : %s\nSignature du fichier : %s" % (etat and etat["garde_fous_sha"], h))
        return
    if not sys.stdin.isatty():
        sys.exit("La signature des garde-fous se fait à la main, dans un terminal interactif.")
    if input("Signer ces garde-fous (%s) ? Tapez OUI : " % h[:12]).strip() != "OUI":
        sys.exit("Rien n'a changé.")
    etat["garde_fous_sha"] = h
    ecrire_json(ch.etat, etat)
    print("Garde-fous signés.")


def cmd_proposer(ch, a):
    """Pour la réunion d'équipe : une hypothèse que l'entraîneur testera à la prochaine évaluation."""
    etat = lire_json(ch.etat)
    if a.agent not in etat["agents"]:
        sys.exit("Agent inconnu : %s (connus : %s)" % (a.agent, ", ".join(etat["agents"])))
    b = strategies.bounds(etat["agents"][a.agent]["strategie"])
    params = {}
    for kv in a.param:
        k, _, v = kv.partition("=")
        if k not in b:
            sys.exit("Paramètre inconnu pour %s : %s (connus : %s)" % (a.agent, k, ", ".join(b)))
        lo, hi, typ = b[k]
        params[k] = typ(float(v))
        if not lo <= params[k] <= hi:
            sys.exit("%s=%s hors bornes [%s, %s]." % (k, v, lo, hi))
    props = lire_json(ch.propositions, [])
    if sum(1 for p in props if p["statut"] == "en_attente") >= 6:
        sys.exit("Déjà 6 propositions en attente : attendez la prochaine évaluation.")
    pid = "%s-%d" % (dt.date.today().isoformat(), len(props) + 1)
    props.append({"id": pid, "agent": a.agent, "parametres": params, "hypothese": a.hypothese,
                  "auteur": a.auteur, "statut": "en_attente", "proposee_le": etat["au"]})
    ecrire_json(ch.propositions, props)
    print("Proposition %s enregistrée pour %s : %s" % (pid, a.agent, params))


def cmd_statut(ch, a):
    etat = lire_json(ch.etat)
    if not etat:
        sys.exit("Pas d'équipe.")
    s = rapport.synthese(etat)
    print("Au %s · source %s · équipe %.0f $ (%+.1f %%) · référence %.0f $ (%+.1f %%)" % (
        s["au"], s["source"], s["valeur_equipe"], s["equipe"]["rendement"] * 100,
        s["valeur_reference"], s["reference"]["rendement"] * 100))
    for x in s["agents"]:
        print("  %-11s gén.%-2d %s %8.0f $ %+6.1f %%  %s" % (x["agent"], x["generation"], "⏸" if x["en_pause"] else " ",
                                                         x["valeur"], x["rendement"] * 100, x["parametres"]))


def main(argv=None):
    p = argparse.ArgumentParser(prog="python3 -m equipe", description="Équipe d'agents de trading, en papier.")
    sp = p.add_subparsers(dest="cmd", required=True)
    x = sp.add_parser("telecharger", help="prix réels dans donnees/prix")
    x.add_argument("--source", choices=sorted(data.PROVIDERS), default="yahoo")
    x.add_argument("--depuis", default="2012-01-01")
    x = sp.add_parser("synthetique", help="marché synthétique, pour tester sans réseau")
    x.add_argument("--jours", type=int, default=1600)
    x.add_argument("--graine", type=int, default=7)
    x = sp.add_parser("init", help="crée l'équipe, tout en cash")
    x.add_argument("--forcer", action="store_true")
    x = sp.add_parser("quotidien", help="rattrape les jours manquants, fait évoluer, écrit le rapport")
    x.add_argument("--jusqu-a", dest="jusqu_a")
    x.add_argument("--sans-evolution", action="store_true")
    x = sp.add_parser("backtest", help="rejoue l'équipe sur le passé (n'affecte pas l'équipe réelle)")
    x.add_argument("--debut", required=True)
    x.add_argument("--fin")
    x.add_argument("--nom", default="defaut")
    x.add_argument("--sans-evolution", action="store_true")
    x.add_argument("--comparer", action="store_true", help="rejoue aussi l'équipe aux réglages figés")
    sp.add_parser("rapport", help="réécrit le rapport")
    sp.add_parser("statut", help="résumé en une ligne par agent")
    x = sp.add_parser("garde-fous", help="affiche ou signe les garde-fous")
    x.add_argument("--approuver", action="store_true")
    x = sp.add_parser("proposer", help="propose un réglage à tester")
    x.add_argument("--agent", required=True)
    x.add_argument("--param", action="append", required=True, metavar="CLE=VALEUR")
    x.add_argument("--hypothese", required=True)
    x.add_argument("--auteur", default="claude")
    a = p.parse_args(argv)
    ch = Chemins()
    {"telecharger": cmd_telecharger, "synthetique": cmd_synthetique, "init": cmd_init, "quotidien": cmd_quotidien,
     "backtest": cmd_backtest, "rapport": cmd_rapport, "statut": cmd_statut, "garde-fous": cmd_garde_fous,
     "proposer": cmd_proposer}[a.cmd](ch, a)


if __name__ == "__main__":
    main()
