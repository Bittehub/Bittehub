# Rapport de l'équipe au 2026-10-23

3222 jours de cotation depuis le 2014-01-02. Mode papier.

| | Valeur | Rendement | Annualisé | Vol | Sharpe | Drawdown max |
|---|---:|---:|---:|---:|---:|---:|
| **Équipe** | 120 733 $ | +201.9 % | +9.0 % | 12.6 % | 0.75 | 25.6 % |
| Référence SPY | 205 632 $ | +414.1 % | +13.7 % | 17.1 % | 0.84 | 33.7 % |
| chasseur (gén. 14) | 22 912 $ | +129.2 % | +6.7 % | 13.2 % | 0.56 | 23.9 % |
| contrarien (gén. 6) | 49 212 $ | +392.3 % | +13.3 % | 15.6 % | 0.88 | 30.2 % |
| pilier (gén. 2) | 24 162 $ | +141.7 % | +7.1 % | 14.3 % | 0.55 | 26.5 % |
| navigateur (gén. 8) | 24 446 $ | +144.5 % | +7.2 % | 11.3 % | 0.67 | 22.0 % |

## Réglages actuels

- **chasseur** (momentum_ajuste) : lookback=20, top_n=5, rebalance_days=16, filtre_absolu=1
- **contrarien** (reversion) : lookback=36, trend_sma=158, top_n=3, z_entree=1.5, rebalance_days=20
- **pilier** (double_momentum) : lookback=252, rebalance_days=16
- **navigateur** (tendance) : sma=250, max_actifs=10, rebalance_days=18

## Événements récents

- 2025-07-15 · chasseur passe en génération 9 (mutation) : lookback 85→38, rebalance_days 23→30, gain de score +0.52 (t=4.6), 6/6 plis gagnés.
- 2025-10-08 · chasseur passe en génération 10 (mentor:navigateur) : rebalance_days 30→24, gain de score +0.33 (t=4.7), 6/6 plis gagnés.
- 2025-12-26 · chasseur passe en génération 11 (mentor:contrarien) : lookback 38→37, rebalance_days 24→20, gain de score +0.49 (t=3.3), 6/6 plis gagnés.
- 2026-02-18 · chasseur passe en génération 12 (mutation) : lookback 37→20, gain de score +0.41 (t=3.9), 6/6 plis gagnés.
- 2026-05-14 · navigateur passe en génération 8 (mentor:chasseur) : rebalance_days 17→18, gain de score +0.27 (t=3.4), 6/6 plis gagnés.
- 2026-06-12 · chasseur passe en génération 13 (mutation) : rebalance_days 20→16, gain de score +0.83 (t=4.6), 6/6 plis gagnés.
- 2026-06-22 · contrarien passe en génération 6 (mutation) : trend_sma 200→158, rebalance_days 16→20, gain de score +0.39 (t=4.5), 6/6 plis gagnés.
- 2026-09-30 · chasseur passe en génération 14 (mutation) : top_n 4→5, gain de score +0.36 (t=5.7), 6/6 plis gagnés.

## Derniers éléments du savoir partagé

- 2022-09-22 · pilier perd 20.0 % depuis son pic : tout en cash, pause et rééducation.
- 2022-10-11 · pilier reprend le travail : score de validation 0.13 sur 6 plis.
- 2023-05-03 · chasseur passe en génération 6 (mentor:contrarien) : lookback 189→112, rebalance_days 12→14, gain de score +0.33 (t=4.1), 6/6 plis gagnés.
- 2023-09-26 · chasseur passe en génération 7 (mutation) : lookback 112→85, gain de score +0.56 (t=3.3), 6/6 plis gagnés.
- 2024-02-20 · navigateur passe en génération 6 (mutation) : rebalance_days 17→9, gain de score +0.29 (t=3.0), 6/6 plis gagnés.
- 2024-11-26 · chasseur passe en génération 8 (mutation) : rebalance_days 14→23, gain de score +0.42 (t=4.6), 6/6 plis gagnés.
- 2025-03-05 · navigateur passe en génération 7 (mutation) : sma 212→250, rebalance_days 9→17, gain de score +0.55 (t=3.2), 6/6 plis gagnés.
- 2025-07-15 · chasseur passe en génération 9 (mutation) : lookback 85→38, rebalance_days 23→30, gain de score +0.52 (t=4.6), 6/6 plis gagnés.
- 2025-10-08 · chasseur passe en génération 10 (mentor:navigateur) : rebalance_days 30→24, gain de score +0.33 (t=4.7), 6/6 plis gagnés.
- 2025-12-26 · chasseur passe en génération 11 (mentor:contrarien) : lookback 38→37, rebalance_days 24→20, gain de score +0.49 (t=3.3), 6/6 plis gagnés.
- 2026-02-18 · chasseur passe en génération 12 (mutation) : lookback 37→20, gain de score +0.41 (t=3.9), 6/6 plis gagnés.
- 2026-05-14 · navigateur passe en génération 8 (mentor:chasseur) : rebalance_days 17→18, gain de score +0.27 (t=3.4), 6/6 plis gagnés.
- 2026-06-12 · chasseur passe en génération 13 (mutation) : rebalance_days 20→16, gain de score +0.83 (t=4.6), 6/6 plis gagnés.
- 2026-06-22 · contrarien passe en génération 6 (mutation) : trend_sma 200→158, rebalance_days 16→20, gain de score +0.39 (t=4.5), 6/6 plis gagnés.
- 2026-09-30 · chasseur passe en génération 14 (mutation) : top_n 4→5, gain de score +0.36 (t=5.7), 6/6 plis gagnés.

## L'évolution a-t-elle servi ?

| | Rendement | Sharpe | Drawdown max |
|---|---:|---:|---:|
| Équipe qui évolue | +201.9 % | 0.75 | 25.6 % |
| Même équipe, réglages figés | +175.1 % | 0.68 | 23.3 % |
| Référence SPY | +414.1 % | 0.84 | 33.7 % |

Écart de Sharpe dû à l'évolution : +0.07. Sur un seul historique, un écart de cette taille peut être de la chance : à confirmer sur d'autres périodes et en papier.
