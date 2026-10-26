# Équipe de trading papier

Quatre agents aux métiers différents, chacun avec son portefeuille et son capital de départ. Ils
tradent chaque jour en papier, se coordonnent, et font évoluer leurs réglages. Une évolution n'est
adoptée que si elle a fait ses preuves sur le passé, sous des garde-fous qu'aucun agent ne peut
toucher.

**Papier uniquement.** Le code ne contient aucun courtier et refuse de tourner si le mode n'est pas
`papier`. Ce n'est pas un conseil financier.

## L'équipe

| Agent | Métier | Ce qu'il fait |
|---|---|---|
| **contrarien** | retour à la moyenne | Achète les replis excessifs à l'intérieur d'une tendance haussière ; le reste du temps, son argent est placé dans le S&P 500 au lieu de dormir. |
| **navigateur** | suivi de tendance | Reste investi dans ce qui est au-dessus de sa moyenne mobile 200 jours, sinon en cash (Faber, Paul Tudor Jones). |
| **vigie** | allocation tactique | Surveille 4 « canaris » (actions US, émergents, monde, obligations). Tout va bien : les 6 actifs les plus forts sur 12. Un canari faiblit : repli sur les 3 meilleurs actifs défensifs (Keller, *Bold Asset Allocation*, 2022). |
| **rempart** | portefeuille permanent | « All Weather » de Bridgewater (Ray Dalio) : 30 % actions, 55 % obligations, 15 % or et matières premières, rééquilibré chaque mois. |
| *risk manager* | code, pas agent | Garde-fous durs : plafonds, pas de levier, coupe-circuit, plafond de rotation. |
| *entraîneur* | code, pas agent | Évalue des réglages et les recommande, uniquement sur preuve (mode conseil : il n'applique rien seul). |
| *capitaine* | Claude | Réunion quotidienne : comprend, explique, propose des hypothèses à tester. |

Chaque agent démarre avec 10 000 $ fictifs. La référence est le même capital total placé dans le
SPY (S&P 500) le premier jour et conservé.

## Comment l'équipe est solidaire

- **Capital partagé.** Tous les 21 jours de cotation, le capital des agents actifs est remis à
  parts égales : ceux qui ont gagné en cèdent à ceux qui ont perdu. Chaque agent garde une valeur
  liquidative (comme une part de fonds) pour que sa performance propre reste mesurable.
- **Rôles complémentaires.** L'équipe est construite pour que ses membres ne perdent pas en même
  temps : la vigie n'est corrélée qu'à 0,29 avec le S&P 500 (2014-2026), le rempart à 0,52.
- **Plafond commun.** Aucun titre ne dépasse 30 % du capital de toute l'équipe, même si chaque
  agent reste dans ses propres limites. Si plusieurs agents veulent le même titre, leurs cibles
  sont réduites au prorata. Les indices larges (fonds d'actions et d'obligations très diversifiés)
  en sont exemptés : ce sont déjà des paniers de centaines de titres.
- **Mentorat.** À chaque évaluation, un agent teste aussi un réglage rapproché de celui du
  coéquipier le plus performant du moment.
- **Diversité protégée.** Un nouveau réglage est refusé s'il rend l'agent trop semblable à un
  coéquipier (corrélation supérieure à 0,9). Une équipe de clones n'est pas une équipe.
- **Rééducation.** Un agent qui perd 20 % depuis son pic passe en cash et en pause. Il ne reprend
  que si ses réglages ont un score positif sur les périodes récentes.
- **Savoir partagé.** Chaque adoption, coupe-circuit ou reprise est consigné dans
  `etat/savoir.json`, que la réunion quotidienne relit.

## Comment ils évoluent, et pourquoi c'est prudent

L'entraîneur a trois modes (`"evolution"` dans `config/equipe.json`) : `auto` (il adopte seul),
`conseil` (il recommande, un humain décide avec `python3 -m equipe adopter`) et `non`. L'équipe
est en **mode conseil** : la recherche de `recherche/RAPPORT.md` a montré qu'en 2008 l'adoption
automatique faisait reprendre un agent en pleine chute, avec une perte de 57 % malgré le
coupe-circuit, et qu'elle n'apportait presque rien en 2014-2026.

Tous les 5 jours de cotation, l'entraîneur évalue les agents dont le dernier changement (ou la
dernière recommandation) date d'au moins 21 jours. Il teste jusqu'à 8 candidats : les propositions de Claude d'abord, puis un conseil
du mentor, puis des mutations au hasard dans des bornes fixes. Chaque candidat est rejoué sur
**6 périodes passées de 6 mois** et comparé au réglage actuel. Il n'est recommandé que s'il :

- gagne sur les 6 périodes ;
- améliore le score moyen (Sharpe pénalisé par le drawdown) d'au moins 0,25 ;
- a un écart stable d'une période à l'autre (statistique t ≥ 3) ;
- ne rend pas l'agent trop semblable à un coéquipier.

Ces seuils sont stricts exprès. Une première version plus souple changeait les réglages d'un
agent 132 fois en 4 ans : elle courait après le bruit. On trade chaque jour, mais on n'adapte que
sur preuve.

**Le contrôle qui compte :** `backtest --comparer` rejoue la même équipe avec ses réglages figés.
Si l'équipe qui évolue ne bat pas l'équipe figée, l'évolution ne sert à rien. Cela peut arriver,
et le rapport le dit.

## Utilisation

```bash
python3 -m equipe telecharger                 # prix réels (Yahoo ; --source stooq en secours)
python3 -m equipe backtest --debut 2018-01-02 --comparer   # l'équipe rejouée sur le passé
python3 -m equipe init                        # crée l'équipe réelle, tout en cash
python3 -m equipe quotidien                   # rattrape les jours manquants, évolue, rapporte
python3 -m equipe statut                      # une ligne par agent
python3 -m equipe proposer --agent navigateur --param sma=150 --hypothese "..."
python3 -m equipe adopter --agent navigateur --param sma=150   # décision humaine, dans un terminal
python3 -m equipe garde-fous                  # affiche les limites et leur signature
python3 -m unittest discover -s tests         # 30 tests, hors ligne
python3 -m recherche conception               # le banc de recherche (voir recherche/RAPPORT.md)
```

`quotidien` est idempotent : le relancer ne refait rien, et rattraper 30 jours d'un coup donne
exactement le même résultat que 30 lancements d'un jour (c'est testé).

Le rapport du jour est dans `rapports/dernier.md` et le tableau de bord dans
`rapports/dernier.html`.

Pour tester sans réseau, `python3 -m equipe synthetique` écrit un marché inventé. Les rapports
l'affichent en gros : ces chiffres testent la mécanique, pas la rentabilité.

## La réunion quotidienne (Claude)

`.claude/skills/reunion-equipe/SKILL.md` décrit la réunion : mettre à jour les prix, faire tourner
la journée, lire, écrire `comptes-rendus/AAAA-MM-JJ.md`, proposer au plus deux hypothèses
réfutables, sauvegarder. Claude ne peut ni toucher aux garde-fous, ni modifier l'état à la main,
ni passer d'ordre réel. Une tâche planifiée peut la lancer chaque soir après la clôture.

## Garde-fous (`config/garde-fous.json`)

| Règle | Valeur |
|---|---|
| Poids max par titre (par agent) | 35 %, sauf indices larges : 98 % |
| Indices larges | SPY, IWM, EFA, EEM (actions) ; SHY, IEF, TLT, AGG, LQD, TIP (obligations) |
| Cash minimum | 2 % |
| Poids max par titre (équipe entière) | 30 % |
| Rotation max par jour | 60 % du portefeuille (au-delà, la cible décidée est atteinte en plusieurs jours, sans être recalculée) |
| Coupe-circuit | −20 % depuis le pic |
| Pause minimum | 10 jours |
| Délai entre deux changements de réglage | 21 jours |
| Glissement simulé | 5 points de base par ordre |

Le fichier est signé : son empreinte est enregistrée à la création de l'équipe et `quotidien`
s'arrête s'il change. Après l'avoir modifié vous-même, re-signez-le dans un terminal :
`python3 -m equipe garde-fous --approuver`.

## Limites honnêtes

- Les décisions se prennent sur les clôtures d'avant le jour J et s'exécutent à la clôture de J.
  C'est réaliste pour des ordres au marché de clôture, mais il n'y a ni impôts ni spread réel.
- Les données gratuites (Yahoo, Stooq) peuvent avoir des trous. Le cache ne réécrit jamais le
  passé : les nouveaux jours sont chaînés en rendements, pour ne pas perdre les dividendes.
- Un backtest, même avec évolution sans regard vers le futur, est un seul historique. Seuls
  plusieurs mois de papier en conditions réelles disent quelque chose.
- Quatre stratégies classiques sur des ETF n'ont aucun avantage secret. L'intérêt du prototype
  est la discipline, la mesure et l'apprentissage, pas une machine à argent.
