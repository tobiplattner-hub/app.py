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

# Custom CSS für schickes LS25-Design
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
# Helper-Funktion für PDF-Erstellung
# ==============================================================================
def erstelle_rechnung_pdf(auftrag, kunde_name, lu_name):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, leading=28, textColor=colors.HexColor('#1b5e20'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, leading=16)
    bold_style = ParagraphStyle('Bold', parent=styles['Normal'], fontSize=11, leading=16, fontName='Helvetica-Bold')

    # 1. Logo einbinden (Extragroß)
    if os.path.exists("logo.png"):
        try:
            logo = Image("logo.png", width=280, height=110)
            logo.hAlign = 'RIGHT'
            story.append(logo)
            story.append(Spacer(1, 15))
        except:
            pass

    # 2. Titel & Metadaten
    story.append(Paragraph("<b>LOHNUNTERNEHMEN RECHNUNG</b>", title_style))
    story.append(Spacer(1, 20))
    
    # Infoblöcke (Sender / Empfänger)
    aktuelles_datum = datetime.now().strftime("%d.%m.%Y - %H:%M")
    metadaten_text = f"""
    <b>Dienstleister (LU):</b> {lu_name}<br/>
    <b>Kunde (Hof):</b> {kunde_name}<br/>
    <b>Datum:</b> {aktuelles_datum}<br/>
    <b>Rechnungsnummer:</b> #RE-{auftrag['id']}{datetime.now().strftime('%y%m%d')}
    """
    story.append(Paragraph(metadaten_text, normal_style))
    story.append(Spacer(1, 25))

    # 3. Tabelle mit den Rechnungsposten
    data = [
        [Paragraph('<b>Beschreibung / Dienstleistung</b>', normal_style), Paragraph('<b>Feld</b>', normal_style), Paragraph('<b>Betrag</b>', normal_style)],
        [Paragraph(f"{auftrag['typ']}", normal_style), Paragraph(f"Feld {auftrag['feld']}", normal_style), Paragraph(f"{auftrag['preis']:,.2f} €", normal_style)],
        ['', Paragraph('<b>Gesamtsumme:</b>', bold_style), Paragraph(f"<b>{auftrag['preis']:,.2f} €</b>", bold_style)]
    ]
    
    t = Table(data, colWidths=[300, 100, 130])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2e7d32')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,1), 0.5, colors.grey),
        ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.HexColor('#1b5e20')),
        ('TOPPADDING', (1,-1), (-1,-1), 10),
    ]))
    
    for i in range(3):
        data[0][i].style.textColor = colors.whitesmoke

    story.append(t)
    story.append(Spacer(1, 40))
    
    # 4. Schlusssatz
    story.append(Paragraph("<i>Der Betrag wurde automatisch über das zentrale LS25-Bankensystem live verbucht und ausgeglichen. Vielen Dank für den Auftrag!</i>", normal_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==============================================================================
# 2. INTERNE LIVE-DATENBANK
# ==============================================================================
DB_DATEI = "ls25_multiplayer_live_data.json"

def lade_globalen_speicher():
    default_daten = {
        "hoefe": {
            "Hof 1": {"name": "Hof 1 - Hauptbetrieb (LU)", "konto": 500000.0},
            "Hof 2": {"name": "Hof 2 - Bio-Betrieb", "konto": 350000.0},
            "Hof 3": {"name": "Hof 3 - Freier Verbund", "konto": 200000.0}
        },
        "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Kartoffeln", "Zuckerrüben"],
        "preise": {
            "Weizen": 850.0, "Gerste": 780.0, "Raps": 1450.0, "Gras": 220.0, "Mais": 900.0, "Kartoffeln": 450.0, "Zuckerrüben": 320.0
        },
        "kalender": {
            "Weizen": {"sa": [1, 2], "er": [5, 6]},
            "Gerste": {"sa": [1, 2], "er": [5]},
            "Raps": {"sa": [6, 7], "er": [5]},
            "Gras": {"sa": [1, 2, 3, 4], "er": [2, 3, 4, 5]},
            "Mais": {"sa": [2, 3], "er": [7, 8]},
            "Kartoffeln": {"sa": [2, 3], "er": [6, 7]},
            "Zuckerrüben": {"sa": [2, 3], "er": [7, 8]}
        },
        "felder": [
            {"id": 1, "besitzer": "Hof 1", "groesse": 4.5, "frucht": "Weizen", "status": "Wachstum"},
            {"id": 2, "besitzer": "Hof 2", "groesse": 2.1, "frucht": "Raps", "status": "Erntebereit"}
        ],
        "maschinen": [
            {"id": 1, "hof": "Hof 1", "typ": "Traktor", "name": "John Deere 7R", "status": "Frei"},
            {"id": 2, "hof": "Hof 1", "typ": "Drescher", "name": "New Holland CR11", "status": "Im Einsatz"}
        ],
        "auftraege": [
            {"id": 1, "kunde": "Hof 2", "auftragnehmer": "Hof 1", "typ": "Dreschen", "feld": 2, "preis": 4500.0, "status": "Offen"}
        ]
    }

    if not os.path.exists(DB_DATEI):
        speichere_globalen_speicher(default_daten)
        return default_daten
    
    try:
        with open(DB_DATEI, "r", encoding="utf-8") as f:
            daten = json.load(f)
            if "auftraege" in daten and isinstance(daten["auftraege"], list):
                bereinigte_auftraege = []
                for auf in daten["auftraege"]:
                    if not isinstance(auf, dict):
                        continue
                    if "auftragsnehmer" in auf:
                        auf["auftragnehmer"] = auf.pop("auftragsnehmer")
                    if "auftragnehmer" not in auf:
                        auf["auftragnehmer"] = "Hof 1"
                    if "kunde" not in auf:
                        auf["kunde"] = "Hof 2"
                    bereinigte_auftraege.append(auf)
                daten["auftraege"] = bereinigte_auftraege
            else:
                daten["auftraege"] = default_daten["auftraege"]
            return daten
    except Exception as e:
        return default_daten

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()

LISTE_MONATE = ["März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember", "Januar", "Februar"]
LISTE_STATUS = ["Wachstum", "Erntebereit", "Gegrubbert", "Gepflügt", "Gekalkt", "Stoppel"]

# ==============================================================================
# 3. SIDEBAR (Mit neuer Reset-Funktion für das Auftragsbuch)
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
        st.success("Erfolgreich gespeichert!")
        st.rerun()

# NEU: Kassenbuch / Auftragsbuch zurücksetzen
with st.sidebar.expander("⚠️ Server-Daten zurücksetzen"):
    st.write("Hier kannst du das komplette Auftragsbuch für eine neue Saison leeren.")
    sicherheits_check = st.checkbox("Ja, ich will das Auftragsbuch unwiderruflich leeren", value=False)
    
    if st.button("🚨 Auftragsbuch komplett zurücksetzen"):
        if sicherheits_check:
            db["auftraege"] = []  # Leert die Liste aller Lohnaufträge komplett
            speichere_globalen_speicher(db)
            st.sidebar.success("Auftragsbuch erfolgreich geleert!")
            st.rerun()
        else:
            st.sidebar.error("Bitte bestätige zuerst die Sicherheits-Checkbox!")

bereich = st.sidebar.radio(
    "Menüpunkt auswählen:",
    ["📊 Dashboard & Finanzen", "🌾 Fruchtpreise", "📅 Saatenkalender", "🗺️ Feldverwaltung", "🚜 Maschinenpool", "💼 LU-Auftragsbuch", "🌱 Mod-Früchte hinzufügen"]
)

HOF_MAPPING = {
    "Hof 1": db["hoefe"]["Hof 1"]["name"],
    "Hof 2": db["hoefe"]["Hof 2"]["name"],
    "Hof 3": db["hoefe"]["Hof 3"]["name"]
}

# ==============================================================================
# BEREICH 1: DASHBOARD & FINANZEN
# ==============================================================================
if bereich == "📊 Dashboard & Finanzen":
    st.title("🚜 LS25 Server-Dashboard")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label=db["hoefe"]["Hof 1"]["name"], value=f"{db['hoefe']['Hof 1']['konto']:,.2f} €")
    with col2:
        st.metric(label=db["hoefe"]["Hof 2"]["name"], value=f"{db['hoefe']['Hof 2']['konto']:,.2f} €")
    with col3:
        st.metric(label=db["hoefe"]["Hof 3"]["name"], value=f"{db['hoefe']['Hof 3']['konto']:,.2f} €")
        
    st.write("---")
    st.subheader("💰 Kontostand live anpassen")
    
    sel_hof = st.selectbox("Welcher Hof?", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    aktion = st.radio("Aktion:", ["Einzahlen / Gewinn", "Auszahlen / Einkauf"])
    betrag = st.number_input("Betrag in €:", min_value=0.0, step=500.0)
    
    if st.button("Buchung global ausführen"):
        if aktion == "Einzahlen / Gewinn":
            db["hoefe"][sel_hof]["konto"] += betrag
        else:
            db["hoefe"][sel_hof]["konto"] -= betrag
        speichere_globalen_speicher(db)
        st.success(f"Kontostand von {HOF_MAPPING[sel_hof]} live aktualisiert!")
        st.rerun()

# ==============================================================================
# BEREICH 2: FRUCHTPREISE
# ==============================================================================
elif bereich == "🌾 Fruchtpreise":
    st.title("🌾 Live-Marktplatz & Fruchtpreise")
    
    df_preise = pd.DataFrame(list(db["preise"].items()), columns=["Fruchtart", "Aktueller Preis pro 1.000L (€)"])
    st.dataframe(df_preise, use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("📈 Preisänderung für den Server eintragen")
    f_auswahl = st.selectbox("Fruchtart:", db["fruchtarten"])
    neuer_preis = st.number_input("Neuer Preis (€):", value=float(db["preise"].get(f_auswahl, 500.0)), step=10.0)
    
    if st.button("Preis für alle Spieler ändern"):
        db["preise"][f_auswahl] = neuer_preis
        speichere_globalen_speicher(db)
        st.success(f"Preis für {f_auswahl} live aktualisiert!")
        st.rerun()

# ==============================================================================
# BEREICH 3: SAATENKALENDER
# ==============================================================================
elif bereich == "📅 Saatenkalender":
    st.title("📅 LS25 Frucht- und Erntekalender")
    for f in db["fruchtarten"]:
        k = db["kalender"].get(f, {"sa": [], "er": []})
        saat_namen = [LISTE_MONATE[i-1] for i in k["sa"]]
        ernte_namen = [LISTE_MONATE[i-1] for i in k["er"]]
        with st.container():
            st.markdown(f"### 🌾 {f}")
            st.write(f"🟢 **Aussaat:** {', '.join(saat_namen) if saat_namen else 'Nicht definiert'}")
            st.write(f"🍂 **Ernte:** {', '.join(ernte_namen) if ernte_namen else 'Nicht definiert'}")
            st.write("---")

# ==============================================================================
# BEREICH 4: FELDVERWALTUNG
# ==============================================================================
elif bereich == "🗺️ Feldverwaltung":
    st.title("🗺️ Globale Feldverwaltung")
    
    if db["felder"]:
        df_felder = pd.DataFrame(db["felder"])
        df_felder["besitzer"] = df_felder["besitzer"].map(HOF_MAPPING)
        st.dataframe(df_felder, use_container_width=True, hide_index=True)
    else:
        st.info("Es sind noch keine Felder registriert.")
        
    st.write("---")
    col_add, col_edit, col_del = st.columns(3)
    
    with col_add:
        st.subheader("➕ Feld hinzufügen")
        f_id = st.number_input("Feldnummer:", min_value=1, step=1)
        f_besitzer = st.selectbox("Besitzer Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
        f_groesse = st.number_input("Größe (ha):", min_value=0.1, step=0.1)
        f_frucht = st.selectbox("Aktuelle Frucht:", db["fruchtarten"])
        f_status = st.selectbox("Feldstatus:", LISTE_STATUS)
        
        if st.button("Feld global eintragen"):
            if any(x['id'] == f_id for x in db["felder"]):
                st.error("Feldnummer existiert bereits!")
            else:
                db["felder"].append({"id": int(f_id), "besitzer": f_besitzer, "groesse": f_groesse, "frucht": f_frucht, "status": f_status})
                speichere_globalen_speicher(db)
                st.success("Feld registriert!")
                st.rerun()
                
    with col_edit:
        st.subheader("🔄 Feldstatus live updaten")
        if db["felder"]:
            f_id_waehl = st.selectbox("Feld zum Bearbeiten:", [x["id"] for x in db["felder"]], key="edit_select")
            f_neu_status = st.selectbox("Neuer Status:", LISTE_STATUS)
            f_neu_frucht = st.selectbox("Neue Frucht drauf:", db["fruchtarten"])
            
            if st.button("Feld aktualisieren"):
                for feld in db["felder"]:
                    if feld["id"] == f_id_waehl:
                        feld["status"] = f_neu_status
                        feld["frucht"] = f_neu_frucht
                        break
                speichere_globalen_speicher(db)
                st.success(f"Feld {f_id_waehl} live geupdated!")
                st.rerun()
        else:
            st.caption("Keine Felder zum Bearbeiten da.")

    with col_del:
        st.subheader("❌ Feld entfernen")
        if db["felder"]:
            f_id_loeschen = st.selectbox("Welches Feld soll gelöscht werden?", [x["id"] for x in db["felder"]], key="del_select")
            
            st.warning(f"Achtung: Feld {f_id_loeschen} wird permanent vom Server gelöscht!")
            if st.button("🗑️ Feld unwiderruflich entfernen"):
                db["felder"] = [x for x in db["felder"] if x["id"] != f_id_loeschen]
                speichere_globalen_speicher(db)
                st.success(f"Feld {f_id_loeschen} erfolgreich entfernt!")
                st.rerun()
        else:
            st.caption("Keine Felder zum Löschen vorhanden.")

# ==============================================================================
# BEREICH 5: MASCHINENPOOL
# ==============================================================================
elif bereich == "🚜 Maschinenpool":
    st.title("🚜 Gemeinsamer Maschinenpool")
    
    if db["maschinen"]:
        df_masch = pd.DataFrame(db["maschinen"])
        df_masch["hof"] = df_masch["hof"].map(HOF_MAPPING)
        st.dataframe(df_masch, use_container_width=True, hide_index=True)
    else:
        st.info("Keine Maschinen im Fuhrpark.")
        
    st.write("---")
    st.subheader("➕ Neue Maschine registrieren")
    m_hof = st.selectbox("Gehört Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    m_typ = st.selectbox("Kategorie:", ["Traktor", "Drescher", "Häcksler", "Sämaschine", "Sonstiges"])
    m_name = st.text_input("Bezeichnung:")
    
    if st.button("Maschine für alle eintragen"):
        if m_name:
            neue_m_id = max([x["id"] for x in db["maschinen"]], default=0) + 1
            db["maschinen"].append({"id": neue_m_id, "hof": m_hof, "typ": m_typ, "name": m_name, "status": "Frei"})
            speichere_globalen_speicher(db)
            st.success("Maschine registriert!")
            st.rerun()

# ==============================================================================
# BEREICH 6: LU-AUFTRAGSBUCH & RECHNUNGSFUNKTION + PDF
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 LU-Auftragsbuch & Rechnungszentrum")
    
    if db["auftraege"]:
        df_auf = pd.DataFrame(db["auftraege"])
        df_auf_anzeige = df_auf.copy()
        
        df_auf_anzeige["kunde"] = df_auf_anzeige["kunde"].map(HOF_MAPPING)
        df_auf_anzeige["auftragnehmer"] = df_auf_anzeige["auftragnehmer"].map(HOF_MAPPING)
        st.dataframe(df_auf_anzeige, use_container_width=True, hide_index=True)
    else:
        st.info("Aktuell keine Lohnaufträge eingetragen.")
        
    st.write("---")
    col_rechnung, col_neu_auf = st.columns(2)
    
    with col_rechnung:
        st.subheader("💳 Auftrag abrechnen (Geld überweisen)")
        offene_auftraege = [x for x in db["auftraege"] if x.get("status") == "Offen"]
        
        if offene_auftraege:
            auswahl_auftrag_id = st.selectbox(
                "Welcher Auftrag wurde erledigt?",
                options=[x["id"] for x in offene_auftraege],
                format_func=lambda x: f"ID {x}: {[a['typ'] for a in offene_auftraege if a['id']==x][0]} auf Feld {[a['feld'] for a in offene_auftraege if a['id']==x][0]} ({[a['preis'] for a in offene_auftraege if a['id']==x][0]:,.2f} €)"
            )
            
            if st.button("💰 Erledigt & Live Abrechnen"):
                letzter_abgerechneter_auftrag = None
                for auf in db["auftraege"]:
                    if auf["id"] == auswahl_auftrag_id:
                        kunde = auf["kunde"]
                        lu = auf["auftragnehmer"]
                        preis = auf["preis"]
                        
                        db["hoefe"][kunde]["konto"] -= preis  
                        db["hoefe"][lu]["konto"] += preis     
                        auf["status"] = "Abgerechnet"
                        letzter_abgerechneter_auftrag = auf
                        break
                        
                speichere_globalen_speicher(db)
                st.success(f"Rechnung beglichen! Das Honorar wurde live verbucht.")
                
                st.session_state["pdf_bereit"] = letzter_abgerechneter_auftrag
                st.rerun()
        else:
            st.success("Alle Aufträge wurden bereits bezahlt und abgerechnet! 🎉")

        if "pdf_bereit" in st.session_state and st.session_state["pdf_bereit"] is not None:
            auf_daten = st.session_state["pdf_bereit"]
            k_name = HOF_MAPPING.get(auf_daten["kunde"], auf_daten["kunde"])
            l_name = HOF_MAPPING.get(auf_daten["auftragnehmer"], auf_daten["auftragnehmer"])
            
            pdf_datei = erstelle_rechnung_pdf(auf_daten, k_name, l_name)
            
            st.write("---")
            st.download_button(
                label="📄 PDF-Rechnung herunterladen",
                data=pdf_datei,
                file_name=f"Rechnung_LU_ID_{auf_daten['id']}.pdf",
                mime="application/pdf"
            )
            
    with col_neu_auf:
        st.subheader("📌 Neuen Auftrag ausschreiben")
        a_kunde = st.selectbox("Auftraggeber (Kunde):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x], key="ku")
        a_lu = st.selectbox("Auftragnehmer (Lohnunternehmen):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x], key="lu")
        a_typ = st.selectbox("Arbeitsart:", ["Pflügen", "Grubbern", "Säen", "Düngen", "Dreschen / Ernten", "Häckseln"])
        a_feld = st.number_input("Auf Feld Nummer:", min_value=1, step=1, key="fe")
        a_preis = st.number_input("Verhandeltes Honorar (€):", min_value=0.0, step=100.0, key="pr")
        
        if st.button("Auftrag live buchen"):
            neuer_a_id = max([x["id"] for x in db["auftraege"]], default=0) + 1
            db["auftraege"].append({
                "id": neuer_a_id, 
                "kunde": a_kunde, 
                "auftragnehmer": a_lu, 
                "typ": a_typ, 
                "feld": int(a_feld), 
                "preis": a_preis, 
                "status": "Offen"
            })
            speichere_globalen_speicher(db)
            st.success("Auftrag im Board ausgehängt!")
            st.rerun()

# ==============================================================================
# BEREICH 7: MOD-FRÜCHTE HINZUFÜGEN
# ==============================================================================
elif bereich == "🌱 Mod-Früchte hinzufügen":
    st.title("🌱 Neue Mod-Früchte registrieren")
    
    neue_frucht = st.text_input("Name der Frucht:").strip()
    neu_saat = st.multiselect("In welchen Monaten wird gesät?", LISTE_MONATE)
    neu_ernte = st.multiselect("In welchen Monaten wird geerntet?", LISTE_MONATE)
    std_preis = st.number_input("Standard-Startpreis pro 1000L (€):", min_value=10.0, value=800.0, step=50.0)
    
    if st.button("🚀 Frucht auf dem Server aktivieren"):
        if neue_frucht and neue_frucht not in db["fruchtarten"]:
            db["fruchtarten"].append(neue_frucht)
            saat_indices = [LISTE_MONATE.index(m) + 1 for m in neu_saat]
            ernte_indices = [LISTE_MONATE.index(m) + 1 for m in neu_ernte]
            db["kalender"][neue_frucht] = {"sa": saat_indices, "er": ernte_indices}
            db["preise"][neue_frucht] = std_preis
            
            speichere_globalen_speicher(db)
            st.success(f"'{neue_frucht}' wurde live für alle Bereiche freigeschaltet!")
            st.rerun()
