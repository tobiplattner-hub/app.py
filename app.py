import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# --- 1. KONFIGURATION & INITIALISIERUNG ---
st.set_page_config(page_title="LS25 Live Manager", page_icon="🚜", layout="wide")
DB_DATEI = "ls25_multiplayer_live_data.json"
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
MONATE_LISTE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

# --- HILFSFUNKTIONEN (Sheets & PDF) ---
def lade_maschinen_aus_sheets():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=preisliste"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.lower()
        return df.rename(columns={'geraet': 'geraet', 'preis': 'Preis'})
    except: return None

def lade_kunden_aus_sheets():
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=kunden"
        df = pd.read_csv(url)
        return df.iloc[:, 0].dropna().unique().tolist()
    except: return None

def erstelle_universal_pdf(titel, meta, posten, summe, info):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph(f"<b>{titel}</b>", styles['Heading1']))
    story.append(Paragraph(meta, styles['Normal']))
    story.append(Spacer(1, 20))
    table_data = [['Position', 'Details', 'Betrag']] + posten + [['', 'Gesamt:', f"{summe:,.2f} €"]]
    story.append(Table(table_data))
    story.append(Paragraph(f"<i>{info}</i>", styles['Normal']))
    doc.build(story)
    buffer.seek(0)
    return buffer

def lade_globalen_speicher():
    if not os.path.exists(DB_DATEI):
        return {
            "aktueller_monat": "Januar", "hoefe": {"Hof 1": {"name": "Hof 1", "konto": 0}, "Hof 2": {"name": "Hof 2", "konto": 0}, "Hof 3": {"name": "Hof 3", "konto": 0}},
            "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais"], "preise": {"Weizen": 850.0, "Gerste": 780.0},
            "lager": {"Hof 1": {"Weizen": 0}, "Hof 2": {"Weizen": 0}, "Hof 3": {"Weizen": 0}}, 
            "auftraege": [], "verkaeufe": [], "felder": [], "hof_nachrichten": [], "manuelle_buchungen": [], "kalender": []
        }
    with open(DB_DATEI, "r", encoding="utf-8") as f: return json.load(f)

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f: json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()
df_sheet_masch = lade_maschinen_aus_sheets()
KUNDEN_AUSWAHL = lade_kunden_aus_sheets() or ["Hof 1", "Hof 2", "Hof 3"]
HOF_MAPPING = {k: v["name"] for k, v in db["hoefe"].items()}

# --- 2. SIDEBAR ---
st.sidebar.title("⚙️ Server-Zentrale")
bereich = st.sidebar.radio("Menü:", ["📊 Dashboard", "💼 LU-Aufträge", "🌾 Warenverkauf", "🚜 Fuhrpark", "📈 Preise", "🗺️ Felder", "📅 Kalender", "📦 Lager"])

# --- 3. LOGIK-BLOCKS ---
if bereich == "📊 Dashboard":
    st.title("📊 Server-Dashboard")
    for k, v in db["hoefe"].items(): st.metric(v["name"], f"{v['konto']:,.2f} €")

elif bereich == "💼 LU-Aufträge":
    st.title("💼 LU-Abrechnung")
    # ... (Dein bisheriger Code für Aufträge) ...

elif bereich == "🌾 Warenverkauf":
    st.title("🌾 Warenverkauf (mit Lager-Automatik)")
    v_hof = st.selectbox("Verkaufender Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    v_frucht = st.selectbox("Frucht:", db["fruchtarten"])
    
    # LIVE-ANZEIGE LAGER
    bestand = db["lager"][v_hof].get(v_frucht, 0)
    st.info(f"Aktueller Bestand in diesem Lager: **{bestand:,} L**")
    
    v_menge = st.number_input("Menge (L):", min_value=0, max_value=int(bestand))
    if st.button("🚀 Verkauf & Lager abbuchen"):
        erloes = (v_menge / 1000) * db["preise"].get(v_frucht, 500)
        db["hoefe"][v_hof]["konto"] += erloes
        db["lager"][v_hof][v_frucht] -= v_menge # LAGER-ABBUCHUNG
        db["verkaeufe"].append({"hof": v_hof, "frucht": v_frucht, "menge": v_menge, "erloes": erloes})
        speichere_globalen_speicher(db)
        st.success(f"Erfolgreich! {v_menge}L abgebucht.")
        st.rerun()

elif bereich == "🚜 Fuhrpark":
    st.title("🚜 Fuhrpark")
    if df_sheet_masch is not None: st.dataframe(df_sheet_masch)

elif bereich == "📈 Preise":
    st.title("📈 Fruchtpreise")
    for f in db["fruchtarten"]: db["preise"][f] = st.number_input(f, value=float(db["preise"].get(f, 500)))
    if st.button("Speichern"): speichere_globalen_speicher(db)

elif bereich == "🗺️ Felder":
    st.title("🗺️ Feldverwaltung")
    df = st.data_editor(pd.DataFrame(db["felder"]))
    if st.button("Speichern"): 
        db["felder"] = df.to_dict('records')
        speichere_globalen_speicher(db)

elif bereich == "📅 Kalender":
    st.title("📅 Kalender")
    st.write(pd.DataFrame(db["kalender"]))

elif bereich == "📦 Lager":
    st.title("📦 Lagerverwaltung")
    hof = st.selectbox("Hof wählen:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    for item, menge in db["lager"][hof].items():
        db["lager"][hof][item] = st.number_input(item, value=int(menge))
    if st.button("Lager speichern"): speichere_globalen_speicher(db)
