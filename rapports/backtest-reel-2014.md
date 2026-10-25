# Rapport de l'équipe au 2026-10-23

3222 jours de cotation depuis le 2014-01-02. Mode papier.

| | Valeur | Rendement | Annualisé | Vol | Sharpe | Drawdown max |
|---|---:|---:|---:|---:|---:|---:|
| **Équipe** | 80 633 $ | +101.6 % | +5.6 % | 8.2 % | 0.71 | 15.1 % |
| Référence SPY | 205 632 $ | +414.1 % | +13.7 % | 17.1 % | 0.84 | 33.7 % |
| chasseur (gén. 9) | 22 979 $ | +129.9 % | +6.7 % | 13.9 % | 0.54 | 22.1 % |
| contrarien (gén. 7) | 12 743 $ | +27.4 % | +1.9 % | 2.9 % | 0.67 | 5.4 % |
| gardien (gén. 1) | 20 391 $ | +104.0 % | +5.7 % | 7.4 % | 0.79 | 16.0 % |
| navigateur (gén. 6) | 24 520 $ | +145.3 % | +7.3 % | 11.9 % | 0.65 | 20.6 % |

## Réglages actuels

- **chasseur** (momentum) : lookback=101, skip=9, top_n=3, rebalance_days=18, filtre_absolu=0
- **contrarien** (reversion) : lookback=44, trend_sma=200, top_n=3, z_entree=2.1973, rebalance_days=4
- **gardien** (defensif) : vol_lookback=60, vol_cible=0.08, rebalance_days=21
- **navigateur** (tendance) : sma=198, max_actifs=7, rebalance_days=5

## Événements récents

- 2025-10-08 · chasseur passe en génération 8 (mentor:navigateur) : rebalance_days 32→18, gain de score +0.28 (t=4.0), 6/6 plis gagnés.
- 2026-10-07 · chasseur passe en génération 9 (mutation) : skip 5→9, top_n 4→3, gain de score +0.28 (t=5.9), 6/6 plis gagnés.

## Derniers éléments du savoir partagé

- 2020-03-12 · chasseur perd 21.4 % depuis son pic : tout en cash, pause et rééducation.
- 2020-03-18 · navigateur perd 20.1 % depuis son pic : tout en cash, pause et rééducation.
- 2020-03-27 · chasseur reprend le travail : score de validation 0.33 sur 6 plis.
- 2020-04-03 · navigateur reprend le travail : score de validation 0.45 sur 6 plis.
- 2020-04-13 · contrarien passe en génération 6 (mutation) : lookback 31→44, rebalance_days 10→8, gain de score +1.69 (t=3.1), 6/6 plis gagnés.
- 2020-07-08 · contrarien passe en génération 7 (mutation) : rebalance_days 8→4, gain de score +1.02 (t=3.0), 6/6 plis gagnés.
- 2021-05-07 · navigateur passe en génération 3 (mutation) : sma 180→199, gain de score +0.35 (t=3.7), 6/6 plis gagnés.
- 2021-09-15 · navigateur passe en génération 4 (mutation) : sma 199→155, max_actifs 6→8, gain de score +0.32 (t=3.1), 6/6 plis gagnés.
- 2022-12-07 · chasseur passe en génération 5 (mutation) : lookback 158→101, gain de score +0.38 (t=5.0), 6/6 plis gagnés.
- 2023-11-21 · chasseur passe en génération 6 (mutation) : top_n 5→4, filtre_absolu 1→0, gain de score +0.29 (t=3.8), 6/6 plis gagnés.
- 2024-05-08 · navigateur passe en génération 5 (mutation) : max_actifs 8→7, rebalance_days 10→5, gain de score +0.31 (t=3.5), 6/6 plis gagnés.
- 2024-08-05 · chasseur passe en génération 7 (mutation) : rebalance_days 21→32, gain de score +0.26 (t=4.1), 6/6 plis gagnés.
- 2025-02-04 · navigateur passe en génération 6 (mutation) : sma 155→198, gain de score +0.28 (t=3.4), 6/6 plis gagnés.
- 2025-10-08 · chasseur passe en génération 8 (mentor:navigateur) : rebalance_days 32→18, gain de score +0.28 (t=4.0), 6/6 plis gagnés.
- 2026-10-07 · chasseur passe en génération 9 (mutation) : skip 5→9, top_n 4→3, gain de score +0.28 (t=5.9), 6/6 plis gagnés.

## L'évolution a-t-elle servi ?

| | Rendement | Sharpe | Drawdown max |
|---|---:|---:|---:|
| Équipe qui évolue | +101.6 % | 0.71 | 15.1 % |
| Même équipe, réglages figés | +88.8 % | 0.76 | 11.3 % |
| Référence SPY | +414.1 % | 0.84 | 33.7 % |

Écart de Sharpe dû à l'évolution : -0.05. Sur un seul historique, un écart de cette taille peut être de la chance : à confirmer sur d'autres périodes et en papier.
