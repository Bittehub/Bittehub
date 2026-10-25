import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equipe import data, entraineur, gardefous, moteur, strategies, synthetique  # noqa: E402
from equipe.equipe import Chemins, avancer, creer  # noqa: E402
from equipe.portefeuille import Portefeuille  # noqa: E402

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
G, _ = gardefous.load(os.path.join(RACINE, "config", "garde-fous.json"))
with open(os.path.join(RACINE, "config", "equipe.json")) as _f:
    CFG = json.load(_f)
TICKERS = sorted(set(CFG["univers"]))
CFG_RAPIDE = dict(CFG, plis=3, longueur_pli=30, evolution_tous_les_jours=5)


def marche(jours=700, graine=3):
    dates, closes = synthetique.generate(TICKERS, jours, graine)
    return data.Prices(dates, closes, "synthetique")


class Bac(unittest.TestCase):
    """Un dossier jetable avec la vraie config et un marché synthétique."""

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        shutil.copytree(os.path.join(RACINE, "config"), os.path.join(self.dir, "config"))
        self.ch = Chemins(self.dir)
        self.prices = marche()

    def tearDown(self):
        shutil.rmtree(self.dir)


class PasDeRegardVersLeFutur(unittest.TestCase):
    def test_strategies_ignorent_le_jour_meme_et_apres(self):
        p = marche()
        i = 500
        futur = copy.deepcopy(p)
        for t in futur.closes:
            for k in range(i, len(p)):
                futur.closes[t][k] *= 3.0
        for nom, spec in CFG["agents"].items():
            u = spec.get("univers", CFG["univers"])
            par = strategies.clamp(spec["strategie"], spec["parametres"])
            self.assertEqual(strategies.targets(spec["strategie"], p, i, u, par),
                             strategies.targets(spec["strategie"], futur, i, u, par), nom)

    def test_entraineur_ignore_le_futur(self):
        p = marche()
        i = 520
        e1 = creer_etat(p, 300)
        avancer(e1, p, G, CFG_RAPIDE, [], p.dates[i - 1], evolution=False)
        e2 = copy.deepcopy(e1)
        ev1 = entraineur.evoluer(e1, p, i, G, CFG_RAPIDE, [])
        ev2 = entraineur.evoluer(e2, p.truncated(i + 1), i, G, CFG_RAPIDE, [])
        self.assertEqual(ev1, ev2)
        self.assertEqual(e1["agents"], e2["agents"])


def creer_etat(prices, debut_i):
    ch = Chemins(RACINE)
    return creer(ch, prices, debut=prices.dates[debut_i])


class GardeFous(unittest.TestCase):
    def test_plafond_par_titre_cash_min_et_univers(self):
        w = gardefous.clip_targets({"SPY": 0.9, "QQQ": 0.5, "BTC": 0.3, "TLT": -0.2}, G, CFG["univers"])
        self.assertNotIn("BTC", w)
        self.assertNotIn("TLT", w)
        self.assertTrue(all(x <= G["poids_max_par_titre"] + 1e-12 for x in w.values()))
        self.assertLessEqual(sum(w.values()), 1 - G["cash_min"] + 1e-12)

    def test_pas_de_levier(self):
        w = gardefous.clip_targets({t: 0.3 for t in CFG["univers"]}, G, CFG["univers"])
        self.assertAlmostEqual(sum(w.values()), 1 - G["cash_min"])

    def test_concentration_equipe(self):
        cibles = {"a": {"SPY": 9000}, "b": {"SPY": 9000, "TLT": 1000}}
        out, coupes = gardefous.team_overlay(cibles, {"SPY": 3000}, 40000, G)
        total_spy = out["a"]["SPY"] + out["b"]["SPY"] + 3000
        self.assertAlmostEqual(total_spy, G["poids_max_equipe_par_titre"] * 40000)
        self.assertEqual(out["b"]["TLT"], 1000)
        self.assertIn("SPY", coupes)

    def test_rotation_plafonnee(self):
        trades, f = gardefous.limit_turnover({"SPY": 9000, "TLT": -5000}, 10000, G)
        self.assertAlmostEqual(sum(abs(v) for v in trades.values()), G["rotation_max_par_jour"] * 10000)
        self.assertLess(f, 1)

    def test_modification_detectee(self):
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "g.json")
            shutil.copy(os.path.join(RACINE, "config", "garde-fous.json"), path)
            _, h = gardefous.load(path)
            with open(path) as f:
                g = json.load(f)
            g["poids_max_par_titre"] = 1.0
            with open(path, "w") as f:
                json.dump(g, f)
            with self.assertRaises(gardefous.GardeFousModifies):
                gardefous.verify(path, h)
        finally:
            shutil.rmtree(d)

    def test_refuse_le_reel(self):
        d = tempfile.mkdtemp()
        try:
            path = os.path.join(d, "g.json")
            with open(path, "w") as f:
                json.dump(dict(G, mode="reel"), f)
            with self.assertRaises(SystemExit):
                gardefous.load(path)
        finally:
            shutil.rmtree(d)


class Portefeuilles(unittest.TestCase):
    def test_aller_retour_sans_couts_conserve_le_cash(self):
        p = marche(50)
        g = dict(G, glissement_bps=0)
        pf = Portefeuille(10000)
        pf.executer({"SPY": 4000, "TLT": 3000}, p, 10, g)
        self.assertAlmostEqual(pf.valeur(p, 10), 10000, places=6)
        pf.executer({t: -v for t, v in pf.notionnels(p, 10).items()}, p, 10, g)
        self.assertAlmostEqual(pf.cash, 10000, places=6)
        self.assertEqual(pf.positions, {})

    def test_jamais_de_cash_negatif_ni_de_vente_a_decouvert(self):
        p = marche(50)
        pf = Portefeuille(1000)
        pf.executer({"SPY": 5000, "QQQ": 5000, "TLT": -500}, p, 10, G)
        self.assertGreaterEqual(pf.cash, -1e-9)
        self.assertNotIn("TLT", pf.positions)

    def test_glissement_coute(self):
        p = marche(50)
        pf = Portefeuille(10000)
        pf.executer({"SPY": 5000}, p, 10, G)
        self.assertLess(pf.valeur(p, 10), 10000)


class Equipe(Bac):
    def test_coupe_circuit_puis_cash(self):
        p = self.prices
        e = creer(self.ch, p, debut=p.dates[300])
        avancer(e, p, G, CFG_RAPIDE, [], p.dates[350], evolution=False)
        crash = copy.deepcopy(p)
        for t in crash.closes:
            for k in range(351, len(p)):
                crash.closes[t][k] *= 0.5
        avancer(e, crash, G, CFG_RAPIDE, [], p.dates[352], evolution=False)
        pauses = 0
        for n, a in e["agents"].items():
            vals = [v for _, v in a["historique"]]
            if 1 - min(vals[-2:]) / max(vals) >= G["drawdown_max_agent"]:
                self.assertTrue(a["en_pause"], n)
            if a["en_pause"]:
                pauses += 1
                self.assertEqual(a["portefeuille"]["positions"], {}, n)
        self.assertGreater(pauses, 0)

    def test_rattrapage_jour_par_jour_identique_au_bloc(self):
        p = self.prices
        bloc = creer(self.ch, p, debut=p.dates[300])
        avancer(bloc, p, G, CFG_RAPIDE, [], p.dates[420])
        pas = creer(self.ch, p, debut=p.dates[300])
        for i in range(300, 421):
            avancer(pas, p, G, CFG_RAPIDE, [], p.dates[i])
        self.assertEqual(json.dumps(bloc, sort_keys=True), json.dumps(pas, sort_keys=True))

    def test_relancer_ne_refait_rien(self):
        p = self.prices
        e = creer(self.ch, p, debut=p.dates[300])
        avancer(e, p, G, CFG_RAPIDE, [], p.dates[360])
        avant = json.dumps(e, sort_keys=True)
        ev, n = avancer(e, p, G, CFG_RAPIDE, [], p.dates[360])
        self.assertEqual((ev, n), ([], 0))
        self.assertEqual(json.dumps(e, sort_keys=True), avant)

    def test_parametres_toujours_dans_les_bornes_et_propositions_traitees(self):
        p = self.prices
        e = creer(self.ch, p, debut=p.dates[300])
        props = [{"id": "x1", "agent": "chasseur", "parametres": {"lookback": 60}, "hypothese": "test",
                  "statut": "en_attente"}]
        avancer(e, p, G, CFG_RAPIDE, props, None)
        for n, a in e["agents"].items():
            for k, (lo, hi, typ) in strategies.bounds(a["strategie"]).items():
                self.assertTrue(lo <= a["parametres"][k] <= hi, (n, k))
                self.assertIsInstance(a["parametres"][k], typ)
        self.assertIn(props[0]["statut"], ("adoptee", "rejetee"))
        self.assertIn("evaluee_le", props[0])

    def test_valeur_equipe_egale_somme_des_agents(self):
        p = self.prices
        e = creer(self.ch, p, debut=p.dates[300])
        avancer(e, p, G, CFG_RAPIDE, [], p.dates[400])
        total = sum(a["historique"][-1][1] for a in e["agents"].values())
        self.assertAlmostEqual(e["equipe"]["historique"][-1][1], total, places=1)
        self.assertEqual(len(e["equipe"]["historique"]), 101)


class Donnees(unittest.TestCase):
    def test_un_dividende_ne_reecrit_pas_le_passe(self):
        cache = {"2026-01-02": 100.0, "2026-01-05": 101.0}
        # Nouveau téléchargement : un dividende de 2 % a réajusté tout l'historique vers le bas.
        nouveau = {"2026-01-02": 98.0, "2026-01-05": 98.98, "2026-01-06": 100.96}
        out = data.merge(cache, nouveau)
        self.assertEqual(out["2026-01-02"], 100.0)
        self.assertEqual(out["2026-01-05"], 101.0)
        self.assertAlmostEqual(out["2026-01-06"], 101.0 * 100.96 / 98.98)

    def test_cache_vide(self):
        self.assertEqual(data.merge({}, {"2026-01-02": 5.0}), {"2026-01-02": 5.0})


class Mutations(unittest.TestCase):
    def test_mutations_dans_les_bornes(self):
        import random
        rng = random.Random(1)
        for strat, (_, b) in strategies.STRATEGIES.items():
            p = strategies.clamp(strat, {k: lo for k, (lo, hi, t) in b.items()})
            for _ in range(200):
                p = entraineur._mutation(strat, p, rng)
                for k, (lo, hi, t) in b.items():
                    self.assertTrue(lo <= p[k] <= hi, (strat, k, p[k]))


if __name__ == "__main__":
    unittest.main()
