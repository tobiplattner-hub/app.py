import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Für die PDF-Generierung
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
START_KONTO_HOF2 = 0
START_KONTO_HOF3 = 0

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
            "Weizen": 850, "Gerste": 780, "Raps": 1450, "Gras": 220, "Mais": 900, "Kartoffeln": 450, "Zuckerrüben": 320, "Silage (Silo)": 410, "Silage (Ballen)": 460,
            "Diesel": 500, "Dünger": 500, "Kalk": 150, "Herbizid": 150, "Saatgut": 500
        },
    
        "lager": {
            
            "Hof 1": {},
            "Hof 2": {},
            "Hof 3": {}
        },
        "silage_gärung": [],
        "hof_nachrichten": [],
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
            if "hof_nachrichten" not in daten:
                daten["hof_nachrichten"] = []
            for key in ["preise", "verkaeufe", "manuelle_buchungen", "auftraege", "felder", "fruchtarten", "kalender", "lager"]:
                if key not in daten:
                    daten[key] = default_daten[key] if key in default_daten else ([] if key != "lager" else default_daten["lager"])
            return daten
    except:
        return default_daten

def speichere_globalen_speicher(daten):
    daten["letztes_update"] = datetime.now().strftime('%H:%M:%S')
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
    
with st.sidebar.expander("👤 Spielernamen festlegen"):
    # 1. Einrückungsebene: Alles unter dem with (4 Leerzeichen)
    if "spielernamen" not in db:
        # 2. Einrückungsebene: Alles unter dem if (weitere 4 Leerzeichen = 8 total)
        db["spielernamen"] = {f"Spieler {i}": f"Spieler {i}" for i in range(1, 6)}
        speichere_globalen_speicher(db)
        
    s1 = st.text_input("Name für Spieler 1:", db["spielernamen"].get("Spieler 1", "Spieler 1"))
    s2 = st.text_input("Name für Spieler 2:", db["spielernamen"].get("Spieler 2", "Spieler 2"))
    s3 = st.text_input("Name für Spieler 3:", db["spielernamen"].get("Spieler 3", "Spieler 3"))
    s4 = st.text_input("Name für Spieler 4:", db["spielernamen"].get("Spieler 4", "Spieler 4"))
    s5 = st.text_input("Name für Spieler 5:", db["spielernamen"].get("Spieler 5", "Spieler 5"))
    
    if st.button("Spielernamen speichern"):
        # Auch hier: Wieder 8 Leerzeichen einrücken!
        db["spielernamen"] = {"Spieler 1": s1, "Spieler 2": s2, "Spieler 3": s3, "Spieler 4": s4, "Spieler 5": s5}
        speichere_globalen_speicher(db)
        st.success("Namen gespeichert!")
        st.rerun()

# ==============================================================================
# SIDEBAR & SERVER-ZENTRALE
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/tractor.png", width=80)
st.sidebar.title("⚙️ Server-Zentrale")

# --- NEU: Synchronisations-Anzeige ---
last_sync = db.get("letztes_update", "Noch keine Daten")
st.sidebar.caption(f"🔄 Letzter Sync: {last_sync}")
st.sidebar.write("---")

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

# --- HIER DEIN SIDEBAR-EXPANDER (immer sichtbar) ---
with st.sidebar.expander("🛒 Warenbestellung (PDF)"):
    st.markdown("### 🛒 Neue Bestellung")
    
    # 1. Eingabefelder
    b_hof = st.selectbox("Bestellender Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING.get(x, x), key="b_hof")
    b_gut = st.selectbox("Ware:", ["Diesel", "Saatgut", "Dünger", "Kalk", "Herbizid", "Weizen", "Gerste", "Mais"], key="b_gut")
    b_menge = st.number_input("Menge:", min_value=1, value=1000, step=500, key="b_menge")
    
    # 2. Preisberechnung
    einzelpreis = db.get("preise", {}).get(b_gut, 1.0) / 1000 
    b_gesamt = b_menge * einzelpreis

    # 3. Logik
    if st.button("📄 PDF erstellen"):
        meta_text = f"<b>Auftraggeber:</b> {HOF_MAPPING.get(b_hof, b_hof)}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}"
        posten = [[f"Bestellung: {b_gut}", f"{b_menge:,} Einheiten", f"{b_gesamt:,.2f} €"]]
        
        # Aufruf deiner zentralen Funktion
        pdf_buffer = erstelle_universal_pdf("BESTELLSCHEIN", meta_text, posten, b_gesamt, "Hinweis: Bitte bei der Zentrale abholen.")
        st.session_state["pdf_bestellung"] = pdf_buffer
        st.success("PDF bereit!")

    # 4. Download-Button (nur wenn vorhanden)
    if "pdf_bestellung" in st.session_state:
        st.download_button(
            label="📥 PDF herunterladen", 
            data=st.session_state["pdf_bestellung"], 
            file_name=f"Bestellung_{b_gut}.pdf", 
            mime="application/pdf"
        )

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
    [
        "📊 Dashboard & Finanzen", 
        "💼 LU-Auftragsbuch", 
        "🌾 Warenverkauf & Rechnungen", 
        "🚜 Fuhrpark & Geräte", 
        "📈 Preise (Feld & Hof)", 
        "🗺️ Feldverwaltung", 
        "📅 Sähe- & Erntekalender", 
        "🌱 Fruchtfolge-Planer",
        "📦 Hof-Lagerverwaltung",
        "🐄 Tier- & Futtermanagement", # NEU HINZUGEFÜGT
        "👥 Mitarbeiter- & Stundenverwaltung",
        "📋 Schwarzes Brett",
        "⛽ Betriebsmittel-Management",
        "🏭 Produktionsplaner",
    
    ]
)
if "status_ticker" not in db:
    db["status_ticker"] = "Alles läuft nach Plan."

ticker_text = db["status_ticker"]
if any(wort in ticker_text.upper() for wort in ["WICHTIG", "ACHTUNG", "DRINGEND"]):
    st.error(f"🚨 **ACHTUNG:** {ticker_text}")
else:
    st.success(f"📢 **Status:** {ticker_text}")
    # --- TICKER BEARBEITEN (PERMANENT IN SIDEBAR - OFEN) ---
st.sidebar.markdown("### 📢 Status-Ticker")
neuer_status = st.sidebar.text_input("Neuer Status:", db.get("status_ticker", "Alles läuft nach Plan."))
if st.sidebar.button("Ticker aktualisieren"):
    db["status_ticker"] = neuer_status
    speichere_globalen_speicher(db)
    st.rerun()
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
    
    st.subheader("📌 Digitales Hof-Schwarzes Brett (Informationsaustausch)")
    col_msg1, col_msg2 = st.columns([1, 2])
    
    with col_msg1:
        st.markdown("##### 📝 Neue Nachricht posten")
        msg_von = st.selectbox("Von Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x], key="msg_von")
        msg_text = st.text_area("Nachricht / Info:", placeholder="Schreibe hier wichtige Infos für die anderen Höfe rein...", key="msg_text")
        if st.button("📢 Nachricht aushängen", use_container_width=True):
            if msg_text.strip() == "":
                st.error("Bitte gib einen Nachrichtentext ein!")
            else:
                db["hof_nachrichten"].insert(0, {
                    "zeit": datetime.now().strftime('%d.%m. - %H:%M'),
                    "monat": db.get("aktueller_monat", "Januar"),
                    "hof": msg_von,
                    "text": msg_text.strip()
                })
                speichere_globalen_speicher(db)
                st.success("Nachricht gepostet!")
                st.rerun()
                
    with col_msg2:
        st.markdown("##### 📥 Aktuelle Server-Mitteilungen")
        if db.get("hof_nachrichten"):
            for i, n in enumerate(db["hof_nachrichten"][:6]):
                st.info(f"**[{n['zeit']} / In-Game: {n['monat']}] {HOF_MAPPING.get(n['hof'], n['hof'])}** schreibt:\n\n{n['text']}")
            if st.button("🗑️ Alle Nachrichten löschen"):
                db["hof_nachrichten"] = []
                speichere_globalen_speicher(db)
                st.success("Schwarzes Brett geleert!")
                st.rerun()
        else:
            st.info("Keine aktuellen Nachrichten vorhanden. Tauscht euch aus!")

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
            
            st.write("---")
    st.subheader("🕒 Aktuelle Aktivitäten der Mitarbeiter")
    
    if "stundenkonto" in db and len(db["stundenkonto"]) > 0:
        # Wir erstellen einen DataFrame aus den letzten 10 Einträgen
        df_stunden = pd.DataFrame(db["stundenkonto"])
        
        # Sortieren nach dem aktuellsten Eintrag (falls du einen Zeitstempel hättest, wäre das noch besser)
        # Hier zeigen wir einfach die letzten 10 Einträge an
        st.dataframe(
            df_stunden.tail(10)[["Mitarbeiter", "Hof", "Aufgabe", "Stunden"]], 
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Noch keine Arbeitsstunden erfasst.")

# ==============================================================================
# BEREICH 2: LU-AUFTRAGSBUCH (MIT MASCHINEN-KETTEN)
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 LU-Auftrags- & Rechnungsbuch")
    
    rechnungs_typ = st.radio("Rechnungsart:", ["Lohnauftrag (Maschinen)", "Warenlieferung (Manuell)"], horizontal=True)
    
    st.subheader("📌 Rechnung erstellen")
    col_a, col_b = st.columns(2)
    
    with col_a:
        kunde = st.selectbox("Auftraggeber:", KUNDEN_AUSWAHL, format_func=lambda x: KUNDEN_MAPPING.get(x, x))
        lieferant = st.selectbox("Verkäufer:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING.get(x, x))
    
    with col_b:
        beschreibung = st.text_input("Beschreibung (z.B. Weizen-Lieferung oder Lohnarbeit)")
        
        # Initialisierung für den Stundensatz
        stundensatz = 0.0 
        
        if rechnungs_typ == "Lohnauftrag (Maschinen)":
            # Sicherstellen, dass das Sheet existiert
            if df_sheet_masch is not None and 'geraet' in df_sheet_masch.columns and 'Preis' in df_sheet_masch.columns:
                # 1. Mapping erstellen (Name -> Preis)
                preis_mapping = dict(zip(df_sheet_masch['geraet'], df_sheet_masch['Preis']))
                verfuegbare_machines = list(preis_mapping.keys())
                
                # 2. Auswahl
                maschinen = st.multiselect("Genutzte Maschinen:", verfuegbare_machines)
                
                # 3. Summe berechnen
                if maschinen:
                    stundensatz = sum([preis_mapping.get(m, 0.0) for m in maschinen])
                    st.info(f"Berechneter Stundensatz: **{stundensatz:,.2f} €/h**")
            else:
                st.error("Maschinenliste oder Preisspalte nicht verfügbar!")
                maschinen = []
        else:
            maschinen = []

        # Falls Warenlieferung, manuelle Eingabe erlauben (optional)
        if rechnungs_typ != "Lohnauftrag (Maschinen)":
             stundensatz = st.number_input("Betrag (€):", min_value=0.0, value=0.0, step=1.0)
    # Abrechnungs-Formular
    with st.form("rechnungs_form"):
        c1, c2 = st.columns(2)
        menge = c1.number_input("Anzahl (Stunden / Menge):", min_value=0.1, step=0.1)
        preis_manuell = c2.number_input("Gesamtpreis (€):", min_value=0.0, step=0.1)
        
        submit_btn = st.form_submit_button("💰 Rechnung erstellen & PDF buchen")

    if submit_btn:
        # Berechnung
        if rechnungs_typ == "Lohnauftrag (Maschinen)":
            end_preis = menge * stundensatz
        else:
            end_preis = preis_manuell

        # Buchung im System
        if kunde in db["hoefe"]:
            db["hoefe"][kunde]["konto"] -= end_preis
        db["hoefe"][lieferant.split(" -")[0]]["konto"] += end_preis # Anpassung falls Mapping nötig
        speichere_globalen_speicher(db)

        # PDF Erstellung mit Formatierung ohne Tausenderpunkt
        meta = f"<b>Verkäufer:</b> {lieferant}<br/><b>Kunde:</b> {KUNDEN_MAPPING.get(kunde, kunde)}"
        
        # Preis-String: .2f für Dezimalstellen, replace für Komma statt Punkt, kein Tausendertrenner
        preis_str = f"{end_preis:.2f}".replace(".", ",")
        posten = [[f"Rechnung: {beschreibung}", f"{menge} Liter", f"{preis_str} €"]]
        
        pdf_buffer = erstelle_universal_pdf("RECHNUNG", meta, posten, end_preis, "Zahlung automatisch verbucht.")
        st.session_state["lu_pdf_ready"] = pdf_buffer
        st.success(f"Erfolgreich! {preis_str} € wurden zwischen den Parteien verbucht.")
        st.rerun()

    # Download Bereich
    if "lu_pdf_ready" in st.session_state:
        st.download_button("📄 PDF herunterladen", st.session_state["lu_pdf_ready"], "Rechnung.pdf", "application/pdf")
        if st.button("Rechnung verwerfen / Neue erstellen"):
            del st.session_state["lu_pdf_ready"]
            st.rerun()
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
# BEREICH 5: MANUELLE FRUCHT- & BETRIEBSMITTELPREISE
# ==============================================================================
elif bereich == "📈 Preise (Feld & Hof)":
    st.title("💰 Preis-Zentrale für Waren & Betriebsmittel")
    
    # 1. Betriebsmittel-Definition (für den Fall, dass sie noch nicht in DB sind)
    BETRIEBSMITTEL_KEYS = ["Diesel", "Saatgut", "Dünger", "Kalk", "Herbizid"]
    if "preise" not in db: db["preise"] = {}
    for bm in BETRIEBSMITTEL_KEYS:
        if bm not in db["preise"]: db["preise"][bm] = 500 # Standardwert
    
    # 2. Anzeige der Preise (Aufgeteilt)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("🌾 Verkaufsfrüchte")
        # WICHTIG: Hier wandeln wir alles mit int() in Ganzzahlen um
        frucht_daten = {k: int(v) for k, v in db["preise"].items() if k not in BETRIEBSMITTEL_KEYS}
        df = pd.DataFrame(list(frucht_daten.items()), columns=["Fruchtart", "Preis/1.000L (€)"])
        # Erzwinge den Datentyp Integer für die Spalte
        df["Preis/1.000L (€)"] = df["Preis/1.000L (€)"].apply(lambda x: f"{x:,} €")
        st.table(df)

    with col_d2:
        st.subheader("⛽ Betriebsmittel")
        bm_daten = {k: int(v) for k, v in db["preise"].items() if k in BETRIEBSMITTEL_KEYS}
        df_bm = pd.DataFrame(list(bm_daten.items()), columns=["Betriebsmittel", "Preis/1.000L (€)"])
        # Erzwinge den Datentyp Integer
        df_bm["Preis/1.000L (€)"] = df_bm["Preis/1.000L (€)"].apply(lambda x: f"{x:,} €")
        st.table(df_bm)
    st.write("---")
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.subheader("🔄 Bestehenden Preis ändern")
        # Alle Preise aus der DB als Auswahlmöglichkeit
        f_auswahl = st.selectbox("Artikel auswählen:", list(db["preise"].keys()))
        neuer_preis = st.number_input("Neuer Preis (€):", value=int(db["preise"].get(f_auswahl, 500)), step=1)
        
        if st.button("Kurs aktualisieren"):
            db["preise"][f_auswahl] = neuer_preis
            speichere_globalen_speicher(db)
            st.success(f"Preis für {f_auswahl} aktualisiert!")
            st.rerun()
            
    with col_p2:
        st.subheader("➕ Neue Mod-Frucht")
        neue_mod_frucht = st.text_input("Name der Mod-Frucht:")
        mod_start_preis = st.number_input("Startpreis pro 1.000L:", min_value=0, value=500, step=50)
        
        if st.button("Mod-Frucht hinzufügen"):
            frucht_name_clean = neue_mod_frucht.strip()
            if frucht_name_clean == "" or frucht_name_clean in BETRIEBSMITTEL_KEYS:
                st.error("Ungültiger Name oder reserviertes Wort!")
            elif frucht_name_clean in db["preise"]:
                st.error("Existiert bereits!")
            else:
                db["preise"][frucht_name_clean] = mod_start_preis
                if "fruchtarten" in db and frucht_name_clean not in db["fruchtarten"]:
                    db["fruchtarten"].append(frucht_name_clean)
                speichere_globalen_speicher(db)
                st.success(f"'{frucht_name_clean}' hinzugefügt!")
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
    
    st.subheader("🔔 Aktuelle Feld-Meldungen für diesen Monat:")
    
    sähen_erlaubt = []
    ernten_erlaubt = []
    
    for eintrag in db.get("kalender", []):
        if "frucht" in eintrag:
            try:
                idx_start_s = MONATE_LISTE.index(eintrag["saat_von"])
                idx_end_s = MONATE_LISTE.index(eintrag["saat_bis"])
                idx_akt = MONATE_LISTE.index(aktueller_m)
                
                if idx_start_s <= idx_end_s:
                    if idx_start_s <= idx_akt <= idx_end_s: sähen_erlaubt.append(eintrag["frucht"])
                else:
                    if idx_akt >= idx_start_s or idx_akt <= idx_end_s: sähen_erlaubt.append(eintrag["frucht"])
            except: pass
            
            try:
                idx_start_e = MONATE_LISTE.index(eintrag["ernte_von"])
                idx_end_e = MONATE_LISTE.index(eintrag["ernte_bis"])
                
                if idx_start_e <= idx_end_e:
                    if idx_start_e <= idx_akt <= idx_end_e: ernten_erlaubt.append(eintrag["frucht"])
                else:
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
elif bereich == "🌱 Fruchtfolge-Planer":
    st.title("🌱 Fruchtfolge-Planer")
    
    # 1. Globale Definitionen
    ERNTEMAP = {"Weizen": "Aug", "Wintergerste": "Jul", "Raps": "Jul", "Mais": "Okt", "Roggen": "Aug", "Sonnenblumen": "Sep"}
    
    if "felder" not in db or not db["felder"]:
        st.error("Keine Felder gefunden. Bitte erst in der Feldverwaltung Felder anlegen.")
    else:
        for feld in db["felder"]:
            if "folge" not in feld: feld["folge"] = ["Weizen"]
            if "ertrag_pro_ha" not in feld: feld["ertrag_pro_ha"] = 5000
            
            feld_name = feld.get("id", "Unbekannt")
            besitzer_id = feld.get("besitzer", "hof1") # Der Key für den Besitzer
            hof_name = HOF_MAPPING.get(besitzer_id, "Unbekannter Hof")
            
            aktuelle_frucht = feld["folge"][0]
            ernte_monat = ERNTEMAP.get(aktuelle_frucht, "Aug")
            akt_m = db.get("aktueller_monat", "Jan")
            
            with st.expander(f"📍 {feld_name} | 🌾 {aktuelle_frucht} ({hof_name})"):
                c_a, c_b = st.columns(2)
                with c_a:
                    folge_str = st.text_input("Fruchtfolge:", value=", ".join(feld["folge"]), key=f"seq_{feld_name}")
                with c_b:
                    neuer_ertrag = st.number_input(f"Ertrag (Liter) für {aktuelle_frucht}:", 
                                                  value=feld.get("ertrag_pro_ha", 5000), 
                                                  key=f"y_{feld_name}")
                
                st.write(f"Geplanter Erntemonat: **{ernte_monat}** | Besitzer: **{hof_name}**")
                
                c1, c2, c3 = st.columns(3)
                
                if c1.button("💾 Speichern", key=f"save_{feld_name}"):
                    feld["folge"] = [x.strip() for x in folge_str.split(",")]
                    feld["ertrag_pro_ha"] = neuer_ertrag
                    speichere_globalen_speicher(db)
                    st.rerun()
                
                if c2.button("🔄 Nächste", key=f"rot_{feld_name}"):
                    if len(feld["folge"]) > 1:
                        feld["folge"] = feld["folge"][1:] + [feld["folge"][0]]
                        speichere_globalen_speicher(db)
                        st.rerun()
                
                if c3.button("🚀 Ernte buchen", key=f"h_{feld_name}"):
                    # Dynamische Ziel-Hof Zuweisung
                    if "lager" not in db: db["lager"] = {}
                    if besitzer_id not in db["lager"]: db["lager"][besitzer_id] = {}
                    
                    # Lager-Eintrag auf den Besitzer-Key (z.B. "hof1")
                    db["lager"][besitzer_id][aktuelle_frucht] = db["lager"][besitzer_id].get(aktuelle_frucht, 0) + neuer_ertrag
                    
                    st.balloons()
                    st.success(f"Ernte erfolgreich in {hof_name} gebucht!")
                    speichere_globalen_speicher(db)
                    st.rerun()
# ==============================================================================
# BEREICH 8: HOF-LAGERVERWALTUNG (VOLLSTÄNDIG & BEREINIGT)
# ==============================================================================
elif bereich == "📦 Hof-Lagerverwaltung":
    st.title("📦 Hof-Lagerverwaltung & Silomanagement")
    
    aktueller_m = db.get("aktueller_monat", "Januar")
    st.markdown(f"📅 **Aktueller Server-Monat:** `{aktueller_m}`")
    
    # 1. Lagerbestände Übersicht
    st.subheader("📋 Aktuelle Lagerbestände")
    
    alle_gueter = set()
    for h_id in ["Hof 1", "Hof 2", "Hof 3"]:
        if h_id in db.get("lager", {}):
            alle_gueter.update(db["lager"][h_id].keys())
    
    liste_gueter = sorted(list(alle_gueter))

    if liste_gueter:
        lager_daten = []
        for h_id in ["Hof 1", "Hof 2", "Hof 3"]:
            zeile = {"Hof / Betrieb": HOF_MAPPING.get(h_id, h_id)}
            for gut in liste_gueter:
                zeile[f"{gut} (L)"] = db["lager"].get(h_id, {}).get(gut, 0)
            lager_daten.append(zeile)
            
        st.data_editor(
            pd.DataFrame(lager_daten), 
            use_container_width=True, 
            hide_index=True, 
            disabled=True
        )
    else:
        st.info("Das Lager ist aktuell leer.")

    
 # --------------------------------------------------------------------------
    # 3. Integrierte Buchungsmaske
    # --------------------------------------------------------------------------
    st.write("---")
    st.subheader("⚙️ Lagerbewegung buchen")
    
    with st.expander("👉 Neuen Eintrag oder Entnahme erfassen", expanded=True):
        col_l1, col_l2 = st.columns(2)
        
        with col_l1:
            l_hof = st.selectbox("Betroffener Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
            l_typ = st.radio("Aktionsart:", ["➕ Einlagern (Bestand erhöhen)", "➖ Auslagern (Bestand reduzieren)"], horizontal=True)
            l_kat = st.selectbox("Kategorie / Zustand:", ["Loses Material / Frucht", "Paletten-Ware", "Ballen-Ware", "Silo-Silage (mit Gärung)"])
            
            platzhalter_text = "z. B. Getreide, Trauben, Kalk, Diesel, Häckselgut"
            if "Paletten" in l_kat:
                platzhalter_text = "z. B. Tomaten-Paletten, Saatgut-Paletten, Salat-Paletten"
            elif "Ballen" in l_kat:
                platzhalter_text = "z. B. Stroh-Ballen, Silage-Ballen, Heu-Ballen"
            elif "Silo" in l_kat:
                platzhalter_text = "Silage (Silo)"
                
            l_name_eingabe = st.text_input("Genaue Bezeichnung / Name der Ware:", placeholder=platzhalter_text, value="Silage (Silo)" if "Silo" in l_kat else "")
            
        with col_l2:
            if "Paletten" in l_kat:
                l_modus = st.radio("Eingabe als:", ["Stückzahl (Paletten)", "Direkt in Liter"], horizontal=True)
                if l_modus == "Stückzahl (Paletten)":
                    anzahl_paletten = st.number_input("Anzahl Paletten (Stück):", min_value=1, step=1, value=1)
                    finale_liter = anzahl_paletten * 1000
                    st.info(f"Umgerechnetes Gesamtvolumen (1.000L pro Palette): **{finale_liter:,} Liter**")
                else:
                    finale_liter = st.number_input("Volumen in Liter (L):", min_value=1, step=100, value=1000)
            
            elif "Ballen" in l_kat:
                l_modus_ballen = st.radio("Eingabe als:", ["Stückzahl (Ballen)", "Direkt in Liter"], horizontal=True)
                if l_modus_ballen == "Stückzahl (Ballen)":
                    anzahl_ballen = st.number_input("Anzahl Ballen (Stück):", min_value=1, step=1, value=1)
                    finale_liter = anzahl_ballen * 5000
                    st.info(f"Umgerechnetes Gesamtvolumen (5.000L pro Großballen): **{finale_liter:,} Liter**")
                else:
                    finale_liter = st.number_input("Volumen in Liter (L):", min_value=1, step=1000, value=5000)
            
            else:
                finale_liter = st.number_input("Volumen in Liter (L):", min_value=1, step=1000, value=5000)
                
            dauer_gärung = 2
            if "Silo" in l_kat and "Einlagern" in l_typ:
                st.write(" ")
                dauer_gärung = st.number_input("Fermentationsdauer (In-Game Monate):", min_value=1, max_value=12, value=2, step=1)
        
        st.write(" ")
        if st.button("💾 Buchung abschließen und live synchronisieren", use_container_width=True):
            waren_name_clean = l_name_eingabe.strip()
            
            if waren_name_clean == "":
                st.error("Bitte gib eine Bezeichnung für das Gut ein!")
            else:
                aktueller_bestand = db["lager"].get(l_hof, {}).get(waren_name_clean, 0)
                
                if "Auslagern" in l_typ and finale_liter > aktueller_bestand:
                    st.error(f"Fehler: {HOF_MAPPING[l_hof]} hat nicht genügend '{waren_name_clean}' auf Lager! Verfügbar: {aktueller_bestand:,} L – Gewünscht: {finale_liter:,} L.")
                else:
                    diff = finale_liter if "Einlagern" in l_typ else -finale_liter
                    
                    if l_hof not in db["lager"]:
                        db["lager"][l_hof] = {}
                        
                    db["lager"][l_hof][waren_name_clean] = aktueller_bestand + diff
                    
                    if db["lager"][l_hof][waren_name_clean] <= 0:
                        del db["lager"][l_hof][waren_name_clean]
                    
                    if "Silo" in l_kat and "Einlagern" in l_typ:
                        db["silage_gärung"].append({
                            "hof": l_hof,
                            "menge": finale_liter,
                            "start_monat": aktueller_m,
                            "dauer": int(dauer_gärung)
                        })
                        
                    speichere_globalen_speicher(db)
                    st.success(f"Bestand erfolgreich aktualisiert! {finale_liter:,} L '{waren_name_clean}' für {HOF_MAPPING[l_hof]} verbucht.")
                    st.rerun()
 # ==============================================================================
# BEREICH: TIER- & FUTTERMANAGEMENT (VOLLSTÄNDIG)
# ==============================================================================
elif bereich == "🐄 Tier- & Futtermanagement":
    st.title("🐄 Tier- & Futtermanagement (PAMM)")
    
    # 1. Datenbasis gemäß Kalkulation
    tier_profile = {
        "Milchkühe (18M)": {"verbrauch": 350, "heu": 0.5, "silage": 0.4, "stroh": 0.1, "typ": "TMR"},
        "Fleischrinder (18M)": {"verbrauch": 550, "heu": 0.5, "silage": 0.4, "stroh": 0.1, "typ": "TMR"},
        "Ziegen": {"verbrauch": 200, "gras_heu": 0.8, "mineral": 0.2, "typ": "GRAS"},
        "Schweine": {"verbrauch": 250, "mais": 0.5, "weizen": 0.3, "raps": 0.2, "typ": "Mix"},
        "Hühner": {"verbrauch": 80, "weizen": 1.0, "typ": "Getreide"}
    }

    # 2. Tierbestand pro Hof
    st.subheader("🏠 Tierbestand (Stall-Management)")
    if "tierbestand" not in db: 
        db["tierbestand"] = {"Hof 1": 0, "Hof 2": 0, "Hof 3": 0}

    cols = st.columns(3)
    hof_tiere = {}
    for i, h_id in enumerate(["Hof 1", "Hof 2", "Hof 3"]):
        with cols[i]:
            label = HOF_MAPPING.get(h_id, h_id)
            hof_tiere[h_id] = st.number_input(f"Anzahl Tiere ({label}):", min_value=0, value=db["tierbestand"].get(h_id, 0), key=f"tiere_{h_id}")

    if st.button("Tierbestand auf Server speichern"):
        db["tierbestand"] = hof_tiere
        speichere_globalen_speicher(db)
        st.success("Bestände global aktualisiert!")

    st.write("---")
    
    # 3. Futterbedarfs-Rechner
    st.subheader("📊 Futterbedarfs-Rechner")
    col_cfg1, col_cfg2 = st.columns([2, 1])
    
    with col_cfg1:
        tier_typ = st.selectbox("Tierart wählen:", list(tier_profile.keys()))
        monate = st.slider("Planungszeitraum (Monate):", 1, 37, 12)
        
        # Manuelle Bedarfsanpassung
        manuell_aktiv = st.checkbox("Bedarf pro Tier/Monat manuell anpassen")
        if manuell_aktiv:
            verbrauch_pro_tier = st.number_input("Liter pro Tier/Monat (Manuell):", min_value=1.0, value=float(tier_profile[tier_typ]["verbrauch"]))
        else:
            verbrauch_pro_tier = tier_profile[tier_typ]["verbrauch"]
            
    with col_cfg2:
        reserve = st.slider("Reserve-Puffer (%)", 0, 20, 5) / 100
        st.write(f"Aktueller Wert: **{verbrauch_pro_tier} L** pro Tier/Monat")

    # Berechnung
    p = tier_profile[tier_typ]
    gesamt_tiere = sum(hof_tiere.values())
    
    bedarf_total = gesamt_tiere * verbrauch_pro_tier * monate
    bedarf_mit_reserve = bedarf_total * (1 + reserve)
    
    st.info(f"### Gesamtbedarf ({gesamt_tiere} Tiere, {monate} Mon.): {bedarf_mit_reserve:,.0f} L (inkl. {reserve*100:.0f}% Reserve)")
    
    # Anzeige der Komponenten (TMR/Mix spezifisch)
    if p["typ"] == "TMR":
        st.subheader("🌾 TMR-Zusammensetzung (50/40/10)")
        c1, c2, c3 = st.columns(3)
        c1.metric("Heu (50%)", f"{bedarf_mit_reserve * p['heu']:,.0f} L")
        c2.metric("Silage (25%)", f"{bedarf_mit_reserve * p['silage']:,.0f} L")
        c3.metric("Stroh (25%)", f"{bedarf_mit_reserve * p['stroh']:,.0f} L")
    elif p["typ"] == "Mix":
        st.subheader("🌾 Mix-Zusammensetzung")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mais (50%)", f"{bedarf_mit_reserve * p['mais']:,.0f} L")
        c2.metric("Weizen (30%)", f"{bedarf_mit_reserve * p['weizen']:,.0f} L")
        c3.metric("Raps (20%)", f"{bedarf_mit_reserve * p['raps']:,.0f} L")

    # 4. Chart Bedarfsentwicklung
    st.markdown("📈 **Bedarfsentwicklung (Gesamt & Komponenten)**")
    monats_daten = []
    for m in range(1, monate + 1):
        m_bedarf = gesamt_tiere * verbrauch_pro_tier * m * (1 + reserve)
        data = {"Monat": m, "Gesamt": m_bedarf}
        if p["typ"] == "TMR":
            data.update({"Heu": m_bedarf * p['heu'], "Silage": m_bedarf * p['silage'], "Stroh": m_bedarf * p['stroh']})
        elif p["typ"] == "Mix":
            data.update({"Mais": m_bedarf * p['mais'], "Weizen": m_bedarf * p['weizen'], "Raps": m_bedarf * p['raps']})
        monats_daten.append(data)

    st.line_chart(pd.DataFrame(monats_daten).set_index("Monat"))

    # --------------------------------------------------------------------------
    # 2. Gärungsprozesse Übersicht (Grafisch aufgewertet)
    # --------------------------------------------------------------------------
    if db.get("silage_gärung"):
        st.write("---")
        st.subheader("⏳ Laufende Silo-Fermentierungen")
        
        gaer_liste = []
        for g in db["silage_gärung"]:
            idx_start = MONATE_LISTE.index(g["start_monat"])
            idx_bereit = (idx_start + g["dauer"]) % 12
            bereit_monat = MONATE_LISTE[idx_bereit]
            
            idx_akt = MONATE_LISTE.index(aktueller_m)
            schon_fertig = False
            if idx_start <= idx_bereit:
                if idx_start <= idx_akt < idx_bereit: schon_fertig = False
                elif idx_akt >= idx_bereit or idx_akt < idx_start: schon_fertig = True
            else:
                if idx_bereit <= idx_akt < idx_start: schon_fertig = True
                
            status_text = "🟢 BEREIT ZUM ÖFFNEN" if schon_fertig else "⏳ Gärt noch..."
            
            gaer_liste.append({
                "Hof": HOF_MAPPING[g["hof"]],
                "Menge": g['menge'],
                "Eingelagert in": g["start_monat"],
                "Dauer": f"{g['dauer']} Mon.",
                "Fertig im": bereit_monat,
                "Status": status_text
            })
            
        df_gaerung = pd.DataFrame(gaer_liste)
        
        st.data_editor(
            df_gaerung,
            use_container_width=True,
            hide_index=True,
            disabled=True,
            column_config={
                "Hof": st.column_config.TextColumn("🏠 Hof"),
                "Menge": st.column_config.NumberColumn("Volumen", format="%d L"),
                "Status": st.column_config.TextColumn("Status", help="Gärstatus des Silos")
            })
        
elif bereich == "👥 Mitarbeiter- & Stundenverwaltung":
    st.title("👥 Mitarbeiter- & Stundenverwaltung")
    
    # Datenbank-Check
    if "stundenkonto" not in db: db["stundenkonto"] = []
    if "spielernamen" not in db: # Fallback falls nicht gesetzt
        db["spielernamen"] = {f"Spieler {i}": f"Spieler {i}" for i in range(1, 6)}

    # Mapping für die Selectbox: {"Spieler 1": "Max", "Spieler 2": "Erika"...}
    spieler_map = db["spielernamen"]
    hof_mapping = {h_id: h_data["name"] for h_id, h_data in db["hoefe"].items()}
    
    with st.form("stunden_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        # Anzeige: Hier nutzen wir die Namen aus der DB, speichern aber den Key "Spieler X"
        ma_id = col1.selectbox("Mitarbeiter:", options=list(spieler_map.keys()), format_func=lambda x: spieler_map[x])
        hof_id = col2.selectbox("Hof zuweisen:", options=list(hof_mapping.keys()), format_func=lambda x: hof_mapping[x])
        aufgabe = col3.text_input("Aufgabe:")
        std = col4.number_input("Stunden:", min_value=0.5, step=0.5)
        
        if st.form_submit_button("Arbeitsnachweis speichern"):
            db["stundenkonto"].append({
                "Mitarbeiter": spieler_map[ma_id], # SPEICHERT DEN ECHTEN NAMEN
                "Hof": hof_mapping[hof_id],
                "Aufgabe": aufgabe,
                "Stunden": std
            })
            speichere_globalen_speicher(db)
            st.success("Gespeichert!")
            st.rerun()

    # Übersicht
    st.subheader("📊 Stundenübersicht")
    if db["stundenkonto"]:
        df = pd.DataFrame(db["stundenkonto"])
        st.dataframe(df, use_container_width=True)

elif bereich == "📋 Schwarzes Brett":
    st.title("📋 Schwarzes Brett")
    
    # 1. Sicherstellen, dass das Brett existiert
    if "aufgaben_brett" not in db:
        db["aufgaben_brett"] = []
    
    # Spielerliste für die Auswahl
    spieler_map = db.get("spielernamen", {f"Spieler {i}": f"Spieler {i}" for i in range(1, 6)})
    spieler_optionen = list(spieler_map.values())
    
    # 2. Formular: Wer schreibt an wen?
    with st.form("neue_nachricht", clear_on_submit=True):
        col_von, col_an = st.columns(2)
        absender = col_von.selectbox("Von:", spieler_optionen)
        empfaenger = col_an.selectbox("An:", ["Alle"] + spieler_optionen)
        nachricht_text = st.text_input("Nachricht:")
        
        if st.form_submit_button("Nachricht veröffentlichen"):
            if nachricht_text:
                db["aufgaben_brett"].append({
                    "von": absender,
                    "an": empfaenger,
                    "text": nachricht_text
                })
                speichere_globalen_speicher(db)
                st.rerun()
    
    st.write("---")
    
    # 3. Nachrichten anzeigen
    if db["aufgaben_brett"]:
        for i, eintrag in enumerate(db["aufgaben_brett"]):
            # Schöne Darstellung
            titel = f"**{eintrag['von']}** an **{eintrag['an']}**:"
            col1, col2 = st.columns([0.85, 0.15])
            
            col1.info(f"{titel} {eintrag['text']}")
            
            if col2.button("✅", key=f"del_{i}"):
                db["aufgaben_brett"].pop(i)
                speichere_globalen_speicher(db)
                st.rerun()
    else:
        st.info("Aktuell keine Nachrichten auf dem Brett.")
        
# ==============================================================================
# BEREICH: BETRIEBSMITTEL-MANAGEMENT (DYNAMISCH & PREIS-GEKOPPELT)
# ==============================================================================
elif bereich == "⛽ Betriebsmittel-Management":
    st.title("⛽ Betriebsmittel-Management")
    
    # 1. Daten-Initialisierung (inkl. Herbizid)
    BETRIEBSMITTEL_LISTE = ["Diesel", "Saatgut", "Dünger", "Kalk", "Herbizid"]
    
    if "betriebsmittel" not in db:
        db["betriebsmittel"] = {h_id: {bm: 0 for bm in BETRIEBSMITTEL_LISTE} for h_id in ["Hof 1", "Hof 2", "Hof 3"]}
    
    # Preise werden direkt aus der Datenbank geholt (synchron zu deiner Preis-Zentrale)
    # Falls der Schlüssel noch fehlt, nutzen wir Standardwerte
    PREISE = {bm: db["preise"].get(bm, 1.0) for bm in BETRIEBSMITTEL_LISTE}
    
    # 2. Übersicht mit dynamischen Hofnamen
    st.subheader("📋 Aktuelle Vorräte")
    
    anzeige_daten = {}
    for h_id, werte in db["betriebsmittel"].items():
        hof_name = HOF_MAPPING.get(h_id, h_id)
        # Nur die Betriebsmittel anzeigen, die wir definiert haben
        anzeige_daten[hof_name] = {k: v for k, v in werte.items() if k in BETRIEBSMITTEL_LISTE}
        
    df_bm = pd.DataFrame(anzeige_daten).T
    st.table(df_bm)

    # 3. Einkauf
    st.subheader("🛍️ Betriebsmittel einkaufen")
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        e_hof = st.selectbox("Hof für Einkauf:", list(HOF_MAPPING.keys()), format_func=lambda x: HOF_MAPPING[x])
        e_gut = st.selectbox("Betriebsmittel:", BETRIEBSMITTEL_LISTE)
    with col_e2:
        e_menge = st.number_input("Menge (Liter/kg):", min_value=1, value=1000)
        kosten = int(e_menge * (PREISE[e_gut] / 1000))
        st.write(f"Kosten: **{int(kosten):,} €**")
    
    if st.button("🛒 Jetzt kaufen & vom Hofkonto abbuchen"):
        if db["hoefe"][e_hof]["konto"] >= kosten:
            db["hoefe"][e_hof]["konto"] -= kosten
            db["betriebsmittel"][e_hof][e_gut] = db["betriebsmittel"][e_hof].get(e_gut, 0) + e_menge
            speichere_globalen_speicher(db)
            st.success(f"Einkauf erfolgreich! {e_menge} Einheiten {e_gut} für {HOF_MAPPING[e_hof]} verbucht.")
            st.rerun()
        else:
            st.error("Nicht genügend Geld auf dem Hofkonto!")

    st.write("---")

    # 4. Manueller Verbrauch
    st.subheader("📉 Materialverbrauch nach Feldarbeit buchen")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_hof = st.selectbox("Hof für Verbrauch:", list(HOF_MAPPING.keys()), format_func=lambda x: HOF_MAPPING[x], key="v_hof")
        v_gut = st.selectbox("Verbrauchtes Material:", BETRIEBSMITTEL_LISTE, key="v_gut")
    with col_v2:
        v_menge = st.number_input("Verbrauchte Menge (L/kg):", min_value=1, value=100, key="v_menge")
    
    if st.button("📉 Verbrauch verbuchen"):
        if db["betriebsmittel"][v_hof].get(v_gut, 0) >= v_menge:
            db["betriebsmittel"][v_hof][v_gut] -= v_menge
            speichere_globalen_speicher(db)
            st.success(f"{v_menge} Einheiten {v_gut} wurden von {HOF_MAPPING[v_hof]} abgebucht.")
            st.rerun()
        else:
            st.error(f"Fehler: Nicht genug {v_gut} auf Lager!")

# ==============================================================================
# BEREICH 9: PRODUKTIONSPLANER
# ==============================================================================

elif bereich == "🏭 Produktionsplaner":
    st.title("🏭 Produktionsplaner")

    # 1. Initialisierung mit Standardwerten (verhindert KeyErrors)
    if "produktionen" not in db:
        db["produktionen"] = {
            "Mühle - Mehl": {"input": "Weizen", "in_menge": 9, "output": "Mehl", "out_menge": 15, "zyklus": 1440}
        }

    # 2. Rezept-Verwaltung
    st.subheader("🛠️ Rezepte verwalten")
    rezept_namen = list(db["produktionen"].keys())
    rezept_wahl = st.selectbox("Rezept wählen:", ["➕ Neues Rezept erstellen"] + rezept_namen)

    if rezept_wahl == "➕ Neues Rezept erstellen":
        neuer_name = st.text_input("Name des neuen Rezepts:")
        if st.button("Erstellen"):
            if neuer_name:
                db["produktionen"][neuer_name] = {"input": "Milch", "in_menge": 1, "output": "Produkt", "out_menge": 1, "zyklus": 1440}
                speichere_globalen_speicher(db)
                st.rerun()
    else:
        # Bestehendes Rezept bearbeiten
        with st.expander(f"⚙️ Bearbeiten: {rezept_wahl}"):
            p = db["produktionen"][rezept_wahl]
            
            # Sicherer Zugriff mit .get() für alte und neue Schlüssel
            n_input = st.text_input("Input-Ware:", value=p.get('input', p.get('input_gut', '')))
            n_in_m = st.number_input("Menge Input:", value=p.get('in_menge', p.get('input_menge', 1)))
            n_zyk = st.number_input("Zyklen pro Monat:", value=p.get('zyklus', p.get('zyklus_faktor', 1440)))
            
            n_output = st.text_input("Output-Ware:", value=p.get('output', p.get('output_gut', '')))
            n_out_m = st.number_input("Menge Output:", value=p.get('out_menge', p.get('output_menge', 1)))
            
            c_save, c_del = st.columns(2)
            if c_save.button("Speichern"):
                db["produktionen"][rezept_wahl] = {
                    "input": n_input, "in_menge": n_in_m, 
                    "output": n_output, "out_menge": n_out_m, 
                    "zyklus": n_zyk
                }
                speichere_globalen_speicher(db)
                st.rerun()
            if c_del.button("🗑️ Löschen"):
                del db["produktionen"][rezept_wahl]
                speichere_globalen_speicher(db)
                st.rerun()

    st.write("---")

    # 3. Produktion (Rechner & Buchung)
    st.subheader("🚀 Produktion ausführen")
    aktive_rezepte = st.multiselect("Rezepte aktivieren:", list(db["produktionen"].keys()))
    monate = st.number_input("Monate planen:", min_value=1, value=1)
    
    modus = st.radio("Modus:", ["Nur Berechnen (Simulation)", "Im Lager verbuchen"], horizontal=True)
    prod_hof = st.selectbox("Betroffener Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])

    if aktive_rezepte:
        st.write("### Kalkulation:")
        for r_name in aktive_rezepte:
            p = db["produktionen"][r_name]
            # Sicherer Zugriff auch hier
            inp = p.get('input', p.get('input_gut', ''))
            in_m = p.get('in_menge', p.get('input_menge', 0))
            outp = p.get('output', p.get('output_gut', ''))
            out_m = p.get('out_menge', p.get('output_menge', 0))
            zyk = p.get('zyklus', p.get('zyklus_faktor', 1440))
            
            bedarf = in_m * zyk * monate
            st.write(f"**{r_name}:** {bedarf:,} {inp} → {out_m * zyk * monate:,} {outp}")
            
            if modus == "Im Lager verbuchen":
                vorrat = db.get("lager", {}).get(prod_hof, {}).get(inp, 0)
                st.caption(f"Aktueller Bestand: {vorrat:,} {inp} | Status: {'✅' if vorrat >= bedarf else '❌ Zu wenig'}")

    # 4. Buchungs-Logik
    if st.button("🚀 Aktion ausführen"):
        if modus == "Nur Berechnen (Simulation)":
            st.success("Simulation erfolgreich kalkuliert!")
        else:
            erfolgreich = True
            # Erst alles prüfen
            for r_name in aktive_rezepte:
                p = db["produktionen"][r_name]
                inp = p.get('input', p.get('input_gut', ''))
                bedarf = p.get('in_menge', p.get('input_menge', 0)) * p.get('zyklus', p.get('zyklus_faktor', 1440)) * monate
                vorrat = db.get("lager", {}).get(prod_hof, {}).get(inp, 0)
                
                if vorrat < bedarf:
                    st.error(f"Nicht genug {inp} für {r_name}!")
                    erfolgreich = False
                    break
            
            # Wenn Prüfung bestanden, abziehen und hinzufügen
            if erfolgreich:
                for r_name in aktive_rezepte:
                    p = db["produktionen"][r_name]
                    inp = p.get('input', p.get('input_gut', ''))
                    outp = p.get('output', p.get('output_gut', ''))
                    
                    input_total = p.get('in_menge', p.get('input_menge', 0)) * p.get('zyklus', p.get('zyklus_faktor', 1440)) * monate
                    output_total = p.get('out_menge', p.get('output_menge', 0)) * p.get('zyklus', p.get('zyklus_faktor', 1440)) * monate
                    
                    db["lager"][prod_hof][inp] -= input_total
                    db["lager"][prod_hof][outp] = db["lager"][prod_hof].get(outp, 0) + output_total
                
                speichere_globalen_speicher(db)
                st.success("Produktion wurde verbucht!")
                st.rerun()

# ==============================================================================
# SIDEBAR-BESTELLUNGEN (PDF-Generator)
# ==============================================================================
with st.sidebar.expander("🛒 Warenbestellung (PDF)", expanded=True):
    st.markdown("### 🛒 Neue Bestellung")
    
    # 1. Hof-Auswahl
    b_hof = st.selectbox("Bestellender Hof:", ["Hof 1", "Hof 2", "Hof 3"], 
                         format_func=lambda x: HOF_MAPPING.get(x, x), key="b_hof_select_pro")
    
    # 2. Session State für manuelle Waren-Liste initialisieren
    if "manuelle_waren_liste" not in st.session_state:
        st.session_state["manuelle_waren_liste"] = []

    # 3. Ware hinzufügen
    neue_ware = st.text_input("Ware hinzufügen (Name):", key="neue_ware_input")
    if st.button("➕ Hinzufügen"):
        if neue_ware and neue_ware not in st.session_state["manuelle_waren_liste"]:
            st.session_state["manuelle_waren_liste"].append(neue_ware)
    
    # 4. Liste anzeigen und Mengen definieren
    bestell_daten = []
    if st.session_state["manuelle_waren_liste"]:
        st.write("Aktuelle Liste:")
        for ware in st.session_state["manuelle_waren_liste"]:
            c1, c2 = st.columns([2, 1])
            m = c1.number_input(f"Menge {ware} (L):", min_value=1, value=1000, step=500, key=f"qty_{ware}")
            if c2.button("🗑️", key=f"del_{ware}"):
                st.session_state["manuelle_waren_liste"].remove(ware)
                st.rerun()
            bestell_daten.append([ware, f"{m:,} Liter", "---"]) # Preis entfernt

    # 5. PDF Erstellung
    if st.button("📄 PDF generieren"):
        if not bestell_daten:
            st.error("Liste ist leer!")
        else:
            meta_text = f"<b>Auftraggeber:</b> {HOF_MAPPING.get(b_hof, b_hof)}<br/><b>Datum:</b> {datetime.now().strftime('%d.%m.%Y')}"
            # PDF ohne Gesamtsumme (0.0 übergeben)
            pdf_buffer = erstelle_universal_pdf("BESTELLSCHEIN", meta_text, bestell_daten, 0.0, "Hinweis: Bitte bei der Zentrale abholen.")
            st.session_state["pdf_bestellung"] = pdf_buffer
            st.success("PDF wurde erstellt!")

    # 6. Download
    if "pdf_bestellung" in st.session_state:
        st.download_button("📥 PDF herunterladen", st.session_state["pdf_bestellung"], 
                           file_name="Bestellung.pdf", mime="application/pdf")
