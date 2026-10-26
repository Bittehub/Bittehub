# Rapport de l'équipe au 2026-10-23

3222 jours de cotation depuis le 2014-01-02. Mode papier.

| | Valeur | Rendement | Annualisé | Vol | Sharpe | Drawdown max |
|---|---:|---:|---:|---:|---:|---:|
| **Équipe** | 112 917 $ | +182.4 % | +8.5 % | 12.9 % | 0.69 | 24.1 % |
| Référence SPY | 205 632 $ | +414.1 % | +13.7 % | 17.1 % | 0.84 | 33.7 % |
| chasseur (gén. 6) | 20 308 $ | +103.1 % | +5.7 % | 14.6 % | 0.45 | 22.0 % |
| contrarien (gén. 5) | 38 996 $ | +290.1 % | +11.2 % | 15.6 % | 0.76 | 30.4 % |
| pilier (gén. 2) | 26 213 $ | +162.2 % | +7.8 % | 14.3 % | 0.60 | 26.5 % |
| navigateur (gén. 7) | 27 399 $ | +174.1 % | +8.2 % | 11.6 % | 0.74 | 19.7 % |

## Réglages actuels

- **chasseur** (momentum) : lookback=20, skip=7, top_n=4, rebalance_days=12, filtre_absolu=0
- **contrarien** (reversion) : lookback=60, trend_sma=200, top_n=4, z_entree=0.7045, rebalance_days=10
- **pilier** (double_momentum) : lookback=252, rebalance_days=16
- **navigateur** (tendance) : sma=180, max_actifs=8, rebalance_days=10

## Événements récents

- 2025-09-24 · navigateur passe en génération 7 (mentor:chasseur) : rebalance_days 7→10, gain de score +0.25 (t=3.6), 6/6 plis gagnés.
- 2026-04-30 · chasseur passe en génération 5 (mentor:contrarien) : lookback 92→76, rebalance_days 13→12, gain de score +0.39 (t=5.8), 6/6 plis gagnés.
- 2026-09-16 · chasseur passe en génération 6 (mutation) : lookback 76→20, skip 5→7, gain de score +0.90 (t=3.3), 6/6 plis gagnés.

## Derniers éléments du savoir partagé

- 2021-07-06 · contrarien passe en génération 2 (mutation) : lookback 20→27, z_entree 1.5→1.0719, gain de score +0.31 (t=3.3), 6/6 plis gagnés.
- 2021-11-17 · navigateur passe en génération 4 (mutation) : max_actifs 8→10, rebalance_days 10→5, gain de score +0.34 (t=3.1), 6/6 plis gagnés.
- 2022-06-13 · contrarien perd 21.5 % depuis son pic : tout en cash, pause et rééducation.
- 2022-07-01 · contrarien reprend le travail : score de validation 0.64 sur 6 plis.
- 2022-09-22 · pilier perd 20.6 % depuis son pic : tout en cash, pause et rééducation.
- 2022-10-11 · pilier reprend le travail : score de validation 0.17 sur 6 plis.
- 2023-08-28 · chasseur passe en génération 4 (mentor:contrarien) : lookback 158→92, rebalance_days 21→13, gain de score +0.82 (t=4.6), 6/6 plis gagnés.
- 2023-11-14 · contrarien passe en génération 3 (mentor:pilier) : lookback 27→60, rebalance_days 5→10, gain de score +0.30 (t=5.2), 6/6 plis gagnés.
- 2024-01-05 · contrarien passe en génération 4 (mutation) : z_entree 1.0719→0.7045, gain de score +0.29 (t=3.7), 6/6 plis gagnés.
- 2024-09-03 · navigateur passe en génération 5 (mutation) : rebalance_days 5→14, gain de score +0.32 (t=4.8), 6/6 plis gagnés.
- 2024-10-22 · navigateur passe en génération 6 (mutation) : max_actifs 10→8, rebalance_days 14→7, gain de score +0.37 (t=6.2), 6/6 plis gagnés.
- 2025-05-22 · contrarien passe en génération 5 (mutation) : top_n 3→4, gain de score +0.30 (t=3.1), 6/6 plis gagnés.
- 2025-09-24 · navigateur passe en génération 7 (mentor:chasseur) : rebalance_days 7→10, gain de score +0.25 (t=3.6), 6/6 plis gagnés.
- 2026-04-30 · chasseur passe en génération 5 (mentor:contrarien) : lookback 92→76, rebalance_days 13→12, gain de score +0.39 (t=5.8), 6/6 plis gagnés.
- 2026-09-16 · chasseur passe en génération 6 (mutation) : lookback 76→20, skip 5→7, gain de score +0.90 (t=3.3), 6/6 plis gagnés.
