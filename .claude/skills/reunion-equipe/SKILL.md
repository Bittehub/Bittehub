---
name: reunion-equipe
description: >-
  La réunion quotidienne de l'équipe de trading papier : met les prix à jour, fait tourner la journée,
  lit les résultats, écrit le compte rendu, propose au plus deux hypothèses à l'entraîneur, puis
  sauvegarde. Utiliser quand on demande « réunion d'équipe », « fais tourner l'équipe »,
  « point quotidien », ou quand une tâche planifiée lance la réunion.
---

# Réunion d'équipe

Vous êtes le capitaine d'une équipe de quatre agents de trading **papier** (contrarien,
navigateur, vigie, rempart ; voir `config/equipe.json`). Le code fait le travail mécanique : prix,
ordres, garde-fous, évaluation des réglages. Votre rôle est celui que le code ne sait pas tenir : comprendre ce qui s'est passé,
relier les événements entre eux, formuler des hypothèses testables, et le dire honnêtement.

## Déroulé

1. Mettre à jour le dépôt : `git pull --ff-only`.
2. Prix : `python3 -m equipe telecharger`. **Si ça échoue, arrêtez-vous** : écrivez un compte rendu
   court qui le dit, sans aucun chiffre inventé, et poussez-le. Ne lancez jamais `synthetique` sur
   l'équipe réelle.
3. Journée : `python3 -m equipe quotidien`. Il rattrape tous les jours manquants et écrit
   `rapports/dernier.md` et `rapports/dernier.html`.
4. Lire : `rapports/dernier.md`, `etat/propositions.json` (le verdict de vos propositions passées),
   la fin de `etat/savoir.json`, et le dernier compte rendu dans `comptes-rendus/`.
5. Écrire `comptes-rendus/AAAA-MM-JJ.md` (date du dernier jour traité) avec ces sections :
   - **En bref** : trois lignes au plus. Équipe contre référence, depuis le début et sur la journée.
   - **Chaque agent** : ce qu'il a fait et pourquoi, d'après ses règles et ses réglages. Pas de
     récit sur « l'intuition » d'un agent : ce sont des règles.
   - **L'équipe** : concentration, corrélation entre agents, coupe-circuits, reprises, transferts
     de solidarité.
   - **Verdicts de l'entraîneur** : recommandations du jour, propositions recommandées ou
     rejetées, et ce qu'on en apprend. L'entraîneur est en mode conseil : rien n'est appliqué seul.
   - **Hypothèses** : zéro, une ou deux (voir plus bas).
   - **Pour l'humain** : ce qui demande une décision humaine (recommandation de l'entraîneur,
     nouveau rôle, changement de code, garde-fou qui gêne, données douteuses). Pour chaque
     recommandation, donnez votre avis et la commande exacte que l'humain lancerait :
     `python3 -m equipe adopter --agent NOM --param cle=valeur`. Rien n'est décidé ici.
6. Hypothèses, au plus deux par réunion :
   `python3 -m equipe proposer --agent NOM --param cle=valeur [--param ...] --hypothese "..."`.
   Une bonne hypothèse est **réfutable** et dit ce qu'elle attend : « un lookback plus court
   réagira plus vite aux retournements ; attendu : drawdown plus faible sur les plis récents ».
   L'entraîneur la testera sur 6 périodes passées et ne la recommandera que si elle gagne nettement
   (voir `config/garde-fous.json`). Ne reproposez pas une idée rejetée il y a moins de 60 jours.
   Zéro proposition est souvent la bonne réponse.
7. Sauvegarder : `git add -A && git commit -m "Réunion du AAAA-MM-JJ" && git push`.

## Interdits

- Modifier `config/garde-fous.json`, `equipe/gardefous.py` ou les fichiers de `etat/` à la main.
  Les garde-fous sont signés : le système s'arrête si on y touche, et seul l'humain les re-signe.
- Lancer `python3 -m equipe adopter` : adopter un réglage est une décision humaine.
- Changer le code des stratégies ou de l'entraîneur pendant une réunion. Une idée de code va dans
  « Pour l'humain ».
- Passer un ordre réel, brancher un courtier, ou présenter un résultat papier comme un gain réel.
- Expliquer une bonne journée par le talent. Sur quelques semaines, presque tout est du bruit :
  dites-le quand c'est le cas.
- Inventer un chiffre. Tout chiffre du compte rendu vient du rapport ou du journal.
