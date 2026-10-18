"""
nifty500_tickers.py
Loads the NIFTY 500 universe from universe.parquet (built by universe_builder.py).
Falls back gracefully if the file doesn't exist yet.

Exposes:
  NIFTY500_TICKERS  — list of .NS ticker strings  (for RS ranking)
  NAME_TO_TICKER    — dict: lowercase name → ticker  (for autocomplete)
  resolve_ticker()  — resolves a user search query to a yfinance symbol
"""

import os
import pandas as pd

_UNIVERSE_FILE = "universe.parquet"


def _load_universe() -> pd.DataFrame:
    """Load universe.parquet, triggering a build if it doesn't exist."""
    if os.path.exists(_UNIVERSE_FILE):
        try:
            return pd.read_parquet(_UNIVERSE_FILE)
        except Exception:
            pass
    # No file yet — trigger build (this happens on first run)
    try:
        from universe_builder import build_universe
        return build_universe()
    except Exception:
        # Absolute fallback: tiny seed list so the app doesn't crash
        return pd.DataFrame({
            "ticker_ns":    ["RELIANCE.NS","TCS.NS","HDFCBANK.NS","INFY.NS","ICICIBANK.NS"],
            "company_name": ["Reliance Industries","Tata Consultancy Services",
                             "HDFC Bank","Infosys","ICICI Bank"],
            "industry":     ["Energy","IT","Banking","IT","Banking"],
        })


# ── Load on import ────────────────────────────────────────────
_universe_df = _load_universe()

# Main exports
NIFTY500_TICKERS: list[str] = _universe_df["ticker_ns"].tolist()

# Build NAME_TO_TICKER from the universe  (lowercase name → ticker)
NAME_TO_TICKER: dict[str, str] = {}
for _, row in _universe_df.iterrows():
    name   = str(row["company_name"]).strip()
    ticker = str(row["ticker_ns"]).strip()
    key    = name.lower()
    NAME_TO_TICKER[key] = ticker
    # Also add ticker symbol itself (without .NS) as a lookup key
    sym = ticker.replace(".NS","").replace(".BO","").lower()
    NAME_TO_TICKER[sym] = ticker

# Manual aliases that aren't in company names but users commonly type
_ALIASES: dict[str, str] = {
    "tcs":              "TCS.NS",
    "hul":              "HINDUNILVR.NS",
    "hcl":              "HCLTECH.NS",
    "sbi":              "SBIN.NS",
    "state bank":       "SBIN.NS",
    "l&t":              "LT.NS",
    "m&m":              "M&M.NS",
    "dr reddy":         "DRREDDY.NS",
    "dr reddys":        "DRREDDY.NS",
    "bajaj fin":        "BAJFINANCE.NS",
    "bajaj auto":       "BAJAJ-AUTO.NS",
    "bpcl":             "BPCL.NS",
    "ongc":             "ONGC.NS",
    "ntpc":             "NTPC.NS",
    "gail":             "GAIL.NS",
    "ioc":              "IOC.NS",
    "indian oil":       "IOC.NS",
    "pfc":              "PFC.NS",
    "rec":              "RECLTD.NS",
    "naukri":           "NAUKRI.NS",
    "dmart":            "DMART.NS",
    "dominos":          "JUBLFOOD.NS",
    "domino's":         "JUBLFOOD.NS",
    "mcdonalds":        "WESTLIFE.NS",
    "mcdonald's":       "WESTLIFE.NS",
    "royal enfield":    "EICHERMOT.NS",
    "jockey":           "PAGEIND.NS",
    "fevicol":          "PIDILITIND.NS",
    "taj hotels":       "INDHOTEL.NS",
    "taj":              "INDHOTEL.NS",
    "oberoi hotels":    "EIHOTEL.NS",
    "angel broking":    "ANGELONE.NS",
    "angel one":        "ANGELONE.NS",
    "motilal":          "MOTILALOFS.NS",
    "igl":              "IGL.NS",
    "mgl":              "MGL.NS",
    "petronet":         "PETRONET.NS",
    "airtel":           "BHARTIARTL.NS",
    "bharti":           "BHARTIARTL.NS",
    "nestle":           "NESTLEIND.NS",
    "kotak":            "KOTAKBANK.NS",
    "hdfc bank":        "HDFCBANK.NS",
    "axis bank":        "AXISBANK.NS",
    "icici bank":       "ICICIBANK.NS",
    "indusind":         "INDUSINDBK.NS",
    "yes bank":         "YESBANK.NS",
    "bandhan":          "BANDHANBNK.NS",
    "federal bank":     "FEDERALBNK.NS",
    "au bank":          "AUBANK.NS",
    "au small finance": "AUBANK.NS",
    "idfc":             "IDFCFIRSTB.NS",
    "idfc first":       "IDFCFIRSTB.NS",
    "tata motors":      "TATAMOTORS.NS",
    "tata steel":       "TATASTEEL.NS",
    "tata power":       "TATAPOWER.NS",
    "tata elxsi":       "TATAELXSI.NS",
    "tata comm":        "TATACOMM.NS",
    "tata chem":        "TATACHEM.NS",
    "tata consumer":    "TATACONSUM.NS",
    "sun tv":           "SUNTV.NS",
    "sun pharma":       "SUNPHARMA.NS",
    "mrf":              "MRF.NS",
    "bata":             "BATAINDIA.NS",
    "relaxo":           "RELAXO.NS",
    "asian paints":     "ASIANPAINT.NS",
    "berger":           "BERGEPAINT.NS",
    "nerolac":          "KANSAINER.NS",
    "indigo":           "INDIGO.NS",
    "indigo paints":    "INDIGOPNTS.NS",
    "vedanta":          "VEDL.NS",
    "jsw steel":        "JSWSTEEL.NS",
    "jsw energy":       "JSWENERGY.NS",
    "adani enterprises":"ADANIENT.NS",
    "adani ports":      "ADANIPORTS.NS",
    "adani green":      "ADANIGREEN.NS",
    "adani power":      "ADANIPOWER.NS",
    "lumax":            "LUMAXTECH.NS",
    "avanti":           "AVANTIFEED.NS",
    "bluejet":          "BLUEJET.NS",
    "blue jet":         "BLUEJET.NS",
    "vimta":            "VIMTALABS.NS",
    "gallantt":         "GALLANTT.NS",
    "sarda":            "SARDAEN.NS",
    "shaily":           "SHAILY.NS",
    "dixon":            "DIXON.NS",
    "polycab":          "POLYCAB.NS",
    "kei":              "KEI.NS",
    "crompton":         "CROMPTON.NS",
    "blue star":        "BLUESTARCO.NS",
    "abb":              "ABB.NS",
    "siemens":          "SIEMENS.NS",
    "honeywell":        "HONAUT.NS",
    "hal":              "HAL.NS",
    "bel":              "BEL.NS",
    "bhel":             "BHEL.NS",
    "irctc":            "IRCTC.NS",
    "irfc":             "IRFC.NS",
    "rvnl":             "RVNL.NS",
    "zomato":           "ZOMATO.NS",
    "paytm":            "PAYTM.NS",
    "nykaa":            "NYKAA.NS",
    "policybazaar":     "POLICYBZR.NS",
    "policy bazaar":    "POLICYBZR.NS",
    "cdsl":             "CDSL.NS",
    "bse":              "BSE.NS",
    "mcx":              "MCX.NS",
    "crisil":           "CRISIL.NS",
    "hdfc amc":         "HDFCAMC.NS",
    "nippon amc":       "NIPPONLIFE.NS",
    "pi industries":    "PIIND.NS",
    "deepak nitrite":   "DEEPAKNITR.NS",
    "vinati organics":  "VINATIORGA.NS",
    "aarti":            "AARTIIND.NS",
    "clean science":    "CLEAN.NS",
    "thermax":          "THERMAX.NS",
    "cummins":          "CUMMINSIND.NS",
    "schaeffler":       "SCHAEFFLER.NS",
    "suzlon":           "SUZLON.NS",
    "inox wind":        "INOXWIND.NS",
    "ultratech":        "ULTRACEMCO.NS",
    "shree cement":     "SHREECEM.NS",
    "ambuja":           "AMBUJACEM.NS",
    "acc":              "ACC.NS",
    "dalmia":           "DALMIA.NS",
    "jubilant foodworks":"JUBLFOOD.NS",
    "muthoot":          "MUTHOOTFIN.NS",
    "cholamandalam":    "CHOLAFIN.NS",
    "chola":            "CHOLAFIN.NS",
    "piramal":          "PIRAMAL.NS",
    "shriram":          "SHRIRAMFIN.NS",
    "manappuram":       "MANAPPURAM.NS",
    "divi's":           "DIVISLAB.NS",
    "divis":            "DIVISLAB.NS",
    "lupin":            "LUPIN.NS",
    "cipla":            "CIPLA.NS",
    "biocon":           "BIOCON.NS",
    "aurobindo":        "AUROPHARMA.NS",
    "torrent pharma":   "TORNTPHARM.NS",
    "ipca":             "IPCALAB.NS",
    "alkem":            "ALKEM.NS",
    "glenmark":         "GLENMARK.NS",
    "zydus":            "ZYDUSLIFE.NS",
    "natco":            "NATCOPHARMA.NS",
    "granules":         "GRANULES.NS",
    "syngene":          "SYNGENE.NS",
    "ajanta pharma":    "AJANTPHARM.NS",
    "eris":             "ERIS.NS",
    "metropolis":       "METROPOLIS.NS",
    "dr lal":           "LALPATHLAB.NS",
    "lal pathlabs":     "LALPATHLAB.NS",
    "max health":       "MAXHEALTH.NS",
    "fortis":           "FORTIS.NS",
    "narayana":         "NARAYANA.NS",
    "apollo hosp":      "APOLLOHOSP.NS",
    "nhpc":             "NHPC.NS",
    "sjvn":             "SJVN.NS",
    "coal india":       "COALINDIA.NS",
    "hindalco":         "HINDALCO.NS",
    "nmdc":             "NMDC.NS",
    "sail":             "SAIL.NS",
    "jspl":             "JSPL.NS",
    "apl apollo":       "APLAPOLLO.NS",
    "ratnamani":        "RATNAMANI.NS",
    "bharatforge":      "BHARAT.NS",
    "bharat forge":     "BHARAT.NS",
    "sona blw":         "SONA.NS",
    "minda":            "MINDAIND.NS",
    "endurance":        "ENDURANCE.NS",
    "suprajit":         "SUPRAJIT.NS",
    "exide":            "EXIDEIND.NS",
    "amara raja":       "AMARAJABAT.NS",
    "ceat":             "CEATLTD.NS",
    "apollo tyres":     "APOLLOTYRE.NS",
    "balkrishna":       "BALKRISIND.NS",
    "marico":           "MARICO.NS",
    "dabur":            "DABUR.NS",
    "britannia":        "BRITANNIA.NS",
    "colgate":          "COLPAL.NS",
    "gillette":         "GILLETTE.NS",
    "raymond":          "RAYMOND.NS",
    "trident":          "TRIDENT.NS",
    "vardhman":         "VARDHMAN.NS",
    "trent":            "TRENT.NS",
    "westside":         "TRENT.NS",
    "manyavar":         "MANYAVAR.NS",
    "page ind":         "PAGEIND.NS",
    "havells":          "HAVELLS.NS",
    "voltas":           "VOLTAS.NS",
    "whirlpool":        "WHIRLPOOL.NS",
    "symphony":         "SYMPHONY.NS",
    "hawkins":          "HAWKINCOOK.NS",
    "ttk prestige":     "TTKPRESTIG.NS",
    "dmart":            "DMART.NS",
    "vmart":            "VMART.NS",
    "dlf":              "DLF.NS",
    "godrej prop":      "GODREJPROP.NS",
    "oberoi realty":    "OBEROIRLTY.NS",
    "prestige":         "PRESTIGE.NS",
    "sobha":            "SOBHA.NS",
    "brigade":          "BRIGADE.NS",
    "phoenix":          "PHOENIXLTD.NS",
    "blue dart":        "BLUEDART.NS",
    "delhivery":        "DELHIVERY.NS",
    "kalyan jewellers": "KALYNA.NS",
    "zee":              "ZEEL.NS",
    "pvr inox":         "PVRINOX.NS",
    "pvr":              "PVRINOX.NS",
    "sun tv":           "SUNTV.NS",
    "balrampur":        "BALRAMCHIN.NS",
    "coromandel":       "COROMANDEL.NS",
    "concor":           "CONCOR.NS",
    "ircon":            "IRCON.NS",
    "rites":            "RITES.NS",
    "varun beverages":  "VARUNBEV.NS",
    "radico":           "RADICO.NS",
    "persistent":       "PERSISTENT.NS",
    "mphasis":          "MPHASIS.NS",
    "coforge":          "COFORGE.NS",
    "kpit":             "KPITTECH.NS",
    "birlasoft":        "BIRLASOFT.NS",
    "eclerx":           "ECLERX.NS",
    "cyient":           "CYIENT.NS",
    "mastek":           "MASTEK.NS",
    "zensar":           "ZENSAR.NS",
    "tanla":            "TANLA.NS",
    "intellect":        "INTELLECT.NS",
    "route mobile":     "ROUTE.NS",
    "justdial":         "JUSTDIAL.NS",
    "info edge":        "NAUKRI.NS",
    "indus towers":     "INDUSTOWER.NS",
    "tata comm":        "TATACOMM.NS",
    "hfcl":             "HFCL.NS",
}

# Merge aliases into NAME_TO_TICKER (aliases take precedence for common short forms)
for k, v in _ALIASES.items():
    NAME_TO_TICKER[k.lower()] = v


# ── Resolve function ──────────────────────────────────────────
def resolve_ticker(query: str) -> str | None:
    """
    Resolve a user search query to a yfinance ticker symbol.
    Order of attempts:
      1. Already has .NS / .BO suffix → return as-is
      2. Exact match in NAME_TO_TICKER (case-insensitive)
      3. Partial match (query is contained in a known name, or vice versa)
      4. Assume raw NSE symbol → append .NS
    """
    q = query.strip()
    if not q:
        return None

    # 1. Already formatted
    if q.upper().endswith(".NS") or q.upper().endswith(".BO"):
        return q.upper()

    lower = q.lower()

    # 2. Exact match
    if lower in NAME_TO_TICKER:
        return NAME_TO_TICKER[lower]

    # 3. Partial match: score by length of match
    best_match = None
    best_score = 0
    for name, ticker in NAME_TO_TICKER.items():
        if lower in name or name in lower:
            score = len(set(lower.split()) & set(name.split()))
            if score > best_score:
                best_score = score
                best_match = ticker
    if best_match:
        return best_match

    # 4. Assume NSE raw ticker
    return q.upper() + ".NS"
