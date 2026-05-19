import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Für die PDF-Generierung
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# ==============================================================================
# 1. SEITEN-KONFIGURATION & STYLING
# ==============================================================================
st.set_page_config(
    page_title="LS25 Live Multiplayer Hof- & LU-Manager",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #f4f6f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #2e7d32; }
    h1, h2, h3 { color: #1b5e20; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #2e7d32; color: white; border-radius: 8px; width: 100%; }
    .stButton>button:hover { background-color: #1b5e20; color: white; }
    .stDataFrame { background-color: #ffffff; border-radius: 8px; padding: 5px; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# GOOGLE SHEETS LIVE-IMPORT
# ==============================================================================
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo" 

def lade_maschinen_aus_sheets():
    try:
        url_maschinen = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=preisliste"
        df_masch = pd.read_csv(url_maschinen)
        df_masch.columns = df_masch.columns.str.strip().str.lower()
        if 'geraet' in df_masch.columns and 'preis' in df_masch.columns:
            return df_masch.rename(columns={'geraet': 'geraet', 'preis': 'Preis'})
        return None
    except: return None

def lade_kunden_aus_sheets():
    try:
        url_kunden = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=kunden"
        df_kunden = pd.read_csv(url_kunden)
        return df_kunden.iloc[:, 0].dropna().unique().tolist()
    except: return None

# ==============================================================================
# UNIVERSAL PDF GENERATOR
# ==============================================================================
def erstelle_universal_pdf(titel, metadaten_text, posten_daten, gesamt_summe, zusatz_info=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"<b>{titel}</b>", styles['Heading1']))
    story.append(Paragraph(metadaten_text, styles['Normal']))
    story.append(Spacer(1, 20))
    table_content = [['Position', 'Details', 'Betrag']] + posten_daten + [['', 'Gesamt:', f"{gesamt_summe:,.2f} €"]]
    story.append(Table(table_content))
    story.append(Paragraph(f"<i>{zusatz_info}</i>", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 2. DATA SYSTEM
# ==============================================================================
DB_DATEI = "ls25_multiplayer_live_data.json"

def generiere_standard_daten():
    return {
        "aktueller_monat": "Januar",
        "hoefe": {"Hof 1": {"name": "Hof 1", "konto": 0}, "Hof 2": {"name": "Hof 2", "konto": 0}, "Hof 3": {"name": "Hof 3", "konto": 0}},
        "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Silage (Silo)"],
        "preise": {"Weizen": 850.0, "Gerste": 780.0, "Raps": 1450.0, "Gras": 220.0, "Mais": 900.0, "Silage (Silo)": 410.0},
        "lager": {"Hof 1": {"Weizen": 0, "Gerste": 0, "Raps": 0, "Gras": 0, "Mais": 0, "Silage (Silo)": 0}, "Hof 2": {"Weizen": 0, "Gerste": 0, "Raps": 0, "Gras": 0, "Mais": 0, "Silage (Silo)": 0}, "Hof 3": {"Weizen": 0, "Gerste": 0, "Raps": 0, "Gras": 0, "Mais": 0, "Silage (Silo)": 0}},
        "verkaeufe": [], "felder": [], "auftraege": [], "kalender": []
    }

def lade_globalen_speicher():
    if not os.path.exists(DB_DATEI):
        d = generiere_standard_daten()
        speichere_globalen_speicher(d)
        return d
    with open(DB_DATEI, "r", encoding="utf-8") as f: return json.load(f)

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()
df_sheet_masch = lade_maschinen_aus_sheets()
HOF_MAPPING = {k: v["name"] for k, v in db["hoefe"].items()}

# ==============================================================================
# 3. SIDEBAR & NAVIGATION
# ==============================================================================
bereich = st.sidebar.radio("Menüpunkt:", ["📊 Dashboard & Finanzen", "💼 LU-Auftragsbuch", "🌾 Warenverkauf & Rechnungen", "🚜 Fuhrpark & Geräte", "📈 Fruchtpreise (Manuell)", "🗺️ Feldverwaltung", "📅 Sähe- & Erntekalender", "📦 Hof-Lagerverwaltung"])

# ==============================================================================
# LOGIK DER BEREICHE
# ==============================================================================

if bereich == "📊 Dashboard & Finanzen":
    st.title("📊 Dashboard")
    for k, v in db["hoefe"].items(): st.metric(v["name"], f"{v['konto']:,.2f} €")

elif bereich == "🌾 Warenverkauf & Rechnungen":
    st.title("🌾 Warenverkauf")
    hof = st.selectbox("Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    frucht = st.selectbox("Frucht:", db["fruchtarten"])
    
    # LIVE-LAGER-ANZEIGE
    bestand = db["lager"][hof].get(frucht, 0)
    st.info(f"Lagerbestand {frucht}: {bestand} L")
    
    menge = st.number_input("Menge (L):", min_value=0, max_value=int(bestand))
    if st.button("Verkauf abschließen"):
        preis = db["preise"].get(frucht, 0)
        summe = (menge / 1000) * preis
        # Buchung
        db["hoefe"][hof]["konto"] += summe
        db["lager"][hof][frucht] -= menge # <-- HIER DIE AUTOMATISCHE ABBUCHUNG
        db["verkaeufe"].append({"hof": hof, "frucht": frucht, "menge": menge, "summe": summe})
        speichere_globalen_speicher(db)
        st.success("Verkauft & Lager angepasst!")
        st.rerun()

elif bereich == "📦 Hof-Lagerverwaltung":
    st.title("📦 Lagerverwaltung")
    hof = st.selectbox("Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    for f in db["fruchtarten"]:
        db["lager"][hof][f] = st.number_input(f, value=int(db["lager"][hof].get(f, 0)))
    if st.button("Lager speichern"): 
        speichere_globalen_speicher(db)
        st.success("Gespeichert!")

# [Hier könnten die restlichen Bereiche wie Fuhrpark etc. folgen...]
else:
    st.write("Wähle einen Bereich in der Sidebar.")
