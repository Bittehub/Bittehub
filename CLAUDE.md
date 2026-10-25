# Équipe de trading papier

Prototype d'équipe d'agents de trading **en papier uniquement**. Python 3.8+, bibliothèque standard,
aucune dépendance.

- `equipe/` : le code. `strategies.py` (les métiers), `gardefous.py` (limites dures),
  `moteur.py` (une journée), `entraineur.py` (évolution des réglages sur preuve),
  `equipe.py` (orchestration), `rapport.py`, `data.py`.
- `config/equipe.json` : agents, capital, univers. `config/garde-fous.json` : limites signées.
- `etat/` : l'état vivant de l'équipe, écrit uniquement par le code.
- `comptes-rendus/` : un compte rendu par réunion, écrit par Claude.
- Tests : `python3 -m unittest discover -s tests`.

La réunion quotidienne suit `.claude/skills/reunion-equipe/SKILL.md`. Ses interdits s'appliquent à
toute session dans ce dépôt : ne jamais toucher aux garde-fous ni à `etat/` à la main, ne jamais
passer d'ordre réel, ne jamais inventer un chiffre.
