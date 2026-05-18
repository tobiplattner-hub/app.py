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
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# GOOGLE SHEETS LIVE-IMPORT (DEINE DEKLARIERTE TABELLEN-ID)
# ==============================================================================
# Deine Live-ID ist hier fest hinterlegt:
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo" 

def lade_maschinen_aus_sheets():
    try:
        # Lädt dein spezifisches Blatt "preisliste"
        url_maschinen = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=preisliste"
        df_masch = pd.read_csv(url_maschinen)
        
        # Bereinigung: Spaltennamen von eventuellen Leerzeichen befreien
        df_masch.columns = df_masch.columns.str.strip()
        return df_masch
    except Exception as e:
        st.sidebar.error("Fehler beim Laden aus Google Sheets. Bitte prüfe, ob das Sheet auf 'Jeder, der den Link hat, kann ansehen' freigegeben ist und die Spalten exakt 'geraet' und 'Preis' heißen.")
        return None

# ==============================================================================
# UNIVERSAL PDF GENERATOR
# ==============================================================================
def erstelle_universal_pdf(titel, metadaten_text, posten_daten, gesamt_summe, zusatz_info=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor('#1b5e20'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, leading=16)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=11, leading=16, fontName='Helvetica-Bold')

    if os.path.exists("logo.png"):
        try:
            logo = Image("logo.png", width=240, height=90)
            logo.hAlign = 'RIGHT'
            story.append(logo)
            story.append(Spacer(1, 10))
        except:
            pass

    story.append(Paragraph(f"<b>{titel}</b>", title_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph(metadaten_text, normal_style))
    story.append(Spacer(1, 20))

    table_content = [[Paragraph('<b>Position / Beschreibung</b>', normal_style), Paragraph('<b>Details</b>', normal_style), Paragraph('<b>Betrag</b>', normal_style)]]
    for p in posten_daten:
        table_content.append([Paragraph(p[0], normal_style), Paragraph(p[1], normal_style), Paragraph(p[2], normal_style)])
    
    table_content.append(['', Paragraph('<b>Gesamtsumme:</b>', bold_style), Paragraph(f"<b>{gesamt_summe:,.2f} €</b>", bold_style)])
    
    t = Table(table_content, colWidths=[280, 120, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('TOPPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.grey),
        ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.HexColor('#1b5e20')),
        ('TOPPADDING', (1,-1), (-1,-1), 10),
    ]))
    
    for i in range(3):
        table_content[0][i].style.textColor = colors.whitesmoke

    story.append(t)
    story.append(Spacer(1, 30))
    story.append(Paragraph(f"<i>{zusatz_info}</i>", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 2. DATA SYSTEM & LOCAL STORAGE
# ==============================================================================
DB_DATEI = "ls25_multiplayer_live_data.json"
START_KONTO_HOF1 = 500000.0
START_KONTO_HOF2 = 350000.0
START_KONTO_HOF3 = 200000.0

def lade_globalen_speicher():
    default_daten = {
        "hoefe": {
            "Hof 1": {"name": "Hof 1 - Hauptbetrieb (LU)", "konto": START_KONTO_HOF1},
            "Hof 2": {"name": "Hof 2 - Bio-Betrieb", "konto": START_KONTO_HOF2},
            "Hof 3": {"name": "Hof 3 - Freier Verbund", "konto": START_KONTO_HOF3}
        },
        "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Kartoffeln", "Zuckerrüben", "Silage"],
        "preise": {
            "Weizen": 850.0, "Gerste": 780.0, "Raps": 1450.0, "Gras": 220.0, "Mais": 900.0, "Kartoffeln": 450.0, "Zuckerrüben": 320.0, "Silage": 410.0
        },
        "felder": [
            {"id": 1, "besitzer": "Hof 1", "groesse": 4.5, "frucht": "Weizen", "status": "Wachstum", "ernte_typ": "Normale Ernte"},
            {"id": 2, "besitzer": "Hof 2", "groesse": 2.1, "frucht": "Mais", "status": "Erntebereit", "ernte_typ": "Silage"}
        ],
        "auftraege": [],
        "verkaeufe": []
    }
    if not os.path.exists(DB_DATEI):
        speichere_globalen_speicher(default_daten)
        return default_daten
    try:
        with open(DB_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
            if "preise" not in daten:
                daten["preise"] = default_daten["preise"]
            return daten
    except:
        return default_daten

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()

# Live-Abruf der Fahrzeuge aus deiner echten Google Sheets "preisliste"
df_sheet_masch = lade_maschinen_aus_sheets()

HOF_MAPPING = {
    "Hof 1": db["hoefe"]["Hof 1"]["name"],
    "Hof 2": db["hoefe"]["Hof 2"]["name"],
    "Hof 3": db["hoefe"]["Hof 3"]["name"]
}

# ==============================================================================
# SIDEBAR & SERVER-ZENTRALE
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/tractor.png", width=80)
st.sidebar.title("⚙️ Server-Zentrale")

with st.sidebar.expander("📝 Hofnamen live ändern"):
    h1_n = st.text_input("Name Hof 1:", db["hoefe"]["Hof 1"]["name"])
    h2_n = st.text_input("Name Hof 2:", db["hoefe"]["Hof 2"]["name"])
    h3_n = st.text_input("Name Hof 3:", db["hoefe"]["Hof 3"]["name"])
    if st.button("Hofnamen synchronisieren"):
        db["hoefe"]["Hof 1"]["name"] = h1_n
        db["hoefe"]["Hof 2"]["name"] = h2_n
        db["hoefe"]["Hof 3"]["name"] = h3_n
        speichere_globalen_speicher(db)
        st.success("Namen global aktualisiert!")
        st.rerun()

bereich = st.sidebar.radio(
    "Menüpunkt auswählen:",
    ["📊 Dashboard & Finanzen", "💼 LU-Auftragsbuch", "🌾 Warenverkauf & Rechnungen", "📈 Fruchtpreise (Manuell)", "🗺️ Feldverwaltung"]
)

# ==============================================================================
# BEREICH 1: DASHBOARD & FINANZEN
# ==============================================================================
if bereich == "📊 Dashboard & Finanzen":
    st.title("🚜 LS25 Server-Dashboard")
    col1, col2, col3 = st.columns(3)
    for i, (k, v) in enumerate(db["hoefe"].items()):
        with [col1, col2, col3][i]:
            st.metric(label=v["name"], value=f"{v['konto']:,.2f} €")

# ==============================================================================
# BEREICH 2: LU-AUFTRAGSBUCH
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 LU-Betriebsstunden-Abrechnung")
    
    st.subheader("📌 Neuen Lohnauftrag anlegen")
    col_a, col_b = st.columns(2)
    
    with col_a:
        a_kunde = st.selectbox("Auftraggeber (Kunde):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        a_lu = st.selectbox("Auftragnehmer (Lohnunternehmen):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        a_typ = st.selectbox("Arbeitsart:", ["Dreschen", "Häckseln", "Pflügen", "Säen", "Gülle fahren", "Ballen pressen"])
        
    with col_b:
        # Filtert die Liste der Geräte aus deiner Spalte 'geraet' aus Google Sheets
        if df_sheet_masch is not None and 'geraet' in df_sheet_masch.columns:
            verfuegbare_maschinen = df_sheet_masch['geraet'].dropna().unique().tolist()
        else:
            verfuegbare_maschinen = ["Standard Schlepper (Kein Sheet geladen)"]
            
        a_maschine = st.selectbox("Genutztes Fahrzeug (aus Google Sheet 'preisliste'):", verfuegbare_maschinen)
        a_feld = st.number_input("Auf Feld Nummer:", min_value=1, step=1)
        
    if st.button("Auftrag live ausschreiben"):
        neuer_id = max([x["id"] for x in db["auftraege"]], default=0) + 1
        
        # Holt den Stundensatz aus deiner Google-Spalte 'Preis'
        stundensatz_aus_sheet = 150.0  # Fallback
        if df_sheet_masch is not None and a_maschine in df_sheet_masch['geraet'].values:
            stundensatz_aus_sheet = float(df_sheet_masch[df_sheet_masch['geraet'] == a_maschine]['Preis'].values[0])
            
        db["auftraege"].append({
            "id": neuer_id, "kunde": a_kunde, "auftragnehmer": a_lu, "typ": a_typ,
            "feld": int(a_feld), "maschine": a_maschine, "stundensatz": stundensatz_aus_sheet, "status": "Offen"
        })
        speichere_globalen_speicher(db)
        st.success(f"Auftrag mit ID #{neuer_id} registriert. Preis laut Google Sheet: {stundensatz_aus_sheet} €/h.")
        st.rerun()

    st.write("---")
    st.subheader("💳 Offene Aufträge über Zählerstände abrechnen")
    offene = [x for x in db["auftraege"] if x["status"] == "Offen"]
    
    if offene:
        df_offene = pd.DataFrame(offene)
        df_offene["Kunde"] = df_offene["kunde"].map(HOF_MAPPING)
        df_offene["Lohnunternehmen"] = df_offene["auftragnehmer"].map(HOF_MAPPING)
        st.dataframe(df_offene[["id", "Kunde", "Lohnunternehmen", "typ", "maschine", "stundensatz"]], use_container_width=True, hide_index=True)
        
        col_c, col_d = st.columns(2)
        with col_c:
            auf_id = st.selectbox("Welchen Auftrag jetzt abrechnen?", [x["id"] for x in offene])
            std_start = st.number_input("Betriebsstunden START:", min_value=0.0, step=0.1, key="start")
        with col_d:
            std_ende = st.number_input("Betriebsstunden ENDE:", min_value=std_start, step=0.1, key="ende")
            
        if st.button("💰 Zählerstände auswerten & Rechnung buchen"):
            stunden_gefahren = std_ende - std_start
            auftrag = next(x for x in db["auftraege"] if x["id"] == auf_id)
            
            # Preisberechnung (Stunden * Google Sheet Preis)
            end_preis = stunden_gefahren * auftrag["stundensatz"]
            
            # 50% Rabatt-Automatik falls das Zielfeld auf Silage steht
            feld_treffer = next((f for f in db["felder"] if f["id"] == auftrag["feld"]), None)
            if feld_treffer and feld_treffer.get("ernte_typ") == "Silage":
                end_preis *= 0.5
                
            auftrag["preis"] = end_preis
            auftrag["stunden_gefahren"] = stunden_gefahren
            auftrag["status"] = "Abgerechnet"
            
            # Geldtransfer durchführen
            db["hoefe"][auftrag["kunde"]]["konto"] -= end_preis
            db["hoefe"][auftrag["auftragnehmer"]]["konto"] += end_preis
            speichere_globalen_speicher(db)
            
            # PDF-Inhalt generieren
            meta = f"<b>Dienstleister:</b> {HOF_MAPPING[auftrag['auftragnehmer']]}<br/><b>Kunde:</b> {HOF_MAPPING[auftrag['kunde']]}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}"
            posten = [[f"Lohnarbeit: {auftrag['typ']} (Feld {auftrag['feld']})", f"{stunden_gefahren:.1f} Betriebsstunden auf {auftrag['maschine']} ({auftrag['stundensatz']} €/h)", f"{end_preis:,.2f} €"]]
            
            st.session_state["pdf_temp"] = erstelle_universal_pdf("LU-BETRIEBSSTUNDEN RECHNUNG", meta, posten, end_preis, "Automatisch erfasst und über das Server-Kassenbuch beglichen.")
            st.success("Erfolgreich abgerechnet!")
            st.rerun()
            
        if "pdf_temp" in st.session_state:
            st.download_button("📄 PDF-Abrechnungsbeleg herunterladen", data=st.session_state["pdf_temp"], file_name="LU_Abrechnung_Stunden.pdf", mime="application/pdf")
    else:
        st.info("Hervorragend! Keine offenen Aufträge im System.")

# ==============================================================================
# BEREICH 3: WARENVERKAUF MIT RECHNUNGSZENTRUM
# ==============================================================================
elif bereich == "🌾 Warenverkauf & Rechnungen":
    st.title("🌾 Verkaufsrechnungen (Getreide- & Ernte-Verkauf)")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_verkaeufer = st.selectbox("Verkaufender Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        v_kaeufer = st.selectbox("Empfänger / Käufer:", ["Zentrale Verkaufsstelle (Server-Bank)", "Hof 1", "Hof 2", "Hof 3"], 
                                 format_func=lambda x: HOF_MAPPING[x] if x in HOF_MAPPING else x)
        v_frucht = st.selectbox("Verkaufte Fruchtart:", db["fruchtarten"])
        
    with col_v2:
        v_menge = st.number_input("Menge in Liter (L):", min_value=0, step=1000, value=10000)
        
        preis_pro_1k = float(db["preise"].get(v_frucht, 500.0))
        st.info(f"💵 Aktueller App-Livepreis: **{preis_pro_1k:,.2f} €** pro 1.000 Liter")
        
    if st.button("🚀 Verkauf abrechnen & Gutschrift erstellen"):
        gesamt_erloes = (v_menge / 1000) * preis_pro_1k
        
        db["hoefe"][v_verkaeufer]["konto"] += gesamt_erloes
        if v_kaeufer in db["hoefe"]:
            db["hoefe"][v_kaeufer]["konto"] -= gesamt_erloes
            
        db["verkaeufe"].append({
            "id": max([x.get("id", 0) for x in db["verkaeufe"]], default=0) + 1,
            "verkaeufer": v_verkaeufer, "kaeufer": v_kaeufer, "frucht": v_frucht, "menge": v_menge, "erloes": gesamt_erloes
        })
        speichere_globalen_speicher(db)
        
        kaeufer_name = HOF_MAPPING[v_kaeufer] if v_kaeufer in HOF_MAPPING else v_kaeufer
        meta_v = f"<b>Verkäufer:</b> {HOF_MAPPING[v_verkaeufer]}<br/><b>Käufer:</b> {kaeufer_name}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y - %H:%M')}"
        posten_v = [[f"Lieferung von {v_frucht}", f"{v_menge:,} Liter (Satz: {preis_pro_1k} € / 1.000L)", f"{gesamt_erloes:,.2f} €"]]
        
        st.session_state["pdf_verkauf"] = erstelle_universal_pdf("OFFIZIELLER WAREN-VERKAUFSBELEG", meta_v, posten_v, gesamt_erloes, "Die Ware wurde geliefert und die Gutschrift auf dem Konto registriert.")
        st.success(f"Erfolgreich! {gesamt_erloes:,.2f} € wurden gebucht.")
        st.rerun()

    if "pdf_verkauf" in st.session_state:
        st.download_button("📄 Verkaufs-PDF herunterladen", data=st.session_state["pdf_verkauf"], file_name="Verkaufsabrechnung.pdf", mime="application/pdf")

# ==============================================================================
# BEREICH 4: MANUELLE FRUCHTPREISE
# ==============================================================================
elif bereich == "📈 Fruchtpreise (Manuell)":
    st.title("🌾 Fruchtpreis-Zentrale für den Server")
    st.write("Ändere hier die Kurse manuell. Die Werte gelten sofort für alle Berechnungen im Warenverkauf.")
    
    df_preise = pd.DataFrame(list(db["preise"].items()), columns=["Fruchtart", "Preis pro 1.000L (€)"])
    st.dataframe(df_preise, use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("🔄 Preis anpassen")
    f_auswahl = st.selectbox("Fruchtart auswählen:", db["fruchtarten"])
    neuer_preis = st.number_input("Neuer Preis (€):", value=float(db["preise"].get(f_auswahl, 500.0)), step=10.0)
    
    if st.button("Kurs live aktualisieren"):
        db["preise"][f_auswahl] = neuer_preis
        speichere_globalen_speicher(db)
        st.success(f"Der Preis für {f_auswahl} steht jetzt global auf {neuer_preis} €.")
        st.rerun()

# ==============================================================================
# BEREICH 5: FELDVERWALTUNG
# ==============================================================================
elif bereich == "🗺️ Feldverwaltung":
    st.title("🗺️ Globale Feldverwaltung")
    if db["felder"]:
        df_felder = pd.DataFrame(db["felder"])
        st.dataframe(df_felder, use_container_width=True, hide_index=True)
