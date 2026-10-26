"""Un portefeuille papier : cash, parts fractionnaires, coûts simulés."""


class Portefeuille:
    def __init__(self, cash, positions=None):
        self.cash = float(cash)
        self.positions = dict(positions or {})

    def valeur(self, prices, i):
        return self.cash + sum(q * prices.px(t, i) for t, q in self.positions.items())

    def notionnels(self, prices, i):
        return {t: q * prices.px(t, i) for t, q in self.positions.items()}

    def executer(self, trades, prices, i, g):
        """trades = {ticker: montant à acheter (+) ou vendre (-)}. Ventes d'abord, puis achats
        limités au cash disponible. Remplissage à la clôture du jour i, glissement compris."""
        slip = g["glissement_bps"] / 1e4
        fills = []
        for t, v in sorted(trades.items(), key=lambda kv: kv[1]):
            if abs(v) < g["ordre_min"]:
                continue
            px = prices.px(t, i)
            if v < 0:
                q = min(-v / px, self.positions.get(t, 0.0))
                if q <= 0:
                    continue
                fill = px * (1 - slip)
                self.cash += q * fill - g["commission_par_ordre"]
                self.positions[t] = self.positions.get(t, 0.0) - q
                if self.positions[t] * px < 0.01:
                    self.positions.pop(t)
                fills.append({"ticker": t, "sens": "vente", "parts": round(q, 6), "prix": round(fill, 4)})
            else:
                fill = px * (1 + slip)
                budget = min(v, self.cash - g["commission_par_ordre"])
                if budget < g["ordre_min"]:
                    continue
                q = budget / fill
                self.cash -= q * fill + g["commission_par_ordre"]
                self.positions[t] = self.positions.get(t, 0.0) + q
                fills.append({"ticker": t, "sens": "achat", "parts": round(q, 6), "prix": round(fill, 4)})
        return fills

    def liquider(self, prices, i, g):
        """Tout vendre, y compris les miettes sous l'ordre minimum : après, il ne reste que du cash."""
        slip = g["glissement_bps"] / 1e4
        fills = []
        for t, q in sorted(self.positions.items()):
            fill = prices.px(t, i) * (1 - slip)
            self.cash += q * fill - (g["commission_par_ordre"] if q * fill >= g["ordre_min"] else 0.0)
            fills.append({"ticker": t, "sens": "vente", "parts": round(q, 6), "prix": round(fill, 4)})
        self.positions = {}
        return fills

    def redimensionner(self, f, prices, i, g):
        """Multiplie tout le portefeuille par f (transfert de capital entre agents), en payant le
        glissement sur la part des positions achetée ou vendue. Rend ce coût."""
        slip = g["glissement_bps"] / 1e4
        cout = 0.0
        for t, q in self.positions.items():
            cout += abs(q * (f - 1)) * prices.px(t, i) * slip
            self.positions[t] = q * f
        self.cash = self.cash * f - cout
        return cout

    def to_dict(self):
        return {"cash": round(self.cash, 6), "positions": {t: round(q, 8) for t, q in self.positions.items()}}

    @classmethod
    def from_dict(cls, d):
        return cls(d["cash"], d["positions"])
