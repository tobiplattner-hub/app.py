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
        df_masch.columns = df_masch.columns.str.strip()
        return df_masch
    except Exception as e:
        st.sidebar.error("Fehler beim Laden der Preisliste aus Google Sheets.")
        return None

def lade_kunden_aus_sheets():
    try:
        url_kunden = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=kunden"
        df_kunden = pd.read_csv(url_kunden)
        df_kunden.columns = df_kunden.columns.str.strip()
        if 'name' in df_kunden.columns:
            return df_kunden['name'].dropna().unique().tolist()
        return None
    except Exception as e:
        # Wenn kein Tab "kunden" existiert, geben wir None zurück für den Fallback
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

def generiere_standard_daten():
    return {
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
        "verkaeufe": [],
        "manuelle_buchungen": []
    }

def lade_globalen_speicher():
    default_daten = generiere_standard_daten()
    if not os.path.exists(DB_DATEI):
        speichere_globalen_speicher(default_daten)
        return default_daten
    try:
        with open(DB_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
            for key in ["preise", "verkaeufe", "manuelle_buchungen", "auftraege", "felder", "fruchtarten"]:
                if key not in daten:
                    daten[key] = default_daten[key] if key in default_daten else []
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

# Kundenliste festlegen (entweder aus Google Sheets oder Fallback auf Höfe)
if sheet_kunden_liste:
    KUNDEN_AUSWAHL = sheet_kunden_liste
    KUNDEN_MAPPING = {k: k for k in sheet_kunden_liste}
    # Höfe hinzufügen, falls nicht vorhanden
    for k, v in HOF_MAPPING.items():
        KUNDEN_MAPPING[k] = v
else:
    KUNDEN_AUSWAHL = ["Hof 1", "Hof 2", "Hof 3"]
    KUNDEN_MAPPING = HOF_MAPPING

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

# --- DANGER ZONE / RESET ---
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
    ["📊 Dashboard & Finanzen", "💼 LU-Auftragsbuch", "🌾 Warenverkauf & Rechnungen", "🚜 Fuhrpark & Geräte", "📈 Fruchtpreise (Manuell)", "🗺️ Feldverwaltung"]
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
                st.error("Bitte gib einen Verwendungszweck an!")
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
            df_v["Käufer"] = df_v["kaeufer"].map(lambda x: HOF_MAPPING[x] if x in HOF_MAPPING else x)
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
# BEREICH 2: LU-AUFTRAGSBUCH (KUNDEN AUS GOOGLE SHEETS)
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 LU-Betriebsstunden-Abrechnung")
    
    st.subheader("📌 Neuen Lohnauftrag anlegen")
    col_a, col_b = st.columns(2)
    
    with col_a:
        # Hier werden die Kunden nun dynamisch aus dem Sheet gezogen
        a_kunde = st.selectbox("Auftraggeber (Kunde aus Google Sheet):", KUNDEN_AUSWAHL, format_func=lambda x: KUNDEN_MAPPING.get(x, x))
        a_lu = st.selectbox("Auftragnehmer (Lohnunternehmen):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        a_typ = st.selectbox("Arbeitsart:", ["Dreschen", "Häckseln", "Pflügen", "Säen", "Gülle fahren", "Ballen pressen"])
        
    with col_b:
        if df_sheet_masch is not None and 'geraet' in df_sheet_masch.columns:
            verfuegbare_maschinen = df_sheet_masch['geraet'].dropna().unique().tolist()
        else:
            verfuegbare_maschinen = ["Standard Schlepper (Kein Sheet geladen)"]
            
        a_maschine = st.selectbox("Genutztes Fahrzeug (aus Google Sheet 'preisliste'):", verfuegbare_maschinen)
        a_feld = st.number_input("Auf Feld Nummer:", min_value=1, step=1)
        
    if st.button("Auftrag live ausschreiben"):
        neuer_id = max([x["id"] for x in db["auftraege"]], default=0) + 1
        stundensatz_aus_sheet = 150.0
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
        df_offene["Kunde"] = df_offene["kunde"].map(lambda x: KUNDEN_MAPPING.get(x, x))
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
            end_preis = stunden_gefahren * auftrag["stundensatz"]
            
            feld_treffer = next((f for f in db["felder"] if f["id"] == auftrag["feld"]), None)
            if feld_treffer and feld_treffer.get("ernte_typ") == "Silage":
                end_preis *= 0.5
                
            auftrag["preis"] = end_preis
            auftrag["stunden_gefahren"] = stunden_gefahren
            auftrag["status"] = "Abgerechnet"
            
            # Nur vom Hof-Konto abbuchen, wenn der Kunde ein registrierter Ingame-Hof ist
            if auftrag["kunde"] in db["hoefe"]:
                db["hoefe"][auftrag["kunde"]]["konto"] -= end_preis
            db["hoefe"][auftrag["auftragnehmer"]]["konto"] += end_preis
            speichere_globalen_speicher(db)
            
            k_name = KUNDEN_MAPPING.get(auftrag['kunde'], auftrag['kunde'])
            meta = f"<b>Dienstleister:</b> {HOF_MAPPING[auftrag['auftragnehmer']]}<br/><b>Kunde:</b> {k_name}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}"
            posten = [[f"Lohnarbeit: {auftrag['typ']} (Feld {auftrag['feld']})", f"{stunden_gefahren:.1f} Betriebsstunden auf {auftrag['maschine']} ({auftrag['stundensatz']} €/h)", f"{end_preis:,.2f} €"]]
            
            st.session_state["pdf_temp"] = erstelle_universal_pdf("LU-BETRIEBSSTUNDEN RECHNUNG", meta, posten, end_preis, "Automatisch erfasst und über das Server-Kassenbuch beglichen.")
            st.success("Erfolgreich abgerechnet und ins Kassenbuch übertragen!")
            st.rerun()
            
        if "pdf_temp" in st.session_state:
            st.download_button("📄 PDF-Abrechnungsbeleg herunterladen", data=st.session_state["pdf_temp"], file_name="LU_Abrechnung_Stunden.pdf", mime="application/pdf")
    else:
        st.info("Hervorragend! Keine offenen Aufträge im System.")

# ==============================================================================
# BEREICH 3: WARENVERKAUF MIT FREIER MOD-FRUCHT-EINGABE
# ==============================================================================
elif bereich == "🌾 Warenverkauf & Rechnungen":
    st.title("🌾 Verkaufsrechnungen (Getreide- & Ernte-Verkauf)")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_verkaeufer = st.selectbox("Verkaufender Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        v_kaeufer = st.selectbox("Empfänger / Käufer:", ["Zentrale Verkaufsstelle (Server-Bank)", "Hof 1", "Hof 2", "Hof 3"], 
                                 format_func=lambda x: HOF_MAPPING[x] if x in HOF_MAPPING else x)
        
        # Fruchtarten-Auswahl vorbereiten mit Option für manuelle Eingabe
        frucht_optionen = db["fruchtarten"] + ["– Eigene Mod-Frucht eingeben –"]
        v_frucht_sel = st.selectbox("Verkaufte Fruchtart:", frucht_optionen)
        
        # Wenn Mod-Frucht gewählt wurde, Freitextfeld einblenden
        if v_frucht_sel == "– Eigene Mod-Frucht eingeben –":
            v_frucht = st.text_input("Name der Mod-Frucht eingeben:", placeholder="z.B. Klee, Alfalfa, Dinkel, Karotten")
            preis_pro_1k = st.number_input("Manueller Preis für diese Mod-Frucht (€ pro 1.000L):", min_value=0.0, value=500.0, step=50.0)
        else:
            v_frucht = v_frucht_sel
            preis_pro_1k = float(db["preise"].get(v_frucht, 500.0))
        
    with col_v2:
        v_menge = st.number_input("Menge in Liter (L):", min_value=0, step=1000, value=10000)
        st.info(f"💵 Abrechnungskurs: **{preis_pro_1k:,.2f} €** pro 1.000 Liter")
        
    if st.button("🚀 Verkauf abrechnen & Gutschrift erstellen"):
        if v_frucht.strip() == "":
            st.error("Bitte gib einen Namen für die Mod-Frucht ein!")
        else:
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
# BEREICH 4: FUHRPARK & GERÄTE (PREISLISTE AUS GOOGLE SHEETS)
# ==============================================================================
elif bereich == "🚜 Fuhrpark & Geräte":
    st.title("🚜 Globaler Maschinen-Fuhrpark & Stundensätze")
    st.write("Diese Liste spiegelt die aktuellen Live-Mietpreise und Lohnsätze direkt aus dem Google Sheet wider.")
    
    if df_sheet_masch is not None:
        # Suchfunktion für Maschinen
        suche = st.text_input("🔍 Fahrzeug oder Gerät suchen:", placeholder="z. B. Fendt, Claas, Drescher...")
        
        df_fuhrpark = df_sheet_masch.copy()
        if suche:
            df_fuhrpark = df_fuhrpark[df_fuhrpark['geraet'].str.contains(suche, case=False, na=False)]
            
        st.dataframe(
            df_fuhrpark.rename(columns={"geraet": "Fahrzeug / Maschine", "Preis": "Stundensatz (€ / h)"}),
            use_container_width=True, hide_index=True
        )
    else:
        st.error("Preisliste konnte nicht aus Google Sheets geladen werden. Bitte überprüfe die Internetverbindung oder das Tabellenblatt.")

# ==============================================================================
# BEREICH 5: MANUELLE FRUCHTPREISE
# ==============================================================================
elif bereich == "📈 Fruchtpreise (Manuell)":
    st.title("🌾 Fruchtpreis-Zentrale für den Server")
    st.write("Ändere hier die Standard-Kurse manuell. Die Werte gelten sofort für alle Berechnungen im Warenverkauf.")
    
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
# BEREICH 6: FELDVERWALTUNG
# ==============================================================================
elif bereich == "🗺️ Feldverwaltung":
    st.title("🗺️ Globale Feldverwaltung")
    st.write("Hier kannst du alle Felder des Servers einsehen, anpassen oder neue hinzufügen.")
    
    if db.get("felder"):
        df_felder = pd.DataFrame(db["felder"])
        df_felder["Besitzer Hof"] = df_felder["besitzer"].map(HOF_MAPPING)
        
        df_anzeige = df_felder[["id", "Besitzer Hof", "groesse", "frucht", "status", "ernte_typ"]].rename(
            columns={"id": "Feld-Nr.", "groesse": "Größe (ha)", "frucht": "Aktuelle Frucht", "status": "Status", "ernte_typ": "Ernte-Art"}
        )
        st.dataframe(df_anzeige, use_container_width=True, hide_index=True)
