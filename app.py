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
            df_masch = df_masch.rename(columns={'geraet': 'geraet', 'preis': 'Preis'})
            return df_masch
        elif len(df_masch.columns) >= 2:
            df_masch.columns = ['geraet', 'Preis']
            return df_masch
        return None
    except Exception as e:
        return None

def lade_kunden_aus_sheets():
    try:
        url_kunden = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=kunden"
        df_kunden = pd.read_csv(url_kunden)
        df_kunden.columns = df_kunden.columns.str.strip().str.lower()
        
        if 'name' in df_kunden.columns:
            return df_kunden['name'].dropna().unique().tolist()
        elif len(df_kunden.columns) > 0:
            return df_kunden.iloc[:, 0].dropna().unique().tolist()
        return None
    except Exception as e:
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
START_KONTO_HOF1 = 0
START_KONTO_HOF2 = 350000.0
START_KONTO_HOF3 = 200000.0

MONATE_LISTE = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def generiere_standard_daten():
    return {
        "aktueller_monat": "Januar",
        "hoefe": {
            "Hof 1": {"name": "Hof 1 - Hauptbetrieb (LU)", "konto": START_KONTO_HOF1},
            "Hof 2": {"name": "Hof 2 - Bio-Betrieb", "konto": START_KONTO_HOF2},
            "Hof 3": {"name": "Hof 3 - Freier Verbund", "konto": START_KONTO_HOF3}
        },
        "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Kartoffeln", "Zuckerrüben", "Silage (Silo)", "Silage (Ballen)"],
        "preise": {
            "Weizen": 850.0, "Gerste": 780.0, "Raps": 1450.0, "Gras": 220.0, "Mais": 900.0, "Kartoffeln": 450.0, "Zuckerrüben": 320.0, "Silage (Silo)": 410.0, "Silage (Ballen)": 460.0
        },
        "lager": {
            "Hof 1": {"Silage (Silo)": 0, "Silage (Ballen)": 0, "Paletten": 0, "Ballen (Allg.)": 0},
            "Hof 2": {"Silage (Silo)": 0, "Silage (Ballen)": 0, "Paletten": 0, "Ballen (Allg.)": 0},
            "Hof 3": {"Silage (Silo)": 0, "Silage (Ballen)": 0, "Paletten": 0, "Ballen (Allg.)": 0}
        },
        "silage_gärung": [],
        "felder": [
            {"id": 1, "besitzer": "Hof 1", "groesse": 4.5, "frucht": "Weizen", "status": "Wachstum", "ernte_typ": "Normale Ernte"},
            {"id": 2, "besitzer": "Hof 2", "groesse": 2.1, "frucht": "Mais", "status": "Erntebereit", "ernte_typ": "Silage"}
        ],
        "auftraege": [],
        "verkaeufe": [],
        "manuelle_buchungen": [],
        "kalender": [
            {"frucht": "Weizen", "saat_von": "September", "saat_bis": "Oktober", "ernte_von": "Juli", "ernte_bis": "August"},
            {"frucht": "Mais", "saat_von": "April", "saat_bis": "Mai", "ernte_von": "Oktober", "ernte_bis": "November"}
        ]
    }

def lade_globalen_speicher():
    default_daten = generiere_standard_daten()
    if not os.path.exists(DB_DATEI):
        speichere_globalen_speicher(default_daten)
        return default_daten
    try:
        with open(DB_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
            if "aktueller_monat" not in daten:
                daten["aktueller_monat"] = "Januar"
            if "silage_gärung" not in daten:
                daten["silage_gärung"] = []
            for key in ["preise", "verkaeufe", "manuelle_buchungen", "auftraege", "felder", "fruchtarten", "kalender", "lager"]:
                if key not in daten:
                    daten[key] = default_daten[key] if key in default_daten else ([] if key != "lager" else default_daten["lager"])
            return daten
    except:
        return default_daten

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()
df_sheet_masch = lade_maschinen_aus_sheets()
sheet_kunden_liste = lade_kunden_aus_sheets()

HOF_MAPPING = {
    "Hof 1": db["hoefe"]["Hof 1"]["name"],
    "Hof 2": db["hoefe"]["Hof 2"]["name"],
    "Hof 3": db["hoefe"]["Hof 3"]["name"]
}

if sheet_kunden_liste:
    KUNDEN_AUSWAHL = sheet_kunden_liste
    KUNDEN_MAPPING = {k: k for k in sheet_kunden_liste}
    for k, v in HOF_MAPPING.items():
        if k not in KUNDEN_MAPPING:
            KUNDEN_MAPPING[k] = v
else:
    KUNDEN_AUSWAHL = ["Hof 1", "Hof 2", "Hof 3"]
    KUNDEN_MAPPING = HOF_MAPPING

# ==============================================================================
# SIDEBAR & SERVER-ZENTRALE
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/tractor.png", width=80)
st.sidebar.title("⚙️ Server-Zentrale")

# Live-In-Game Monat wechseln
idx_monat = MONATE_LISTE.index(db.get("aktueller_monat", "Januar"))
neuer_monat = st.sidebar.selectbox("📅 Aktueller In-Game Monat:", MONATE_LISTE, index=idx_monat)
if neuer_monat != db.get("aktueller_monat"):
    db["aktueller_monat"] = neuer_monat
    speichere_globalen_speicher(db)
    st.sidebar.success(f"Monat auf {neuer_monat} geändert!")
    st.rerun()

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

st.sidebar.write("---")
with st.sidebar.expander("⚠️ Danger Zone (Reset)"):
    st.warning("Das setzt alle Finanzen und Listen komplett auf Null zurück!")
    if st.button("🚨 GANZEN SERVER ZURÜCKSETZEN"):
        neubeginn = generiere_standard_daten()
        speichere_globalen_speicher(neubeginn)
        st.success("Erfolgreich zurückgesetzt! Lade neu...")
        st.rerun()

bereich = st.sidebar.radio(
    "Menüpunkt auswählen:",
    ["📊 Dashboard & Finanzen", "💼 LU-Auftragsbuch", "🌾 Warenverkauf & Rechnungen", "🚜 Fuhrpark & Geräte", "📈 Fruchtpreise (Manuell)", "🗺️ Feldverwaltung", "📅 Sähe- & Erntekalender", "📦 Hof-Lagerverwaltung"]
)

# ==============================================================================
# BEREICH 1: DASHBOARD & FINANZEN
# ==============================================================================
if bereich == "📊 Dashboard & Finanzen":
    st.title("🚜 LS25 Server-Dashboard")
    
    st.info(f"📅 **Aktuelle Server-Saison:** {db.get('aktueller_monat', 'Januar')}")
    
    col1, col2, col3 = st.columns(3)
    for i, (k, v) in enumerate(db["hoefe"].items()):
        with [col1, col2, col3][i]:
            st.metric(label=v["name"], value=f"{v['konto']:,.2f} €")
            
    st.write("---")
    
    st.subheader("💰 Manuelle Buchung durchführen (Kassierer-Zentrale)")
    with st.expander("🛠️ Gelder direkt einbuchen oder abbuchen", expanded=False):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            m_hof = st.selectbox("Betroffener Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x], key="m_hof")
            m_art = st.radio("Buchungsart:", ["➕ Gutschrift (Einnahme)", "➖ Abbuchung (Kosten)"])
        with col_m2:
            m_betrag = st.number_input("Betrag (€):", min_value=0.0, step=100.0, value=1000.0)
        with col_m3:
            m_zweck = st.text_input("Verwendungszweck / Grund:", placeholder="z. B. Kredit, Strafe, Bonus, Tierhandel")
            
        if st.button("⚡ Buchung jetzt live erzwingen"):
            if m_zweck.strip() == "":
                st.error("Bitte gib einen Vermwendungszweck an!")
            else:
                effektiver_betrag = m_betrag if "Guts" in m_art else -m_betrag
                db["hoefe"][m_hof]["konto"] += effektiver_betrag
                
                db["manuelle_buchungen"].append({
                    "datum": datetime.now().strftime('%d.%m.%Y - %H:%M'),
                    "hof": m_hof,
                    "typ": "Guts" if "Guts" in m_art else "Abbuchung",
                    "betrag": m_betrag,
                    "zweck": m_zweck
                })
                speichere_globalen_speicher(db)
                st.success(f"Erfolgreich verbucht! {m_art} über {m_betrag:,.2f} € für {HOF_MAPPING[m_hof]}.")
                st.rerun()

    st.write("---")
    st.subheader("📖 Zentrales Server-Kassenbuch")
    
    tab1, tab2, tab3 = st.tabs(["💼 Abgerechnete LU-Aufträge", "🌾 Getätigte Warenverkäufe", "🛠️ Manuelle Buchungen & Korrekturen"])
    
    with tab1:
        erledigte_auftraege = [x for x in db["auftraege"] if x.get("status") == "Abgerechnet"]
        if erledigte_auftraege:
            df_erledigt = pd.DataFrame(erledigte_auftraege)
            for col in ["id", "kunde", "auftragnehmer", "typ", "maschine", "stunden_gefahren", "preis"]:
                if col not in df_erledigt.columns:
                    df_erledigt[col] = 0 if col in ["stunden_gefahren", "preis", "id"] else "Unbekannt"
            df_erledigt["Kunde"] = df_erledigt["kunde"].map(lambda x: KUNDEN_MAPPING.get(x, x))
            df_erledigt["Lohnunternehmen"] = df_erledigt["auftragnehmer"].map(HOF_MAPPING)
            st.dataframe(
                df_erledigt[["id", "Kunde", "Lohnunternehmen", "typ", "maschine", "stunden_gefahren", "preis"]].rename(
                    columns={"typ": "Arbeit", "maschine": "Fahrzeug", "stunden_gefahren": "Betriebsstunden", "preis": "Erlös (€)"}
                ), use_container_width=True, hide_index=True
            )
        else:
            st.info("Es wurden noch keine Lohnaufträge über Betriebsstunden abgerechnet.")
            
    with tab2:
        if db["verkaeufe"]:
            df_v = pd.DataFrame(db["verkaeufe"])
            for col in ["id", "verkaeufer", "kaeufer", "frucht", "menge", "erloes"]:
                if col not in df_v.columns:
                    df_v[col] = 0 if col in ["id", "menge", "erloes"] else "Unbekannt"
            df_v["Verkäufer"] = df_v["verkaeufer"].map(HOF_MAPPING)
            df_v["Käufer"] = df_v["kaeufer"].map(lambda x: KUNDEN_MAPPING.get(x, x))
            st.dataframe(
                df_v[["id", "Verkäufer", "Käufer", "frucht", "menge", "erloes"]].rename(
                    columns={"frucht": "Ware", "menge": "Menge (L)", "erloes": "Umsatz (€)"}
                ), use_container_width=True, hide_index=True
            )
        else:
            st.info("Es wurden noch keine Warenverkäufe verbucht.")

    with tab3:
        if db.get("manuelle_buchungen"):
            df_m = pd.DataFrame(db["manuelle_buchungen"])
            df_m["Hof"] = df_m["hof"].map(HOF_MAPPING)
            st.dataframe(
                df_m[["datum", "Hof", "typ", "betrag", "zweck"]].rename(
                    columns={"datum": "Zeitpunkt", "typ": "Art", "betrag": "Betrag (€)", "zweck": "Grund"}
                ), use_container_width=True, hide_index=True
            )
        else:
            st.info("Bisher keine manuellen Korrekturbuchungen durchgeführt.")

# ==============================================================================
# BEREICH 2: LU-AUFTRAGSBUCH
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 LU-Betriebsstunden-Abrechnung")
    
    st.subheader("📌 Neuen Lohnauftrag anlegen")
    col_a, col_b = st.columns(2)
    
    with col_a:
        a_kunde = st.selectbox("Auftraggeber (Kunde aus Google Sheet):", KUNDEN_AUSWAHL, format_func=lambda x: KUNDEN_MAPPING.get(x, x))
        a_lu = st.selectbox("Auftragnehmer (Lohnunternehmen):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        
        arbeitsart_optionen = db["fruchtarten"] + ["Dreschen", "Häckseln", "Pflügen", "Säen", "Gülle fahren", "Ballen pressen", "– Eigene Mod-Arbeitsart eingeben –"]
        a_typ_sel = st.selectbox("Arbeitsart:", arbeitsart_optionen)
        
        if a_typ_sel == "– Eigene Mod-Arbeitsart eingeben –":
            a_typ = st.text_input("Name der Mod-Frucht / Arbeit eingeben:", placeholder="z. B. Klee dreschen, Luzerne häckseln")
        else:
            a_typ = a_typ_sel
        
    with col_b:
        if df_sheet_masch is not None and 'geraet' in df_sheet_masch.columns:
            verfuegbare_machines = df_sheet_masch['geraet'].dropna().unique().tolist()
        else:
            verfuegbare_machines = ["Standard Schlepper (Kein Sheet geladen)"]
            
        a_maschine = st.selectbox("Genutztes Fahrzeug (aus Google Sheet 'preisliste'):", verfuegbare_machines)
        a_feld = st.number_input("Auf Feld Nummer:", min_value=1, step=1)
        
    if st.button("Auftrag live ausschreiben"):
        if a_typ.strip() == "":
            st.error("Bitte gib einen Namen für die Mod-Arbeitsart ein!")
        else:
            neuer_id = max([x["id"] for x in db["auftraege"]], default=0) + 1
            stundensatz_aus_sheet = 150.0
            
            if df_sheet_masch is not None and 'geraet' in df_sheet_masch.columns and a_maschine in df_sheet_masch['geraet'].values:
                treffer = df_sheet_masch[df_sheet_masch['geraet'] == a_maschine]['Preis'].values
                if len(treffer) > 0:
                    stundensatz_aus_sheet = float(treffer[0])
                
            db["auftraege"].append({
                "id": neuer_id, "kunde": a_kunde, "auftragnehmer": a_lu, "typ": a_typ,
                "feld": int(a_feld), "maschine": a_maschine, "stundensatz": stundensatz_aus_sheet, "status": "Offen"
            })
            speichere_globalen_speicher(db)
            st.success(f"Auftrag mit ID #{neuer_id} registriert. Preis: {stundensatz_aus_sheet} €/h.")
            st.rerun()

    st.write("---")
    st.subheader("💳 Offene Aufträge über Zählerstände abrechnen")
    offene = [x for x in db["auftraege"] if x["status"] == "Offen"]
    
    if offene:
        df_offene = pd.DataFrame(offene)
        df_offene["Kunde"] = df_offene["kunde"].map(lambda x: KUNDEN_MAPPING.get(x, x))
        df_offene["Lohnunternehmen"] = df_offene["auftragnehmer"].map(HOF_MAPPING)
        st.dataframe(df_offene[["id", "Kunde", "Lohnunternehmen", "typ", "maschine", "stundensatz"]], use_container_width=True, hide_index=True)
        
        col_c, col_d = st.columns(2)
        with col_c:
            auf_id = st.selectbox("Welchen Auftrag jetzt abrechnen?", [x["id"] for x in offene], key="select_auf_id")
            std_start = st.number_input("Betriebsstunden START:", min_value=0.0, step=0.1, key="start")
        with col_d:
            std_ende = st.number_input("Betriebsstunden ENDE:", min_value=std_start, step=0.1, key="ende")
            
        if st.button("💰 Zählerstände auswerten & Rechnung buchen"):
            stunden_gefahren = std_ende - std_start
            auftrag = next(x for x in db["auftraege"] if x["id"] == auf_id)
            end_preis = stunden_gefahren * auftrag["stundensatz"]
            
            feld_treffer = next((f for f in db["felder"] if f["id"] == auftrag["feld"]), None)
            if feld_treffer and feld_treffer.get("ernte_typ") == "Silage":
                end_preis *= 0.5
                
            auftrag["preis"] = end_preis
            auftrag["stunden_gefahren"] = stunden_gefahren
            auftrag["status"] = "Abgerechnet"
            
            # Geldtransfer buchen
            if auftrag["kunde"] in db["hoefe"]:
                db["hoefe"][auftrag["kunde"]]["konto"] -= end_preis
            db["hoefe"][auftrag["auftragnehmer"]]["konto"] += end_preis
            speichere_globalen_speicher(db)
            
            # PDF jetzt direkt generieren und im Session State parken
            k_name = KUNDEN_MAPPING.get(auftrag['kunde'], auftrag['kunde'])
            meta = f"<b>Dienstleister:</b> {HOF_MAPPING[auftrag['auftragnehmer']]}<br/><b>Kunde:</b> {k_name}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}<br/><b>Auftrags-ID:</b> #{auftrag['id']}"
            posten = [[
                f"Lohnarbeit: {auftrag['typ']} (Feld {auftrag['feld']})", 
                f"{stunden_gefahren:.1f} Betriebsstunden auf {auftrag['maschine']}<br/>(Basis: {auftrag['stundensatz']} €/h)", 
                f"{end_preis:,.2f} €"
            ]]
            
            # PDF-Generierung für den Download-Button vorbereiten
            st.session_state["lu_pdf_ready"] = erstelle_universal_pdf("LU-BETRIEBSSTUNDEN ABRECHNUNG", meta, posten, end_preis, "Buchung wurde dem Server-Kassenbuch automatisch belastet/gutgeschrieben.")
            st.session_state["lu_erfolg_msg"] = f"Erfolgreich abgerechnet! {stunden_gefahren:.1f} Std. ergeben einen Betrag von {end_preis:,.2f} €."
            
        # Wenn eine PDF-Abrechnung bereitliegt, zeige sie an
        if "lu_pdf_ready" in st.session_state:
            st.success(st.session_state["lu_erfolg_msg"])
            st.download_button(
                label="📄 PDF-Abrechnungsbeleg herunterladen", 
                data=st.session_state["lu_pdf_ready"], 
                file_name=f"LU_Abrechnung_ID_{auf_id}.pdf", 
                mime="application/pdf"
            )
            if st.button("🔄 Seite aktualisieren (Nächster Auftrag)"):
                if "lu_pdf_ready" in st.session_state: del st.session_state["lu_pdf_ready"]
                if "lu_erfolg_msg" in st.session_state: del st.session_state["lu_erfolg_msg"]
                st.rerun()
    else:
        st.info("Hervorragend! Keine offenen LU-Aufträge im System.")

# ==============================================================================
# BEREICH 3: WARENVERKAUF & RECHNUNGEN
# ==============================================================================
elif bereich == "🌾 Warenverkauf & Rechnungen":
    st.title("🌾 Verkaufsrechnungen (Getreide- & Ernte-Verkauf)")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_verkaeufer = st.selectbox("Verkaufenden Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        v_kaeufer = st.selectbox("Empfänger / Käufer (aus Google Sheet):", KUNDEN_AUSWAHL, format_func=lambda x: KUNDEN_MAPPING.get(x, x))
        
        frucht_optionen = db["fruchtarten"] + ["– Eigene Mod-Frucht eingeben –"]
        v_frucht_sel = st.selectbox("Verkaufte Fruchtart:", frucht_optionen)
        
        if v_frucht_sel == "– Eigene Mod-Frucht eingeben –":
            v_frucht = st.text_input("Name der Mod-Frucht eingeben:", placeholder="z.b. Klee, Alfalfa, Dinkel")
            preis_pro_1k = st.number_input("Manueller Preis (€ pro 1.000L):", min_value=0.0, value=500.0, step=50.0)
        else:
            v_frucht = v_frucht_sel
            preis_pro_1k = float(db["preise"].get(v_frucht, 500.0))
        
    with col_v2:
        v_menge = st.number_input("Menge in Liter (L):", min_value=0, step=1000, value=10000)
        st.info(f"💵 Abrechnungskurs: **{preis_pro_1k:,.2f} €** pro 1.000 Liter")
        
    if st.button("🚀 Verkauf abrechnen"):
        if v_frucht.strip() == "":
            st.error("Bitte gib einen Namen für die Mod-Frucht ein!")
        else:
            if v_frucht.strip() not in db["fruchtarten"]:
                db["fruchtarten"].append(v_frucht.strip())
                db["preise"][v_frucht.strip()] = preis_pro_1k

            gesamt_erloes = (v_menge / 1000) * preis_pro_1k
            db["hoefe"][v_verkaeufer]["konto"] += gesamt_erloes
            if v_kaeufer in db["hoefe"]:
                db["hoefe"][v_kaeufer]["konto"] -= gesamt_erloes
                
            db["verkaeufe"].append({
                "id": max([x.get("id", 0) for x in db["verkaeufe"]], default=0) + 1,
                "verkaeufer": v_verkaeufer, "kaeufer": v_kaeufer, "frucht": v_frucht, "menge": v_menge, "erloes": gesamt_erloes
            })
            speichere_globalen_speicher(db)
            
            kaeufer_name = KUNDEN_MAPPING.get(v_kaeufer, v_kaeufer)
            meta_v = f"<b>Verkäufer:</b> {HOF_MAPPING[v_verkaeufer]}<br/><b>Käufer:</b> {kaeufer_name}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y - %H:%M')}"
            posten_v = [[f"Lieferung von {v_frucht}", f"{v_menge:,} Liter ({preis_pro_1k} € / 1.000L)", f"{gesamt_erloes:,.2f} €"]]
            
            st.session_state["pdf_verkauf"] = erstelle_universal_pdf("OFFIZIELLER WAREN-VERKAUFSBELEG", meta_v, posten_v, gesamt_erloes, "Gutschrift auf dem Server-Konto registriert.")
            st.success(f"Erfolgreich gebucht!")
            st.rerun()

    if "pdf_verkauf" in st.session_state:
        st.download_button("📄 Verkaufs-PDF herunterladen", data=st.session_state["pdf_verkauf"], file_name="Verkaufsabrechnung.pdf", mime="application/pdf")

# ==============================================================================
# BEREICH 4: FUHRPARK & GERÄTE
# ==============================================================================
elif bereich == "🚜 Fuhrpark & Geräte":
    st.title("🚜 Globaler Maschinen-Fuhrpark & Stundensätze")
    
    if df_sheet_masch is not None:
        suche = st.text_input("🔍 Fahrzeug oder Gerät suchen:", placeholder="z. B. Fendt, Claas...")
        df_fuhrpark = df_sheet_masch.copy()
        if suche:
            df_fuhrpark = df_fuhrpark[df_fuhrpark['geraet'].str.contains(suche, case=False, na=False)]
            
        st.dataframe(
            df_fuhrpark.rename(columns={"geraet": "Fahrzeug / Maschine", "Preis": "Stundensatz (€ / h)"}),
            use_container_width=True, hide_index=True
        )
    else:
        st.error("Preisliste konnte nicht aus Google Sheets geladen werden. Bitte Freigabe prüfen.")

# ==============================================================================
# BEREICH 5: MANUELLE FRUCHTPREISE
# ==============================================================================
elif bereich == "📈 Fruchtpreise (Manuell)":
    st.title("🌾 Fruchtpreis-Zentrale für den Server")
    
    df_preise = pd.DataFrame(list(db["preise"].items()), columns=["Fruchtart", "Preis pro 1.000L (€)"])
    st.dataframe(df_preise, use_container_width=True, hide_index=True)
    
    st.write("---")
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("🔄 Bestehenden Preis ändern")
        f_auswahl = st.selectbox("Fruchtart auswählen:", db["fruchtarten"])
        neuer_preis = st.number_input("Neuer Preis (€):", value=float(db["preise"].get(f_auswahl, 500.0)), step=10.0, key="edit_price")
        
        if st.button("Kurs live aktualisieren"):
            db["preise"][f_auswahl] = neuer_preis
            speichere_globalen_speicher(db)
            st.success(f"Preis für {f_auswahl} aktualisiert!")
            st.rerun()
            
    with col_p2:
        st.subheader("➕ Neue Mod-Frucht registrieren")
        neue_mod_frucht = st.text_input("Name der neuen Mod-Frucht:", placeholder="z. B. Dinkel, Alfalfa, Klee, Senf")
        mod_start_preis = st.number_input("Startpreis (€ pro 1.000L):", min_value=0.0, value=500.0, step=50.0)
        
        if st.button("Mod-Frucht global hinzufügen"):
            frucht_name_clean = neue_mod_frucht.strip()
            if frucht_name_clean == "":
                st.error("Bitte gib einen Namen für die Mod-Frucht ein!")
            elif frucht_name_clean in db["preise"]:
                st.error("Diese Frucht existiert bereits im Preissystem!")
            else:
                if frucht_name_clean not in db["fruchtarten"]:
                    db["fruchtarten"].append(frucht_name_clean)
                db["preise"][frucht_name_clean] = mod_start_preis
                speichere_globalen_speicher(db)
                st.success(f"'{frucht_name_clean}' wurde erfolgreich hinzugefügt und mit {mod_start_preis} € bepreist!")
                st.rerun()

# ==============================================================================
# BEREICH 6: FELDVERWALTUNG
# ==============================================================================
elif bereich == "🗺️ Feldverwaltung":
    st.title("🗺️ Globale Feldverwaltung")
    if db.get("felder"):
        df_felder = pd.DataFrame(db["felder"])
        df_felder["Besitzer Hof"] = df_felder["besitzer"].map(HOF_MAPPING)
        df_anzeige = df_felder[["id", "Besitzer Hof", "groesse", "frucht", "status", "ernte_typ"]].rename(
            columns={"id": "Feld-Nr.", "groesse": "Größe (ha)", "frucht": "Aktuelle Frucht", "status": "Status", "ernte_typ": "Ernte-Art"}
        )
        st.dataframe(df_anzeige, use_container_width=True, hide_index=True)
        
    st.write("---")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.subheader("➕ Feld registrieren")
        f_id = st.number_input("Feld-Nummer:", min_value=1, step=1, value=3)
        f_besitzer = st.selectbox("Besitzer:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        f_groesse = st.number_input("Größe in Hektar (ha):", min_value=0.1, step=0.1, value=2.0)
        
        feld_frucht_optionen = db["fruchtarten"] + ["– Eigene Mod-Frucht eingeben –"]
        f_frucht_sel = st.selectbox("Fruchtart:", feld_frucht_optionen)
        
        if f_frucht_sel == "– Eigene Mod-Frucht eingeben –":
            f_frucht = st.text_input("Name der Mod-Frucht eingeben (Feld):", placeholder="z.b. Klee, Luzerne, Vermehrungsgras")
        else:
            f_frucht = f_frucht_sel
            
        f_status = st.selectbox("Status:", ["Gepflügt", "Gesät", "Wachstum", "Erntebereit", "Abgeerntet"])
        f_typ = st.selectbox("Ernte-Art:", ["Normale Ernte", "Silage (50% LU-Rabatt)"])
        
        if st.button("Feld gespeichert"):
            if f_frucht.strip() == "":
                st.error("Bitte gib einen Namen für die Mod-Frucht ein!")
            else:
                if f_frucht.strip() not in db["fruchtarten"]:
                    db["fruchtarten"].append(f_frucht.strip())
                    if f_frucht.strip() not in db["preise"]:
                        db["preise"][f_frucht.strip()] = 500.0
                        
                db["felder"] = [x for x in db["felder"] if x["id"] != f_id]
                db["felder"].append({"id": int(f_id), "besitzer": f_besitzer, "groesse": float(f_groesse), "frucht": f_frucht, "status": f_status, "ernte_typ": f_typ})
                speichere_globalen_speicher(db)
                st.success(f"Feld {f_id} gespeichert!")
                st.rerun()
            
    with col_f2:
        st.subheader("🗑️ Feld entfernen")
        if db.get("felder"):
            f_loesch_id = st.selectbox("Feld entfernen?", [x["id"] for x in db["felder"]])
            if st.button("🔴 Löschen"):
                db["felder"] = [x for x in db["felder"] if x["id"] != f_loesch_id]
                speichere_globalen_speicher(db)
                st.success("Feld gelöscht!")
                st.rerun()

# ==============================================================================
# BEREICH 7: SÄHE- & ERNTEKALENDER
# ==============================================================================
elif bereich == "📅 Sähe- & Erntekalender":
    st.title("📅 Server Anbau- & Erntekalender (inkl. Mod-Früchte)")
    
    aktueller_m = db.get("aktueller_monat", "Januar")
    st.info(f"📅 **Aktueller Server-Monat:** {aktueller_m}")
    
    # Live-Meldungen basierend auf dem eingestellten Monat
    st.subheader("🔔 Aktuelle Feld-Meldungen für diesen Monat:")
    
    sähen_erlaubt = []
    ernten_erlaubt = []
    
    for eintrag in db.get("kalender", []):
        if "frucht" in eintrag:
            # Check Säen
            try:
                idx_start_s = MONATE_LISTE.index(eintrag["saat_von"])
                idx_end_s = MONATE_LISTE.index(eintrag["saat_bis"])
                idx_akt = MONATE_LISTE.index(aktueller_m)
                
                if idx_start_s <= idx_end_s:
                    if idx_start_s <= idx_akt <= idx_end_s: sähen_erlaubt.append(eintrag["frucht"])
                else: # Jahresübergreifend
                    if idx_akt >= idx_start_s or idx_akt <= idx_end_s: sähen_erlaubt.append(eintrag["frucht"])
            except: pass
            
            # Check Ernte
            try:
                idx_start_e = MONATE_LISTE.index(eintrag["ernte_von"])
                idx_end_e = MONATE_LISTE.index(eintrag["ernte_bis"])
                
                if idx_start_e <= idx_end_e:
                    if idx_start_e <= idx_akt <= idx_end_e: ernten_erlaubt.append(eintrag["frucht"])
                else: # Jahresübergreifend
                    if idx_akt >= idx_start_e or idx_akt <= idx_end_e: ernten_erlaubt.append(eintrag["frucht"])
            except: pass

    col_not1, col_not2 = st.columns(2)
    with col_not1:
        if sähen_erlaubt:
            st.success(f"🌱 **Jetzt SÄEN im {aktueller_m}:**\n" + "\n".join([f"* {f}" for f in sähen_erlaubt]))
        else:
            st.write(f"ℹ️ Keine spezifischen Saaten im {aktueller_m} eingetragen.")
    with col_not2:
        if ernten_erlaubt:
            st.warning(f"🚜 **Jetzt ERNTEN im {aktueller_m}:**\n" + "\n".join([f"* {f}" for f in ernten_erlaubt]))
        else:
            st.write(f"ℹ️ Keine spezifischen Ernten im {aktueller_m} eingetragen.")
            
    st.write("---")
    
    bereinigter_kalender = []
    if db.get("kalender"):
        for eintrag in db["kalender"]:
            if isinstance(eintrag, dict) and "frucht" in eintrag:
                bereinigter_kalender.append(eintrag)
                
    if bereinigter_kalender:
        df_kalender = pd.DataFrame(bereinigter_kalender)
        df_kal_anzeige = df_kalender.rename(columns={
            "frucht": "Fruchtart / Kultur",
            "saat_von": "Säen ab",
            "saat_bis": "Säen bis",
            "ernte_von": "Ernten ab",
            "ernte_bis": "Ernten bis"
        })
        st.dataframe(df_kal_anzeige, use_container_width=True, hide_index=True)
    else:
        st.info("Bisher keine gültigen Einträge im Kalender vorhanden.")
        
    st.write("---")
    col_k1, col_k2 = st.columns(2)
    
    with col_k1:
        st.subheader("➕ Eintrag hinzufügen oder überschreiben")
        k_frucht_sel = st.selectbox("Fruchtart wählen:", db["fruchtarten"] + ["– Eigene Mod-Frucht eingeben –"], key="k_frucht_sel")
        
        if k_frucht_sel == "– Eigene Mod-Frucht eingeben –":
            k_frucht = st.text_input("Name der Mod-Frucht:", placeholder="z. B. Vermehrungsgras, Klee, Dinkel")
        else:
            k_frucht = k_frucht_sel
            
        col_ks1, col_ks2 = st.columns(2)
        with col_ks1:
            k_saat_von = st.selectbox("Aussaat Start-Monat:", MONATE_LISTE, index=2)
        with col_ks2:
            k_saat_bis = st.selectbox("Aussaat End-Monat:", MONATE_LISTE, index=4)
            
        col_ke1, col_ke2 = st.columns(2)
        with col_ke1:
            k_ernte_von = st.selectbox("Ernte Start-Monat:", MONATE_LISTE, index=6)
        with col_ke2:
            k_ernte_bis = st.selectbox("Ernte End-Monat:", MONATE_LISTE, index=8)
            
        if st.button("📅 Kalendereintrag speichern"):
            if k_frucht.strip() == "":
                st.error("Bitte gib einen Namen für die Frucht ein!")
            else:
                if k_frucht.strip() not in db["fruchtarten"]:
                    db["fruchtarten"].append(k_frucht.strip())
                    if k_frucht.strip() not in db["preise"]:
                        db["preise"][k_frucht.strip()] = 500.0

                neuer_kalender = [x for x in bereinigter_kalender if x["frucht"].lower() != k_frucht.strip().lower()]
                neuer_kalender.append({
                    "frucht": k_frucht.strip(),
                    "saat_von": k_saat_von,
                    "saat_bis": k_saat_bis,
                    "ernte_von": k_ernte_von,
                    "ernte_bis": k_ernte_bis
                })
                db["kalender"] = neuer_kalender
                speichere_globalen_speicher(db)
                st.success(f"Kalenderdaten für '{k_frucht}' live synchronisiert!")
                st.rerun()
                
    with col_k2:
        st.subheader("🗑️ Fruchttyp aus Kalender löschen")
        if bereinigter_kalender:
            k_loesch_frucht = st.selectbox("Welche Frucht entfernen?", [x["frucht"] for x in bereinigter_kalender if "frucht" in x])
            if st.button("🔴 Aus Kalender löschen"):
                db["kalender"] = [x for x in bereinigter_kalender if x["frucht"] != k_loesch_frucht]
                speichere_globalen_speicher(db)
                st.success(f"'{k_loesch_frucht}' wurde aus dem Kalender gelöscht.")
                st.rerun()
        else:
            st.info("Keine löschbaren Einträge vorhanden.")

# ==============================================================================
# BEREICH 8: HOF-LAGERVERWALTUNG
# ==============================================================================
elif bereich == "📦 Hof-Lagerverwaltung":
    st.title("📦 Allgemeine Hof-Lagerbestände (Volumen-Abrechnung)")
    
    aktueller_m = db.get("aktueller_monat", "Januar")
    st.info(f"📅 **Aktueller In-Game Monat auf dem Server:** {aktueller_m}")

    # Live-Anzeige aller Lagerbestände als Tabelle (Einheitlich in Liter)
    lager_daten = []
    for h_id, h_lager in db["lager"].items():
        lager_daten.append({
            "Hof": HOF_MAPPING[h_id],
            "Silage (Silo in L)": f"{h_lager.get('Silage (Silo)', 0):,}",
            "Silage (Ballen in L)": f"{h_lager.get('Silage (Ballen)', 0):,}",
            "Paletten (Gesamtvolumen in L)": f"{h_lager.get('Paletten', 0):,}",
            "Ballen Allg. (Gesamtvolumen in L)": f"{h_lager.get('Ballen (Allg.)', 0):,}"
        })
    st.dataframe(pd.DataFrame(lager_daten), use_container_width=True, hide_index=True)
    
    # Anzeige der gärenden Silos
    if db.get("silage_gärung"):
        st.subheader("⏳ Laufende Silo-Fermentierungen (Gärungsprozesse):")
        gaer_liste = []
        for g in db["silage_gärung"]:
            idx_start = MONATE_LISTE.index(g["start_monat"])
            idx_bereit = (idx_start + g["dauer"]) % 12
            bereit_monat = MONATE_LISTE[idx_bereit]
            
            # Status ermitteln
            idx_akt = MONATE_LISTE.index(aktueller_m)
            schon_fertig = False
            if idx_start <= idx_bereit:
                if idx_start <= idx_akt < idx_bereit: schon_fertig = False
                elif idx_akt >= idx_bereit or idx_akt < idx_start: schon_fertig = True
            else:
                if idx_bereit <= idx_akt < idx_start: schon_fertig = True
                
            status_text = "🟢 FERTIG / Bereit zum Öffnen!" if schon_fertig else "⏳ Gärt noch..."
            
            gaer_liste.append({
                "Hof": HOF_MAPPING[g["hof"]],
                "Menge (L)": f"{g['menge']:,}",
                "Zugedeckt im": g["start_monat"],
                "Dauer (Monate)": g["dauer"],
                "Fertig im Monat": bereit_monat,
                "Status": status_text
            })
        st.dataframe(pd.DataFrame(gaer_liste), use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("📥 / 📤 Bestand buchen")
    
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        l_hof = st.selectbox("Welcher Hof?", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        l_typ = st.radio("Aktion:", ["➕ Einlagern", "➖ Auslagern"])
    with col_l2:
        l_gut = st.selectbox("Lager-Objekt:", ["Silage (Silo)", "Silage (Ballen)", "Paletten", "Ballen (Allg.)"])
    with col_l3:
        if l_gut == "Paletten":
            anzahl_paletten = st.number_input("Anzahl Paletten (Stück):", min_value=1, step=1, value=1)
            l_menge = anzahl_paletten * 1000
            st.caption(f"ℹ️ Entspricht bei 1.000L pro Palette: **{l_menge:,} Litern**")
        elif "Ballen" in l_gut:
            st.info("💡 Ballen haben unterschiedliche Größen! Bitte gib das Gesamtvolumen in Litern an.")
            l_menge = st.number_input("Gesamtvolumen der Ballen (Liter):", min_value=1, step=100, value=2000)
        else:
            l_menge = st.number_input("Menge in Liter (L):", min_value=1, step=1000, value=5000)
            
        dauer_gärung = 1
        if l_gut == "Silage (Silo)" and "Einlagern" in l_typ:
            dauer_gärung = st.number_input("Gärungszeit / Dauer (in In-Game Monaten):", min_value=1, max_value=12, value=2, step=1)
        
    if st.button("💾 Lagerbestand aktualisieren"):
        aktueller_bestand = db["lager"][l_hof].get(l_gut, 0)
        
        if "Auslagern" in l_typ and l_menge > aktueller_bestand:
            st.error(f"Fehler: {HOF_MAPPING[l_hof]} hat nicht genügend {l_gut} auf Lager! (Bestand: {aktueller_bestand:,} L)")
        else:
            diff = l_menge if "Einlagern" in l_typ else -l_menge
            db["lager"][l_hof][l_gut] = aktueller_bestand + diff
            
            if l_gut == "Silage (Silo)" and "Einlagern" in l_typ:
                db["silage_gärung"].append({
                    "hof": l_hof,
                    "menge": l_menge,
                    "start_monat": aktueller_m,
                    "dauer": int(dauer_gärung)
                })
                
            speichere_globalen_speicher(db)
            st.success(f"Erfolgreich gebucht! Der Bestand von {l_gut} wurde für {HOF_MAPPING[l_hof]} angepasst.")
            st.rerun()
