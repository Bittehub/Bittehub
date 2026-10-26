# Rapport de recherche : améliorer le moteur de l'équipe

*26 octobre 2026. Tout est reproductible avec le code de ce dossier et les prix de
`donnees/recherche/`.*

## La question

Peut-on rendre l'équipe nettement meilleure en s'inspirant de ce que font les meilleurs gérants
et chercheurs, sans se tromper soi-même ? Le piège principal est le surapprentissage : tester des
centaines de variantes jusqu'à ce que l'une brille par hasard.

## Le protocole

1. **Données** : 30 ETF, cours ajustés Yahoo, de janvier 2003 à octobre 2026. Les ETF lancés
   tardivement sont remplacés partout par leur équivalent plus ancien (VWO→EEM, VEA→EFA,
   BND→AGG, BIL→SHY), comme le font leurs auteurs.
2. **Deux périodes** : conception sur 2014-2026, où se font tous les choix ; validation sur
   2004-2013 (crise de 2008 comprise), jamais regardée avant la sélection.
3. **Des stratégies publiées, avec leurs paramètres publiés** : aucun réglage taillé sur mesure.
4. **Chaque essai est consigné** (`essais.jsonl`, 81 essais), pour calculer le Sharpe dégonflé
   (Bailey & López de Prado, 2014).
5. **Sélection écrite avant la validation** (`selection.json`), avec ses critères de succès ;
   validation lancée une seule fois (`validation.lock`, `validation.json`).

Sharpe : en excès du rendement des bons du Trésor (SHY) dans les phases 1 à 3, sans taux sans
risque dans la phase 4 (comme les rapports de l'équipe). Coûts : 5 points de base par ordre.

## Phase 1 : les stratégies publiées, sur 2014-2026

| Stratégie (source) | Par an | Sharpe | Perte max | Corrélation au SPY |
|---|---:|---:|---:|---:|
| S&P 500 conservé (SPY) | +13,4 % | 0,74 | 33,1 % | 1,00 |
| 60/40 (SPY / IEF) | +8,8 % | 0,77 | 20,8 % | 0,97 |
| S&P 500 à volatilité gérée (Moreira & Muir, 2017) | +11,0 % | 0,73 | 23,0 % | 0,95 |
| All Weather (Bridgewater) | +6,1 % | 0,64 | 23,0 % | 0,52 |
| Filtre 200 jours (Paul Tudor Jones, Faber) | +9,1 % | 0,62 | 32,3 % | 0,71 |
| BAA équilibré (Keller, 2022) | +6,4 % | 0,59 | 15,3 % | 0,29 |
| Parité de risque sans levier | +4,9 % | 0,56 | 17,6 % | 0,55 |
| Rotation sectorielle (Faber, 2010) | +9,7 % | 0,56 | 31,8 % | 0,85 |
| DAA (Keller, 2018) | +5,2 % | 0,45 | 22,7 % | 0,63 |
| Accelerating Dual Momentum | +7,3 % | 0,45 | 36,3 % | 0,54 |
| GTAA 5 (Faber, 2007) | +4,4 % | 0,43 | 16,0 % | 0,75 |
| Global Equities Momentum (Antonacci, 2014) | +7,0 % | 0,41 | 33,1 % | — |
| BAA agressif (Keller, 2022) | +4,5 % | 0,37 | 19,2 % | — |
| Momentum de série temporelle (AQR, sans vente à découvert) | +3,3 % | 0,37 | 12,5 % | 0,55 |
| VAA-G4 (Keller, 2017) | +3,8 % | 0,27 | 24,3 % | — |

Aucune ne bat le S&P 500 en rendement sur cette période exceptionnelle pour les grandes
entreprises américaines. La gestion de la volatilité réduit fortement les pertes maximales mais
pas le Sharpe ; le cash rémunéré ne change rien tant que les taux étaient nuls.

## Phase 2 : le diagnostic de l'équipe

| Agent actuel, 2014-2026 | Par an | Sharpe | Perte max | Corrélation au SPY |
|---|---:|---:|---:|---:|
| contrarien | +11,3 % | 0,64 | 30,4 % | 0,97 |
| navigateur | +8,3 % | 0,58 | 21,2 % | 0,75 |
| chasseur | +8,4 % | 0,51 | 21,7 % | 0,72 |
| pilier | +8,3 % | 0,49 | 33,1 % | 0,88 |

L'équipe était un S&P 500 déguisé : des agents très corrélés, qui perdent en même temps.

## Phase 3 : les équipes candidates, puis la sélection

| Équipe (2014-2026, capital rééquilibré chaque mois) | Par an | Sharpe | Perte max |
|---|---:|---:|---:|
| T0 actuelle (chasseur, contrarien, pilier, navigateur) | +9,2 % | 0,61 | 25,1 % |
| T1 vigie (BAA) à la place du pilier | +8,8 % | 0,67 | 20,5 % |
| **T2 contrarien, navigateur, vigie (BAA), rempart (All Weather)** | **+8,2 %** | **0,74** | **18,1 %** |
| T3 chasseur, contrarien, vigie, rempart | +8,3 % | 0,71 | 18,8 % |
| T4 = T1 avec volatilité gérée à 15 % | +8,0 % | 0,65 | 17,1 % |

Règle fixée à l'avance : le meilleur Sharpe, puis la plus faible perte maximale. **T2** est
retenue. Sharpe dégonflé compte tenu des 81 essais : **93 %** de probabilité que son vrai Sharpe
dépasse le meilleur que le hasard aurait produit (seuil du hasard : 0,31).

## Phase 4 : la validation unique, sur 2004-2013

| 2004-03 → 2013-12 | Par an | Sharpe | Perte max | Pire année |
|---|---:|---:|---:|---:|
| **T2** | **+9,0 %** | **0,66** | 22,1 % | −8,8 % |
| T0 équipe actuelle | +8,5 % | 0,50 | 19,4 % | −7,4 % |
| 60/40 | +6,5 % | 0,40 | 32,0 % | −17,4 % |
| SPY | +6,9 % | 0,30 | 54,4 % | −35,6 % |

Les 4 critères écrits à l'avance sont remplis : Sharpe de T2 supérieur au SPY, à l'équipe
actuelle et au 60/40 ; perte maximale de T2 inférieure à celle du SPY. Vedette : la vigie (BAA),
+12,1 % par an, Sharpe 0,89, perte maximale 11,1 %, aucune année négative.

Un premier lancement a planté avant d'afficher quoi que ce soit (un ETF sans prix en 2004) ; la
correction et la relance sont consignées dans `plantage-validation.txt`.

## Phase 5 : le moteur complet (coupe-circuit, solidarité, évolution)

Sharpe sans taux sans risque, comme dans les rapports de l'équipe.

| | 2004-2013 | | 2014-2026 | |
|---|---:|---:|---:|---:|
| | Sharpe | Perte max | Sharpe | Perte max |
| Ancienne équipe, évolution automatique (configuration de `main`) | 0,58 | 24,3 % | 0,75 | 22,6 % |
| Ancienne équipe, réglages figés | 0,67 | 15,6 % | 0,72 | 23,1 % |
| Nouvelle équipe, évolution automatique | 0,87 | 21,9 % | 0,92 | 16,1 % |
| **Nouvelle équipe, mode conseil** | **1,02** | **13,2 %** | **0,90** | **17,4 %** |
| SPY | 0,43 | 55,2 % | 0,84 | 33,7 % |

Rendement annuel de la nouvelle équipe en mode conseil : +8,7 % (2004-2013, SPY +7,0 %) et
+8,1 % (2014-2026, SPY +13,7 %).

**L'évolution automatique a fait plus de mal que de bien.** En 2008, elle a trouvé des réglages
qui avaient bien marché en 2005-2007 et a fait reprendre le contrarien en pleine chute, plusieurs
fois : perte maximale de 57 à 63 % malgré le coupe-circuit. D'où le **mode conseil** : l'entraîneur
recommande, un humain décide. Ce choix a été fait après avoir vu 2004-2013 ; il n'est donc pas
validé à l'aveugle, mais c'est le choix le plus simple (garder les paramètres publiés) et
2014-2026 montre aussi que l'évolution n'apportait presque rien (+0,02 de Sharpe).

## Ce qui change dans le moteur

- Stratégies `baa` (vigie) et `all_weather` (rempart), identiques au banc sur 813 dates.
- Solidarité de capital : tous les 21 jours, le capital des agents actifs est remis à parts
  égales (tous ou aucun, pour conserver exactement la somme) ; valeur liquidative par agent.
- Évolution en trois modes : `auto`, `conseil`, `non` ; commande humaine `adopter`.
- Un titre pas encore coté est ignoré au lieu de faire planter la simulation.
- Indices larges élargis (exemptés du plafond de 35 % par titre) : SPY, IWM, EFA, EEM, SHY,
  IEF, TLT, AGG, LQD, TIP. **Garde-fou à approuver avant l'équipe réelle.**

## Limites, sans fard

- « Jamais vue » vaut pour moi, pas pour les auteurs : Keller a conçu BAA en 2022 sur des données
  qui incluent 2004-2013 ; Faber a publié en 2007. Le succès de la vigie en 2008 est donc en partie
  celui de son concepteur.
- Sur 2014-2026, l'équipe rapporte nettement moins que le S&P 500 (+8,1 % contre +13,7 % par an).
  Son avantage est le risque : une perte maximale deux fois plus faible et un meilleur Sharpe sur
  les deux périodes. Qui supporte une baisse de 34 à 55 % gagne plus avec le S&P 500.
- Deux périodes ne font pas une preuve : seuls des mois de papier en conditions réelles diront
  si ces résultats tiennent.
- Ni impôts, ni spread réel ; cours de clôture uniquement.
- Ce n'est pas un conseil financier.

## Reproduire

```bash
python3 -m recherche conception        # la phase 1 (consigne de nouveaux essais)
python3 -m unittest discover -s tests  # 30 tests
```
