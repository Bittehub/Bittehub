"""Prix de clôture ajustés : téléchargement, cache CSV, alignement sur un calendrier commun."""
import csv
import datetime as dt
import json
import os
import time
import urllib.request

UA = "Mozilla/5.0 (equipe-trading)"


class Prices:
    """Clôtures alignées. closes[ticker][i] vaut None tant que le titre n'existe pas."""

    def __init__(self, dates, closes, source="inconnue"):
        self.dates = dates
        self.closes = closes
        self.source = source

    def __len__(self):
        return len(self.dates)

    def index_of(self, date):
        for i, d in enumerate(self.dates):
            if d >= date:
                return i
        return len(self.dates)

    def px(self, ticker, i):
        return self.closes[ticker][i]

    def hist(self, ticker, i, n):
        """Les n clôtures strictement avant le jour i (rien du jour i : pas de regard vers le futur)."""
        if i - n < 0:
            return None
        h = self.closes[ticker][i - n:i]
        if any(v is None for v in h):
            return None
        return h

    def truncated(self, end):
        """Copie limitée aux jours [0, end) : utile pour prouver l'absence de regard vers le futur."""
        return Prices(self.dates[:end], {t: c[:end] for t, c in self.closes.items()}, self.source)


def _http(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def fetch_yahoo(ticker, since):
    p1 = int(dt.datetime.fromisoformat(since).replace(tzinfo=dt.timezone.utc).timestamp())
    p2 = int(time.time())
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/%s?period1=%d&period2=%d"
           "&interval=1d&events=div%%2Csplit" % (ticker, p1, p2))
    res = json.loads(_http(url))["chart"]["result"][0]
    ts = res["timestamp"]
    adj = res["indicators"]["adjclose"][0]["adjclose"]
    out = {}
    for t, c in zip(ts, adj):
        if c is not None:
            out[dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()] = float(c)
    return out


def fetch_stooq(ticker, since):
    text = _http("https://stooq.com/q/d/l/?s=%s.us&i=d" % ticker.lower())
    out = {}
    for row in csv.DictReader(text.splitlines()):
        if row.get("Date", "") >= since and row.get("Close"):
            out[row["Date"]] = float(row["Close"])
    if not out:
        raise ValueError("stooq n'a rien renvoyé pour %s" % ticker)
    return out


PROVIDERS = {"yahoo": fetch_yahoo, "stooq": fetch_stooq}


def cache_path(cache_dir, ticker):
    return os.path.join(cache_dir, "%s.csv" % ticker)


def read_cache(cache_dir, ticker):
    path = cache_path(cache_dir, ticker)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return {r["date"]: float(r["close"]) for r in csv.DictReader(f)}


def write_cache(cache_dir, ticker, series):
    os.makedirs(cache_dir, exist_ok=True)
    with open(cache_path(cache_dir, ticker), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "close"])
        for d in sorted(series):
            w.writerow([d, "%.6f" % series[d]])


def read_meta(cache_dir):
    try:
        with open(os.path.join(cache_dir, "meta.json")) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def write_meta(cache_dir, meta):
    os.makedirs(cache_dir, exist_ok=True)
    with open(os.path.join(cache_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)


def merge(cache, nouveau):
    """Ajoute les nouveaux jours SANS réécrire le passé.

    Un cours ajusté est recalculé en arrière à chaque dividende : si on remplaçait l'historique, les
    portefeuilles (comptés en parts) perdraient le dividende. On chaîne donc les rendements du
    nouveau téléchargement sur le dernier niveau connu du cache, qui reste figé.
    """
    if not cache:
        return dict(nouveau)
    fin = max(cache)
    communs = [d for d in nouveau if d in cache]
    if not communs:
        raise ValueError("pas de jour commun entre le cache et le téléchargement")
    ancre = max(communs)
    out = dict(cache)
    for d in sorted(nouveau):
        if d > fin:
            out[d] = cache[ancre] * nouveau[d] / nouveau[ancre]
    return out


def fetch_all(tickers, cache_dir, provider="yahoo", since="2012-01-01", log=print):
    """Télécharge chaque titre ; un fournisseur qui échoue laisse le cache intact."""
    if read_meta(cache_dir).get("source") == "synthetique":
        raise SystemExit("Le cache contient des données synthétiques. Supprimez %s avant de télécharger "
                         "de vraies données." % cache_dir)
    fn = PROVIDERS[provider]
    failed = []
    for t in tickers:
        try:
            series = merge(read_cache(cache_dir, t), fn(t, since))
            write_cache(cache_dir, t, series)
            log("%-5s %d jours, dernier %s" % (t, len(series), max(series)))
        except Exception as e:  # réseau, format, titre inconnu
            failed.append(t)
            log("%-5s ÉCHEC : %s" % (t, e))
        time.sleep(0.3)
    write_meta(cache_dir, {"source": provider, "maj": dt.datetime.now(dt.timezone.utc).isoformat()})
    return failed


def load_prices(tickers, cache_dir, reference):
    """Calendrier = jours de cotation de la référence ; les trous isolés sont reportés (ffill)."""
    raw = {t: read_cache(cache_dir, t) for t in tickers}
    if not raw.get(reference):
        raise SystemExit("Aucun prix pour la référence %s dans %s. Lancez d'abord : python3 -m equipe "
                         "telecharger" % (reference, cache_dir))
    dates = sorted(raw[reference])
    closes = {}
    for t in tickers:
        col, last = [], None
        for d in dates:
            v = raw[t].get(d)
            if v is not None:
                last = v
            col.append(last)
        closes[t] = col
    return Prices(dates, closes, read_meta(cache_dir).get("source", "inconnue"))
