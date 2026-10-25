"""Orchestration : créer l'équipe, rattraper les jours manquants, faire évoluer, sauvegarder."""
import json
import os

from . import data, entraineur, gardefous, moteur

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Chemins:
    def __init__(self, racine=RACINE, etat="etat"):
        self.racine = racine
        self.config = os.path.join(racine, "config", "equipe.json")
        self.garde_fous = os.path.join(racine, "config", "garde-fous.json")
        self.prix = os.path.join(racine, "donnees", "prix")
        self.etat_dir = os.path.join(racine, etat)
        self.etat = os.path.join(self.etat_dir, "equipe.json")
        self.journal = os.path.join(self.etat_dir, "journal.jsonl")
        self.savoir = os.path.join(self.etat_dir, "savoir.json")
        self.propositions = os.path.join(self.etat_dir, "propositions.json")
        self.rapports = os.path.join(racine, "rapports")


def lire_json(path, defaut=None):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut


def ecrire_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def charger_config(ch):
    cfg = lire_json(ch.config)
    tickers = sorted(set(cfg["univers"]) | {cfg["reference"]}
                     | {t for a in cfg["agents"].values() for t in a.get("univers", [])})
    return cfg, tickers


def creer(ch, prices, debut=None, garde_fous_sha=None):
    """Nouvelle équipe, tout en cash, qui commence à trader le jour `debut` (par défaut : demain)."""
    cfg, _ = charger_config(ch)
    g, h = gardefous.load(ch.garde_fous)
    i0 = prices.index_of(debut) if debut else len(prices)
    cap = float(cfg["capital_par_agent"])
    agents = {n: moteur.nouvel_agent(n, spec, cap, cfg["univers"]) for n, spec in cfg["agents"].items()}
    total = cap * len(agents)
    ref_i = min(i0, len(prices) - 1)
    etat = {
        "version": 1,
        "source_donnees": prices.source,
        "debut": prices.dates[i0] if i0 < len(prices) else None,
        "au": prices.dates[i0 - 1] if i0 > 0 else None,
        "garde_fous_sha": garde_fous_sha or h,
        "agents": agents,
        "reference": {"ticker": cfg["reference"], "capital": total, "parts": None, "historique": []},
        "equipe": {"capital": total, "historique": []},
    }
    if i0 < len(prices):
        etat["reference"]["parts"] = total / prices.px(cfg["reference"], ref_i)
    return etat


def avancer(etat, prices, g, cfg, propositions, jusqu_a=None, evolution=True, log=None):
    """Fait tourner chaque jour pas encore traité, jusqu'à `jusqu_a` inclus. Rend les événements."""
    ev = []
    start = sum(1 for d in prices.dates if etat["au"] and d <= etat["au"])
    end = len(prices) if jusqu_a is None else sum(1 for d in prices.dates if d <= jusqu_a)
    if etat["reference"]["parts"] is None and start < len(prices):
        etat["reference"]["parts"] = etat["reference"]["capital"] / prices.px(etat["reference"]["ticker"], start)
        etat["debut"] = prices.dates[start]
    for i in range(start, end):
        ev += moteur.jour(etat, prices, i, g)
        # Calendrier fixe (un jour de cotation sur N) : le même que l'on rattrape 1 jour ou 300.
        if evolution and i % cfg["evolution_tous_les_jours"] == 0:
            ev += entraineur.evoluer(etat, prices, i, g, cfg, propositions)
        if log and (i - start + 1) % 126 == 0:
            log("… %s" % prices.dates[i])
    return ev, max(0, end - start)


def lecons(evenements):
    """Ce qui mérite d'aller dans le savoir partagé de l'équipe."""
    out = []
    for e in evenements:
        if e["type"] in ("adoption", "coupe_circuit", "reprise", "concentration"):
            out.append({k: e[k] for k in ("date", "type", "agent", "texte", "source", "hypothese", "gain")
                        if k in e and e[k] is not None})
    return out


def sauver(ch, etat, evenements, propositions):
    ecrire_json(ch.etat, etat)
    ecrire_json(ch.propositions, propositions)
    savoir = lire_json(ch.savoir, []) + lecons(evenements)
    ecrire_json(ch.savoir, savoir[-1000:])
    os.makedirs(ch.etat_dir, exist_ok=True)
    with open(ch.journal, "a") as f:
        for e in evenements:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


def charger_prix(ch):
    _, tickers = charger_config(ch)
    cfg = lire_json(ch.config)
    return data.load_prices(tickers, ch.prix, cfg["reference"])
