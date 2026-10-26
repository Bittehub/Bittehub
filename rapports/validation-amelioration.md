# Validation de l'équipe améliorée

Changements testés (branche `amelioration-equipe`) :

- le contrarien place dans le S&P 500 l'argent qu'il n'utilise pas ;
- le pilier (double momentum : S&P 500 ou EFA, sinon IEF) remplace le gardien (parité de risque) ;
- les indices larges SPY, EFA et IEF échappent aux plafonds par titre et d'équipe.

Méthode : les changements ont été choisis en ne regardant que 2014-2020. La période 2021-2026 n'a
servi qu'une fois, à la fin, sans retouche après. Les deux équipes tournent avec l'évolution
activée, 10 000 $ fictifs par agent, glissement de 5 points de base par ordre, prix Yahoo ajustés.

## Conception : 2014-01-02 → 2020-12-31

| | Rendement | Par an | Sharpe | Perte max |
|---|---:|---:|---:|---:|
| Ancienne équipe | +42,3 % | +5,2 % | 0,67 | 15,1 % |
| Nouvelle équipe | +72,2 % | +8,1 % | 0,67 | 24,1 % |
| SPY conservé | +134,3 % | +12,9 % | 0,78 | 33,7 % |

## Validation : 2021-01-04 → 2026-10-23

| | Rendement | Par an | Sharpe | Perte max |
|---|---:|---:|---:|---:|
| Ancienne équipe | +37,8 % | +5,7 % | 0,72 | 13,6 % |
| Nouvelle équipe | +68,0 % | +9,4 % | 0,78 | 20,0 % |
| SPY conservé | +122,5 % | +14,8 % | 0,92 | 24,5 % |

Par agent sur la validation : chasseur +45,5 %, contrarien +89,9 % (contre +13,5 % avant),
pilier +70,1 % (le gardien faisait +28,0 %), navigateur +66,4 %.

## Conclusion

- L'amélioration tient sur la période jamais utilisée : environ +4 points de rendement par an, un
  Sharpe un peu meilleur, au prix d'une perte maximale plus forte (20 % contre 14 %).
- L'essentiel du gain vient d'être plus investi, pas d'une meilleure sélection.
- L'équipe reste nettement derrière le S&P 500 conservé, en rendement comme en Sharpe. Son seul
  avantage est une perte maximale un peu plus faible.
- En l'état, rien ne justifie d'y mettre de l'argent réel. L'intérêt est d'observer le système en
  papier et d'apprendre.

## Erratum (26 octobre 2026)

Les chiffres ci-dessus ont été calculés avec deux défauts du moteur, corrigés depuis :

- une cible freinée par le plafond de rotation était recalculée chaque jour au lieu d'être
  poursuivie, ce qui pénalisait surtout le chasseur ;
- avec l'évolution coupée, un agent stoppé par le coupe-circuit ne reprenait jamais, ce qui
  faussait toute comparaison « équipe figée contre équipe qui évolue ».

Refaite avec le moteur corrigé, la comparaison donne (Sharpe de l'équipe) :

| | 2014-2020 | 2021-2026 |
|---|---:|---:|
| Ancien chasseur, réglages figés | 0,55 | 0,67 |
| Ancien chasseur, avec évolution | 0,64 | 0,81 |
| Nouveau chasseur, réglages figés | 0,60 | 0,78 |
| Nouveau chasseur, avec évolution | 0,61 | 0,80 |
| SPY conservé | 0,78 | 0,92 |

L'évolution apporte bien quelque chose à l'ancien chasseur. Le nouveau chasseur (momentum ajusté
du risque) atteint le même niveau d'équipe sans en dépendre, et c'est lui qui est retenu.
L'équipe reste derrière le S&P 500 conservé.
