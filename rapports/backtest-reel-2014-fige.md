# Rapport de l'équipe au 2026-10-23

3222 jours de cotation depuis le 2014-01-02. Mode papier.

| | Valeur | Rendement | Annualisé | Vol | Sharpe | Drawdown max |
|---|---:|---:|---:|---:|---:|---:|
| **Équipe** | 75 505 $ | +88.8 % | +5.1 % | 6.9 % | 0.76 | 11.3 % |
| Référence SPY | 205 632 $ | +414.1 % | +13.7 % | 17.1 % | 0.84 | 33.7 % |
| chasseur ⏸ (gén. 1) | 8 726 $ | -12.7 % | -1.1 % | 5.1 % | -0.18 | 20.5 % |
| contrarien (gén. 1) | 11 564 $ | +15.6 % | +1.1 % | 5.6 % | 0.23 | 16.1 % |
| gardien (gén. 1) | 20 391 $ | +104.0 % | +5.7 % | 7.4 % | 0.79 | 16.0 % |
| navigateur (gén. 1) | 34 824 $ | +248.3 % | +10.3 % | 12.3 % | 0.86 | 17.7 % |

## Réglages actuels

- **chasseur** (momentum) : lookback=126, skip=5, top_n=3, rebalance_days=21, filtre_absolu=1
- **contrarien** (reversion) : lookback=20, trend_sma=200, top_n=3, z_entree=1.5, rebalance_days=5
- **gardien** (defensif) : vol_lookback=60, vol_cible=0.08, rebalance_days=21
- **navigateur** (tendance) : sma=200, max_actifs=6, rebalance_days=10

## Événements récents

- Rien de notable.

## Derniers éléments du savoir partagé

- 2015-11-13 · chasseur perd 20.5 % depuis son pic : tout en cash, pause et rééducation.
