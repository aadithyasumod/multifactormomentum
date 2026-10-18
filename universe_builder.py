"""
universe_builder.py
Fetches the complete NIFTY 500 constituent list from official sources
and saves it to universe.parquet for use by the rest of the app.

Sources tried in order:
  1. NSE India official CSV (most reliable, requires internet + no strict proxy)
  2. Wikipedia NIFTY 500 article (HTML table scrape)
  3. Expanded hardcoded fallback (~500 tickers)

Run manually:  python universe_builder.py
Auto-called:   on app startup if universe.parquet is missing or stale (>30 days)
"""

import os
import io
import time
import requests
import pandas as pd
from datetime import datetime

UNIVERSE_FILE = "universe.parquet"
UNIVERSE_TTL_DAYS = 30   # re-fetch after 30 days (index rebalances quarterly)

NSE_CSV_URL = "https://www.niftyindices.com/IndexConstituents/ind_nifty500list.csv"
WIKI_URL    = "https://en.wikipedia.org/wiki/NIFTY_500"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.niftyindices.com/",
}

# ──────────────────────────────────────────────────────────────
#  SOURCE 1: NSE Official CSV
# ──────────────────────────────────────────────────────────────
def _fetch_nse_csv() -> pd.DataFrame | None:
    try:
        r = requests.get(NSE_CSV_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        # NSE CSV columns: Company Name, Industry, Symbol, Series, ISIN Code
        df.columns = [c.strip() for c in df.columns]
        symbol_col = next((c for c in df.columns if "Symbol" in c), None)
        name_col   = next((c for c in df.columns if "Company" in c or "Name" in c), None)
        if not symbol_col:
            return None
        result = pd.DataFrame({
            "ticker_ns":    df[symbol_col].str.strip() + ".NS",
            "company_name": df[name_col].str.strip() if name_col else df[symbol_col].str.strip(),
            "industry":     df["Industry"].str.strip() if "Industry" in df.columns else "N/A",
        })
        result = result.dropna(subset=["ticker_ns"])
        print(f"  ✓ NSE CSV: {len(result)} constituents fetched")
        return result
    except Exception as e:
        print(f"  ✗ NSE CSV failed: {e}")
        return None


# ──────────────────────────────────────────────────────────────
#  SOURCE 2: Wikipedia
# ──────────────────────────────────────────────────────────────
def _fetch_wikipedia() -> pd.DataFrame | None:
    try:
        tables = pd.read_html(WIKI_URL)
        for df in tables:
            cols = [str(c).lower() for c in df.columns]
            sym_col  = next((i for i, c in enumerate(cols) if "symbol" in c or "ticker" in c), None)
            name_col = next((i for i, c in enumerate(cols) if "company" in c or "name" in c), None)
            if sym_col is not None and len(df) > 50:
                syms  = df.iloc[:, sym_col].astype(str).str.strip()
                names = df.iloc[:, name_col].astype(str).str.strip() if name_col is not None else syms
                result = pd.DataFrame({
                    "ticker_ns":    syms + ".NS",
                    "company_name": names,
                    "industry":     "N/A",
                })
                result = result[result["ticker_ns"].str.len() > 3]
                print(f"  ✓ Wikipedia: {len(result)} constituents fetched")
                return result
        return None
    except Exception as e:
        print(f"  ✗ Wikipedia failed: {e}")
        return None


# ──────────────────────────────────────────────────────────────
#  SOURCE 3: Comprehensive hardcoded fallback  (~500 tickers)
# ──────────────────────────────────────────────────────────────
_HARDCODED = [
    # ── NIFTY 50 ──────────────────────────────────────────────
    ("RELIANCE.NS",     "Reliance Industries",         "Energy"),
    ("TCS.NS",          "Tata Consultancy Services",   "IT"),
    ("HDFCBANK.NS",     "HDFC Bank",                   "Banking"),
    ("INFY.NS",         "Infosys",                     "IT"),
    ("BHARTIARTL.NS",   "Bharti Airtel",               "Telecom"),
    ("ICICIBANK.NS",    "ICICI Bank",                  "Banking"),
    ("SBIN.NS",         "State Bank of India",         "Banking"),
    ("HINDUNILVR.NS",   "Hindustan Unilever",          "FMCG"),
    ("ITC.NS",          "ITC",                         "FMCG"),
    ("KOTAKBANK.NS",    "Kotak Mahindra Bank",         "Banking"),
    ("LT.NS",           "Larsen & Toubro",             "Capital Goods"),
    ("AXISBANK.NS",     "Axis Bank",                   "Banking"),
    ("ASIANPAINT.NS",   "Asian Paints",                "Consumer"),
    ("MARUTI.NS",       "Maruti Suzuki",               "Auto"),
    ("BAJFINANCE.NS",   "Bajaj Finance",               "NBFC"),
    ("NTPC.NS",         "NTPC",                        "Power"),
    ("ONGC.NS",         "ONGC",                        "Oil & Gas"),
    ("SUNPHARMA.NS",    "Sun Pharmaceutical",          "Pharma"),
    ("TITAN.NS",        "Titan Company",               "Consumer"),
    ("POWERGRID.NS",    "Power Grid Corporation",      "Power"),
    ("ULTRACEMCO.NS",   "UltraTech Cement",            "Cement"),
    ("WIPRO.NS",        "Wipro",                       "IT"),
    ("HCLTECH.NS",      "HCL Technologies",            "IT"),
    ("NESTLEIND.NS",    "Nestle India",                "FMCG"),
    ("ADANIENT.NS",     "Adani Enterprises",           "Conglomerate"),
    ("ADANIPORTS.NS",   "Adani Ports",                 "Infrastructure"),
    ("BAJAJFINSV.NS",   "Bajaj Finserv",               "Finance"),
    ("TECHM.NS",        "Tech Mahindra",               "IT"),
    ("GRASIM.NS",       "Grasim Industries",           "Cement"),
    ("COALINDIA.NS",    "Coal India",                  "Mining"),
    ("INDUSINDBK.NS",   "IndusInd Bank",               "Banking"),
    ("TATAMOTORS.NS",   "Tata Motors",                 "Auto"),
    ("TATASTEEL.NS",    "Tata Steel",                  "Metals"),
    ("M&M.NS",          "Mahindra & Mahindra",         "Auto"),
    ("JSWSTEEL.NS",     "JSW Steel",                   "Metals"),
    ("TATACONSUM.NS",   "Tata Consumer Products",      "FMCG"),
    ("BPCL.NS",         "BPCL",                        "Oil & Gas"),
    ("CIPLA.NS",        "Cipla",                       "Pharma"),
    ("APOLLOHOSP.NS",   "Apollo Hospitals",            "Healthcare"),
    ("EICHERMOT.NS",    "Eicher Motors",               "Auto"),
    ("LTIM.NS",         "LTIMindtree",                 "IT"),
    ("HINDALCO.NS",     "Hindalco Industries",         "Metals"),
    ("DRREDDY.NS",      "Dr. Reddy's Laboratories",    "Pharma"),
    ("BRITANNIA.NS",    "Britannia Industries",        "FMCG"),
    ("SBILIFE.NS",      "SBI Life Insurance",          "Insurance"),
    ("HEROMOTOCO.NS",   "Hero MotoCorp",               "Auto"),
    ("HDFCLIFE.NS",     "HDFC Life Insurance",         "Insurance"),
    ("DIVISLAB.NS",     "Divi's Laboratories",         "Pharma"),
    ("BAJAJ-AUTO.NS",   "Bajaj Auto",                  "Auto"),
    ("UPL.NS",          "UPL",                         "Agro Chemicals"),
    # ── NIFTY NEXT 50 ─────────────────────────────────────────
    ("VEDL.NS",         "Vedanta",                     "Metals"),
    ("IOC.NS",          "Indian Oil Corporation",      "Oil & Gas"),
    ("SIEMENS.NS",      "Siemens India",               "Capital Goods"),
    ("HAVELLS.NS",      "Havells India",               "Electricals"),
    ("BOSCHLTD.NS",     "Bosch",                       "Auto Ancillaries"),
    ("PIDILITIND.NS",   "Pidilite Industries",         "Chemicals"),
    ("MARICO.NS",       "Marico",                      "FMCG"),
    ("DABUR.NS",        "Dabur India",                 "FMCG"),
    ("BERGEPAINT.NS",   "Berger Paints",               "Consumer"),
    ("MUTHOOTFIN.NS",   "Muthoot Finance",             "NBFC"),
    ("TORNTPHARM.NS",   "Torrent Pharmaceuticals",     "Pharma"),
    ("AMBUJACEM.NS",    "Ambuja Cements",              "Cement"),
    ("GODREJCP.NS",     "Godrej Consumer Products",    "FMCG"),
    ("LUPIN.NS",        "Lupin",                       "Pharma"),
    ("BIOCON.NS",       "Biocon",                      "Pharma"),
    ("MOTHERSON.NS",    "Samvardhana Motherson",       "Auto Ancillaries"),
    ("DLF.NS",          "DLF",                         "Real Estate"),
    ("SRF.NS",          "SRF",                         "Chemicals"),
    ("INDIGO.NS",       "InterGlobe Aviation (IndiGo)","Airlines"),
    ("TATAPOWER.NS",    "Tata Power",                  "Power"),
    ("SAIL.NS",         "Steel Authority of India",    "Metals"),
    ("PNB.NS",          "Punjab National Bank",        "Banking"),
    ("BANKBARODA.NS",   "Bank of Baroda",              "Banking"),
    ("CANBK.NS",        "Canara Bank",                 "Banking"),
    ("CHOLAFIN.NS",     "Cholamandalam Investment",    "NBFC"),
    ("PAGEIND.NS",      "Page Industries",             "Consumer"),
    ("MCDOWELL-N.NS",   "United Spirits",              "Consumer"),
    ("GODREJPROP.NS",   "Godrej Properties",           "Real Estate"),
    ("LICHSGFIN.NS",    "LIC Housing Finance",         "NBFC"),
    ("RECLTD.NS",       "REC",                         "Finance"),
    ("PFC.NS",          "Power Finance Corporation",   "Finance"),
    ("NAUKRI.NS",       "Info Edge (Naukri.com)",      "Internet"),
    ("OFSS.NS",         "Oracle Financial Services",   "IT"),
    ("AUROPHARMA.NS",   "Aurobindo Pharma",            "Pharma"),
    ("COLPAL.NS",       "Colgate-Palmolive India",     "FMCG"),
    ("SHREECEM.NS",     "Shree Cement",                "Cement"),
    ("ACC.NS",          "ACC",                         "Cement"),
    ("TRENT.NS",        "Trent",                       "Retail"),
    ("VOLTAS.NS",       "Voltas",                      "Consumer"),
    ("TVSMOTOR.NS",     "TVS Motor Company",           "Auto"),
    ("DMART.NS",        "Avenue Supermarts (D-Mart)",  "Retail"),
    ("SBICARD.NS",      "SBI Cards",                   "Finance"),
    ("BANDHANBNK.NS",   "Bandhan Bank",                "Banking"),
    ("FEDERALBNK.NS",   "Federal Bank",                "Banking"),
    ("MPHASIS.NS",      "Mphasis",                     "IT"),
    ("COFORGE.NS",      "Coforge",                     "IT"),
    ("LTTS.NS",         "L&T Technology Services",     "IT"),
    ("PERSISTENT.NS",   "Persistent Systems",          "IT"),
    ("INDUSTOWER.NS",   "Indus Towers",                "Telecom"),
    # ── NIFTY MIDCAP 150 ──────────────────────────────────────
    ("ZOMATO.NS",       "Zomato",                      "Internet"),
    ("PAYTM.NS",        "One97 Communications (Paytm)","Fintech"),
    ("NYKAA.NS",        "FSN E-Commerce (Nykaa)",      "Retail"),
    ("POLICYBZR.NS",    "PB Fintech (PolicyBazaar)",   "Fintech"),
    ("IRCTC.NS",        "IRCTC",                       "Travel"),
    ("CONCOR.NS",       "Container Corporation",       "Logistics"),
    ("HAL.NS",          "Hindustan Aeronautics",       "Defence"),
    ("BEL.NS",          "Bharat Electronics",          "Defence"),
    ("BHEL.NS",         "BHEL",                        "Capital Goods"),
    ("NHPC.NS",         "NHPC",                        "Power"),
    ("SJVN.NS",         "SJVN",                        "Power"),
    ("RVNL.NS",         "Rail Vikas Nigam",            "Infrastructure"),
    ("IRFC.NS",         "IRFC",                        "Finance"),
    ("NBCC.NS",         "NBCC India",                  "Infrastructure"),
    ("NLC.NS",          "NLC India",                   "Power"),
    ("BSE.NS",          "BSE",                         "Exchange"),
    ("MCX.NS",          "Multi Commodity Exchange",    "Exchange"),
    ("CDSL.NS",         "CDSL",                        "Finance"),
    ("ANGELONE.NS",     "Angel One",                   "Broking"),
    ("MOTILALOFS.NS",   "Motilal Oswal Financial",     "Broking"),
    ("HDFCAMC.NS",      "HDFC AMC",                    "AMC"),
    ("NIPPONLIFE.NS",   "Nippon India AMC",            "AMC"),
    ("ICICIGI.NS",      "ICICI Lombard GIC",           "Insurance"),
    ("NIACL.NS",        "New India Assurance",         "Insurance"),
    ("STAR.NS",         "Star Health Insurance",       "Insurance"),
    ("KFINTECH.NS",     "KFin Technologies",           "Fintech"),
    ("CRISIL.NS",       "CRISIL",                      "Finance"),
    ("IIFL.NS",         "IIFL Finance",                "NBFC"),
    ("MFSL.NS",         "Max Financial Services",      "Insurance"),
    ("AUBANK.NS",       "AU Small Finance Bank",       "Banking"),
    ("SURYODAY.NS",     "Suryoday Small Finance Bank", "Banking"),
    ("UJJIVANSFB.NS",   "Ujjivan Small Finance Bank",  "Banking"),
    ("EQUITASBNK.NS",   "Equitas Small Finance Bank",  "Banking"),
    ("RBLBANK.NS",      "RBL Bank",                    "Banking"),
    ("DCBBANK.NS",      "DCB Bank",                    "Banking"),
    ("CITYUNIONBK.NS",  "City Union Bank",             "Banking"),
    ("KARURVYSYA.NS",   "Karur Vysya Bank",            "Banking"),
    ("INDIANB.NS",      "Indian Bank",                 "Banking"),
    ("IDFCFIRSTB.NS",   "IDFC First Bank",             "Banking"),
    ("YESBANK.NS",      "Yes Bank",                    "Banking"),
    ("IDBI.NS",         "IDBI Bank",                   "Banking"),
    ("J&KBANK.NS",      "Jammu & Kashmir Bank",        "Banking"),
    ("SOUTHBANK.NS",    "South Indian Bank",           "Banking"),
    ("KARNATAKA.NS",    "Karnataka Bank",              "Banking"),
    ("LALPATHLAB.NS",   "Dr. Lal PathLabs",            "Healthcare"),
    ("METROPOLIS.NS",   "Metropolis Healthcare",       "Healthcare"),
    ("MAXHEALTH.NS",    "Max Healthcare",              "Healthcare"),
    ("FORTIS.NS",       "Fortis Healthcare",           "Healthcare"),
    ("NARAYANA.NS",     "Narayana Hrudayalaya",        "Healthcare"),
    ("RAINBOW.NS",      "Rainbow Children's Medicare", "Healthcare"),
    ("IPCALAB.NS",      "IPCA Laboratories",           "Pharma"),
    ("ALKEM.NS",        "Alkem Laboratories",          "Pharma"),
    ("GLENMARK.NS",     "Glenmark Pharmaceuticals",    "Pharma"),
    ("TORNTPOWER.NS",   "Torrent Power",               "Power"),
    ("CESC.NS",         "CESC",                        "Power"),
    ("TATAELXSI.NS",    "Tata Elxsi",                  "IT"),
    ("DIXON.NS",        "Dixon Technologies",          "Electronics"),
    ("AMBER.NS",        "Amber Enterprises",           "Electronics"),
    ("KAYNES.NS",       "Kaynes Technology",           "Electronics"),
    ("SYRMA.NS",        "Syrma SGS Technology",        "Electronics"),
    ("ECLERX.NS",       "eClerx Services",             "IT"),
    ("BIRLASOFT.NS",    "Birlasoft",                   "IT"),
    ("KPITTECH.NS",     "KPIT Technologies",           "IT"),
    ("CYIENT.NS",       "Cyient",                      "IT"),
    ("MASTEK.NS",       "Mastek",                      "IT"),
    ("ZENSAR.NS",       "Zensar Technologies",         "IT"),
    ("TANLA.NS",        "Tanla Platforms",             "IT"),
    ("INTELLECT.NS",    "Intellect Design Arena",      "IT"),
    ("ROUTE.NS",        "Route Mobile",                "IT"),
    ("INFIBEAM.NS",     "Infibeam Avenues",            "Fintech"),
    ("INDHOTEL.NS",     "Indian Hotels (Taj)",         "Hotels"),
    ("EIHOTEL.NS",      "EIH (Oberoi Hotels)",         "Hotels"),
    ("CHALET.NS",       "Chalet Hotels",               "Hotels"),
    ("LEMON.NS",        "Lemon Tree Hotels",           "Hotels"),
    ("MAHINDCIE.NS",    "Mahindra CIE Automotive",     "Auto Ancillaries"),
    ("SUNDARMFIN.NS",   "Sundaram Finance",            "NBFC"),
    ("SHRIRAMFIN.NS",   "Shriram Finance",             "NBFC"),
    ("MANAPPURAM.NS",   "Manappuram Finance",          "NBFC"),
    ("L&TFH.NS",        "L&T Finance Holdings",        "NBFC"),
    ("POONAWALLA.NS",   "Poonawalla Fincorp",          "NBFC"),
    ("CREDITACC.NS",    "CreditAccess Grameen",        "MFI"),
    ("SPANDANA.NS",     "Spandana Sphoorty",           "MFI"),
    ("APLAPOLLO.NS",    "APL Apollo Tubes",            "Metals"),
    ("JSPL.NS",         "Jindal Steel & Power",        "Metals"),
    ("NMDC.NS",         "NMDC",                        "Mining"),
    ("RATNAMANI.NS",    "Ratnamani Metals",            "Metals"),
    ("WELSPUNLIV.NS",   "Welspun Living",              "Textiles"),
    ("RAYMOND.NS",      "Raymond",                     "Textiles"),
    ("ARVIND.NS",       "Arvind",                      "Textiles"),
    ("TRIDENT.NS",      "Trident",                     "Textiles"),
    ("VARDHMAN.NS",     "Vardhman Textiles",           "Textiles"),
    ("KPR.NS",          "KPR Mill",                    "Textiles"),
    ("POLYCAB.NS",      "Polycab India",               "Electricals"),
    ("KEI.NS",          "KEI Industries",              "Electricals"),
    ("FINCABLES.NS",    "Finolex Cables",              "Electricals"),
    ("VGUARD.NS",       "V-Guard Industries",          "Electricals"),
    ("ORIENT.NS",       "Orient Electric",             "Electricals"),
    ("BAJAJELEC.NS",    "Bajaj Electricals",           "Electricals"),
    ("CROMPTON.NS",     "Crompton Greaves Consumer",   "Electricals"),
    ("BLUESTARCO.NS",   "Blue Star",                   "Electricals"),
    ("HITACHIENERGY.NS","Hitachi Energy India",        "Capital Goods"),
    ("ABB.NS",          "ABB India",                   "Capital Goods"),
    ("APARINDS.NS",     "APAR Industries",             "Electricals"),
    ("SCHAEFFLER.NS",   "Schaeffler India",            "Auto Ancillaries"),
    ("SKFINDIA.NS",     "SKF India",                   "Auto Ancillaries"),
    ("CUMMINSIND.NS",   "Cummins India",               "Capital Goods"),
    ("GRINDWELL.NS",    "Grindwell Norton",            "Capital Goods"),
    ("ELGI.NS",         "Elgi Equipments",             "Capital Goods"),
    ("THERMAX.NS",      "Thermax",                     "Capital Goods"),
    ("PRAJ.NS",         "Praj Industries",             "Capital Goods"),
    ("CENTURYPLY.NS",   "Century Plyboards",           "Building Materials"),
    ("GREENPANEL.NS",   "Greenpanel Industries",       "Building Materials"),
    ("SUPREMEIND.NS",   "Supreme Industries",          "Plastics"),
    ("ASTRAL.NS",       "Astral Poly Technik",         "Plastics"),
    ("FINOLEX.NS",      "Finolex Industries",          "Plastics"),
    ("JKCEMENT.NS",     "JK Cement",                   "Cement"),
    ("RAMCOCEM.NS",     "The Ramco Cements",           "Cement"),
    ("HEIDELBERG.NS",   "Heidelberg Cement India",     "Cement"),
    ("DALMIA.NS",       "Dalmia Bharat",               "Cement"),
    ("BIRLACORPN.NS",   "Birla Corporation",           "Cement"),
    ("NCLIND.NS",       "NCL Industries",              "Cement"),
    ("PIIND.NS",        "PI Industries",               "Agro Chemicals"),
    ("SUMICHEM.NS",     "Sumitomo Chemical India",     "Agro Chemicals"),
    ("AARTIIND.NS",     "Aarti Industries",            "Chemicals"),
    ("ALKYLAMINE.NS",   "Alkyl Amines Chemicals",      "Chemicals"),
    ("VINATIORGA.NS",   "Vinati Organics",             "Chemicals"),
    ("GNFC.NS",         "GNFC",                        "Chemicals"),
    ("TATACHEM.NS",     "Tata Chemicals",              "Chemicals"),
    ("DEEPAKNITR.NS",   "Deepak Nitrite",              "Chemicals"),
    ("NOCIL.NS",        "NOCIL",                       "Chemicals"),
    ("FINEORG.NS",      "Fine Organic Industries",     "Chemicals"),
    ("IOLCP.NS",        "IOL Chemicals",               "Chemicals"),
    ("CLEAN.NS",        "Clean Science & Technology",  "Chemicals"),
    ("NEOGEN.NS",       "Neogen Chemicals",            "Chemicals"),
    ("GAIL.NS",         "GAIL India",                  "Oil & Gas"),
    ("IGL.NS",          "Indraprastha Gas",            "Oil & Gas"),
    ("MGL.NS",          "Mahanagar Gas",               "Oil & Gas"),
    ("PETRONET.NS",     "Petronet LNG",                "Oil & Gas"),
    ("AEGISCHEM.NS",    "Aegis Logistics",             "Oil & Gas"),
    ("GSPL.NS",         "Gujarat State Petronet",      "Oil & Gas"),
    ("GUJGASLTD.NS",    "Gujarat Gas",                 "Oil & Gas"),
    ("LINDEINDIA.NS",   "Linde India",                 "Chemicals"),
    ("INOXAIR.NS",      "INOX Air Products",           "Chemicals"),
    ("SUZLON.NS",       "Suzlon Energy",               "Renewable Energy"),
    ("INOXWIND.NS",     "Inox Wind",                   "Renewable Energy"),
    ("WEBSOL.NS",       "Websol Energy System",        "Renewable Energy"),
    ("BOROSIL.NS",      "Borosil Renewables",          "Renewable Energy"),
    ("KEC.NS",          "KEC International",           "Infrastructure"),
    ("KALPATPOWR.NS",   "Kalpataru Power",             "Infrastructure"),
    ("PNC.NS",          "PNC Infratech",               "Infrastructure"),
    ("KNRCON.NS",       "KNR Constructions",           "Infrastructure"),
    ("HGINFRA.NS",      "H.G. Infra Engineering",      "Infrastructure"),
    ("OBEROIRLTY.NS",   "Oberoi Realty",               "Real Estate"),
    ("PHOENIXLTD.NS",   "Phoenix Mills",               "Real Estate"),
    ("PRESTIGE.NS",     "Prestige Estates",            "Real Estate"),
    ("SOBHA.NS",        "Sobha",                       "Real Estate"),
    ("BRIGADE.NS",      "Brigade Enterprises",         "Real Estate"),
    ("MAHLIFE.NS",      "Mahindra Lifespace",          "Real Estate"),
    ("SUNTECK.NS",      "Sunteck Realty",              "Real Estate"),
    ("ACRYSIL.NS",      "Acrysil",                     "Consumer"),
    ("JUBLFOOD.NS",     "Jubilant Foodworks (Domino's)","QSR"),
    ("WESTLIFE.NS",     "Westlife Foodworld (McDonald's)","QSR"),
    ("DEVYANI.NS",      "Devyani International",       "QSR"),
    ("SAPPHIRE.NS",     "Sapphire Foods",              "QSR"),
    ("BARBEQUE.NS",     "Barbeque-Nation",             "QSR"),
    ("RELAXO.NS",       "Relaxo Footwears",            "Consumer"),
    ("BATAINDIA.NS",    "Bata India",                  "Consumer"),
    ("METROBRAND.NS",   "Metro Brands",                "Retail"),
    ("VMART.NS",        "V-Mart Retail",               "Retail"),
    ("SHOPERSTOP.NS",   "Shoppers Stop",               "Retail"),
    ("CENTRALBKL.NS",   "Central Depository",          "Retail"),
    ("RAYMOND.NS",      "Raymond",                     "Textiles"),
    ("MANYAVAR.NS",     "Vedant Fashions (Manyavar)",  "Retail"),
    ("SYMPHONY.NS",     "Symphony",                    "Consumer"),
    ("HAWKINCOOK.NS",   "Hawkins Cookers",             "Consumer"),
    ("TTKPRESTIG.NS",   "TTK Prestige",                "Consumer"),
    ("WONDERLA.NS",     "Wonderla Holidays",           "Tourism"),
    ("IRCON.NS",        "IRCON International",         "Infrastructure"),
    ("RITES.NS",        "RITES",                       "Infrastructure"),
    ("WABAG.NS",        "VA Tech Wabag",               "Infrastructure"),
    ("BENGALENE.NS",    "Bengal Energy",               "Energy"),
    ("ZYDUSLIFE.NS",    "Zydus Lifesciences",          "Pharma"),
    ("NATCOPHARMA.NS",  "Natco Pharma",                "Pharma"),
    ("SUVEN.NS",        "Suven Pharmaceuticals",       "Pharma"),
    ("GRANULES.NS",     "Granules India",              "Pharma"),
    ("APLLTD.NS",       "APL Apollo Tubes",            "Pharma"),
    ("SYNGENE.NS",      "Syngene International",       "Pharma"),
    ("JUBILANT.NS",     "Jubilant Pharmova",           "Pharma"),
    ("SOLARA.NS",       "Solara Active Pharma",        "Pharma"),
    ("DIVI.NS",         "Divi's Laboratories",         "Pharma"),
    ("GILLETTE.NS",     "Gillette India",              "FMCG"),
    ("3MINDIA.NS",      "3M India",                    "Diversified"),
    ("HONAUT.NS",       "Honeywell Automation",        "Capital Goods"),
    ("WHIRLPOOL.NS",    "Whirlpool India",             "Consumer"),
    ("BLUEDART.NS",     "Blue Dart Express",           "Logistics"),
    ("DELHIVERY.NS",    "Delhivery",                   "Logistics"),
    ("GATI.NS",         "Gati",                        "Logistics"),
    ("VRL.NS",          "VRL Logistics",               "Logistics"),
    ("ALLCARGO.NS",     "Allcargo Logistics",          "Logistics"),
    ("TCI.NS",          "Transport Corporation",       "Logistics"),
    ("JUSTDIAL.NS",     "Just Dial",                   "Internet"),
    ("INDIGOPNTS.NS",   "Indigo Paints",               "Consumer"),
    ("KANSAINER.NS",    "Kansai Nerolac Paints",       "Consumer"),
    ("AKZOINDIA.NS",    "Akzo Nobel India",            "Consumer"),
    ("BASF.NS",         "BASF India",                  "Chemicals"),
    ("TATACOFFEE.NS",   "Tata Coffee",                 "FMCG"),
    ("CCL.NS",          "CCL Products India",          "FMCG"),
    ("VARUNBEV.NS",     "Varun Beverages",             "FMCG"),
    ("RADICO.NS",       "Radico Khaitan",              "Consumer"),
    ("GLOBUSSP.NS",     "Globus Spirits",              "Consumer"),
    ("GMMPFAUDLR.NS",   "GMM Pfaudler",                "Capital Goods"),
    ("JBCHEPHARM.NS",   "JB Chemicals & Pharmaceuticals","Pharma"),
    ("NEULANDLAB.NS",   "Neuland Laboratories",        "Pharma"),
    ("WINDLAS.NS",      "Windlas Biotech",             "Pharma"),
    ("GLAND.NS",        "Gland Pharma",                "Pharma"),
    ("ERIS.NS",         "Eris Lifesciences",           "Pharma"),
    ("AJANTPHARM.NS",   "Ajanta Pharma",               "Pharma"),
    ("SEQUENT.NS",      "SeQuent Scientific",          "Pharma"),
    ("STRIDES.NS",      "Strides Pharma",              "Pharma"),
    ("CAPLIPOINT.NS",   "Caplin Point Laboratories",   "Pharma"),
    ("LAXMIPATHI.NS",   "Laxmi Organic Industries",    "Chemicals"),
    ("TATVA.NS",        "Tatva Chintan Pharma",        "Chemicals"),
    ("NUVAMA.NS",       "Nuvama Wealth Management",    "Broking"),
    ("360ONE.NS",       "360 ONE WAM",                 "Broking"),
    ("ANAND.NS",        "Anand Rathi Wealth",          "Broking"),
    ("IIFLWAM.NS",      "IIFL Wealth Management",      "Broking"),
    ("GEOJITFSL.NS",    "Geojit Financial Services",   "Broking"),
    ("LUMAXTECH.NS",    "Lumax Technologies",          "Auto Ancillaries"),
    ("LUMAXIND.NS",     "Lumax Industries",            "Auto Ancillaries"),
    ("AVANTIFEED.NS",   "Avanti Feeds",                "Food Processing"),
    ("VIMTALABS.NS",    "Vimta Labs",                  "Healthcare"),
    ("GALLANTT.NS",     "Gallantt Metal",              "Metals"),
    ("SARDAEN.NS",      "Sarda Energy & Minerals",     "Metals"),
    ("SHAILY.NS",       "Shaily Engineering Plastics",  "Plastics"),
    ("BLUEJET.NS",      "Blue Jet Healthcare",         "Pharma"),
    ("INNOVACAP.NS",    "Innova Captab",               "Pharma"),
    ("GRWRHITECH.NS",   "GKW",                         "Capital Goods"),
    ("BANCOINDIA.NS",   "Banco Products India",        "Auto Ancillaries"),
    ("SUPPETRO.NS",     "Supreme Petrochem",           "Chemicals"),
    ("SUPRAJIT.NS",     "Suprajit Engineering",        "Auto Ancillaries"),
    ("RACL.NS",         "RACL Geartech",               "Auto Ancillaries"),
    ("ENDURANCE.NS",    "Endurance Technologies",      "Auto Ancillaries"),
    ("STARTRACK.NS",    "Star Trackers",               "Auto Ancillaries"),
    ("CRAFTSMAN.NS",    "Craftsman Automation",        "Auto Ancillaries"),
    ("ROLEX.NS",        "Rolex Rings",                 "Auto Ancillaries"),
    ("PRICOL.NS",       "Pricol",                      "Auto Ancillaries"),
    ("SUBROS.NS",       "Subros",                      "Auto Ancillaries"),
    ("MINDA.NS",        "Minda Corporation",           "Auto Ancillaries"),
    ("MINDAIND.NS",     "Minda Industries",            "Auto Ancillaries"),
    ("SONA.NS",         "Sona BLW Precision",          "Auto Ancillaries"),
    ("SAMVARDHANA.NS",  "Samvardhana Motherson",       "Auto Ancillaries"),
    ("GABRIEL.NS",      "Gabriel India",               "Auto Ancillaries"),
    ("BHARAT.NS",       "Bharat Forge",                "Auto Ancillaries"),
    ("SUNDRM.NS",       "Sundram Fasteners",           "Auto Ancillaries"),
    ("EXIDEIND.NS",     "Exide Industries",            "Auto Ancillaries"),
    ("AMARAJABAT.NS",   "Amara Raja Energy",           "Auto Ancillaries"),
    ("CEATLTD.NS",      "CEAT",                        "Tyres"),
    ("MRF.NS",          "MRF",                         "Tyres"),
    ("APOLLOTYRE.NS",   "Apollo Tyres",                "Tyres"),
    ("BALKRISIND.NS",   "Balkrishna Industries",       "Tyres"),
    ("JK.NS",           "JK Tyre",                     "Tyres"),
    ("TATACOMM.NS",     "Tata Communications",         "Telecom"),
    ("HFCL.NS",         "HFCL",                        "Telecom"),
    ("TEJAS.NS",        "Tejas Networks",              "Telecom"),
    ("GTLINFRA.NS",     "GTL Infrastructure",          "Telecom"),
    ("HATHWAY.NS",      "Hathway Cable",               "Media"),
    ("SUNTV.NS",        "Sun TV Network",              "Media"),
    ("ZEEL.NS",         "Zee Entertainment",           "Media"),
    ("PVRINOX.NS",      "PVR Inox",                    "Media"),
    ("SAREGAMA.NS",     "Saregama India",              "Media"),
    ("TIPS.NS",         "Tips Music",                  "Media"),
    ("BALRAMCHIN.NS",   "Balrampur Chini Mills",       "Sugar"),
    ("RENUKA.NS",       "Shree Renuka Sugars",         "Sugar"),
    ("DHAMPURSUG.NS",   "Dhampur Sugar",               "Sugar"),
    ("TRIVENI.NS",      "Triveni Engineering",         "Sugar"),
    ("ZUARI.NS",        "Zuari Industries",            "Fertilizers"),
    ("GSFC.NS",         "Gujarat State Fertilizers",   "Fertilizers"),
    ("COROMANDEL.NS",   "Coromandel International",    "Fertilizers"),
    ("IFFCO.NS",        "IFFCO Tokio",                 "Insurance"),
    ("ABSLAMC.NS",      "Aditya Birla Sun Life AMC",   "AMC"),
    ("UTI.NS",          "UTI AMC",                     "AMC"),
    ("JSWENERGY.NS",    "JSW Energy",                  "Power"),
    ("ADANIGREEN.NS",   "Adani Green Energy",          "Renewable Energy"),
    ("ADANITRANS.NS",   "Adani Transmission",          "Power"),
    ("ADANIPOWER.NS",   "Adani Power",                 "Power"),
    ("TORNTPOWER.NS",   "Torrent Power",               "Power"),
    ("KALYNA.NS",       "Kalyan Jewellers",            "Jewellery"),
    ("RAJESHEXPO.NS",   "Rajesh Exports",              "Jewellery"),
    ("PCJEWELLER.NS",   "PC Jeweller",                 "Jewellery"),
    ("THANGAMAYL.NS",   "Thangamayil Jewellery",       "Jewellery"),
    ("SENCO.NS",        "Senco Gold",                  "Jewellery"),
    ("SJS.NS",          "SJS Enterprises",             "Consumer"),
    ("CLEAN.NS",        "Clean Science",               "Chemicals"),
    ("EPIGRAL.NS",      "Epigral",                     "Chemicals"),
    ("ANUPAM.NS",       "Anupam Rasayan",              "Chemicals"),
    ("NFASSL.NS",       "NFA SSL",                     "Chemicals"),
    ("BEML.NS",         "BEML",                        "Defence"),
    ("COCHINSHIP.NS",   "Cochin Shipyard",             "Defence"),
    ("MAZDOCK.NS",      "Mazagon Dock",                "Defence"),
    ("GRSE.NS",         "Garden Reach Shipbuilders",   "Defence"),
    ("PARAS.NS",        "Paras Defence",               "Defence"),
    ("IDEAFORGE.NS",    "ideaForge Technology",        "Defence"),
    ("DATAPATTNS.NS",   "Data Patterns India",         "Defence"),
    ("MTAR.NS",         "MTAR Technologies",           "Defence"),
    ("SOLARINDS.NS",    "Solar Industries India",      "Defence"),
    ("DCAL.NS",         "Dishman Carbogen Amcis",      "Pharma"),
    ("MARKSANS.NS",     "Marksans Pharma",             "Pharma"),
    ("GLENMARK.NS",     "Glenmark Life Sciences",      "Pharma"),
    ("TORNTPHARM.NS",   "Torrent Pharma",              "Pharma"),
    ("ZYDUSCAD.NS",     "Zydus Cadila",                "Pharma"),
]

def _hardcoded_fallback() -> pd.DataFrame:
    df = pd.DataFrame(_HARDCODED, columns=["ticker_ns", "company_name", "industry"])
    df = df.drop_duplicates(subset="ticker_ns")
    print(f"  ✓ Hardcoded fallback: {len(df)} constituents")
    return df


# ──────────────────────────────────────────────────────────────
#  MAIN BUILD FUNCTION
# ──────────────────────────────────────────────────────────────
def build_universe(force: bool = False) -> pd.DataFrame:
    """
    Builds universe.parquet if missing or stale.
    Returns the DataFrame of {ticker_ns, company_name, industry}.
    """
    if not force and os.path.exists(UNIVERSE_FILE):
        age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(UNIVERSE_FILE))).days
        if age < UNIVERSE_TTL_DAYS:
            return pd.read_parquet(UNIVERSE_FILE)

    print("Building NIFTY 500 universe…")

    df = _fetch_nse_csv()
    if df is None or len(df) < 100:
        print("  Trying Wikipedia fallback…")
        df = _fetch_wikipedia()
    if df is None or len(df) < 100:
        print("  Using hardcoded fallback…")
        df = _hardcoded_fallback()

    df = df.drop_duplicates(subset="ticker_ns").reset_index(drop=True)
    df.to_parquet(UNIVERSE_FILE, index=False)
    print(f"  Universe saved: {len(df)} stocks → {UNIVERSE_FILE}")
    return df


def load_universe() -> pd.DataFrame:
    """Load universe from disk if available, build it otherwise."""
    if os.path.exists(UNIVERSE_FILE):
        return pd.read_parquet(UNIVERSE_FILE)
    return build_universe()


def universe_is_fresh() -> bool:
    if not os.path.exists(UNIVERSE_FILE):
        return False
    age = (datetime.now() - datetime.fromtimestamp(os.path.getmtime(UNIVERSE_FILE))).days
    return age < UNIVERSE_TTL_DAYS


if __name__ == "__main__":
    df = build_universe(force=True)
    print(df.head(10).to_string(index=False))
    print(f"\nTotal: {len(df)} stocks in universe.")
