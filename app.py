import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

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
""", unsafe_index=True)

# ==============================================================================
# 2. INTERNE LIVE-DATENBANK (ZENTRALER CLOUD-SPEICHER)
# ==============================================================================
DB_DATEI = "ls25_multiplayer_live_data.json"

def lade_globalen_speicher():
    """Lädt alle Daten live für alle Spieler aus der gemeinsamen Datei"""
    if not os.path.exists(DB_DATEI):
        # Das absolute Standard-Setup, falls die Datei noch komplett neu ist
        default_daten = {
            "hoefe": {
                "Hof 1": {"name": "Hof 1 - Hauptbetrieb", "konto": 500000.0},
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
                {"id": 1, "kunde": "Hof 2", "typ": "Dreschen", "feld": 2, "preis": 4500.0, "status": "Offen"}
            ]
        }
        speichere_globalen_speicher(default_daten)
        return default_daten
    
    with open(DB_DATEI, "r", encoding="utf-8") as f:
        return json.load(f)

def speichere_globalen_speicher(daten):
    """Speichert Änderungen sofort auf dem Server ab, damit andere Spieler es live sehen"""
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

# Live-Daten holen
db = lade_globalen_speicher()

LISTE_MONATE = ["März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember", "Januar", "Februar"]
LISTE_STATUS = ["Wachstum", "Erntebereit", "Gegrubbert", "Gepflügt", "Gekalkt", "Stoppel"]

# ==============================================================================
# 3. SIDEBAR (SERVER-STEUERUNG FÜR HOFNAMEN & MONATE)
# ==============================================================================
st.sidebar.image("https://img.icons8.com/color/96/tractor.png", width=80)
st.sidebar.title("⚙️ Server-Zentrale")

# Live-Anpassung der Hofnamen
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

# Schnell-Auswahl für die Navigation
bereich = st.sidebar.radio(
    "Menüpunkt auswählen:",
    ["📊 Dashboard & Finanzen", "🌾 Fruchtpreise", "📅 Saatenkalender", "🗺️ Feldverwaltung", "🚜 Maschinenpool", "💼 LU-Auftragsbuch", "🌱 Mod-Früchte hinzufügen"]
)

# Erstelle ein Mapping für einfachere Zuweisung in Menüs
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
    st.info("Live-Multiplayer-Modus aktiv. Alle Spieler teilen sich diese Übersicht.")
    
    # 3 Spalten für die Höfe
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
        st.success(f"Kontostand von {HOF_MAPPING[sel_hof]} erfolgreich live aktualisiert!")
        st.rerun()

# ==============================================================================
# BEREICH 2: FRUCHTPREISE
# ==============================================================================
elif bereich == "🌾 Fruchtpreise":
    st.title("🌾 Live-Marktplatz & Fruchtpreise")
    
    # Tabelle anzeigen
    df_preise = pd.DataFrame(list(db["preise"].items()), columns=["Fruchtart", "Aktueller Preis pro 1.000L (€)"])
    st.dataframe(df_preise, use_container_width=True, hide_index=True)
    
    st.write("---")
    st.subheader("📈 Preisänderung für den Server eintragen")
    
    f_auswahl = st.selectbox("Fruchtart:", db["fruchtarten"])
    neuer_preis = st.number_input("Neuer Preis (€):", value=float(db["preise"].get(f_auswahl, 500.0)), step=10.0)
    
    if st.button("Preis für alle Spieler ändern"):
        db["preise"][f_auswahl] = neuer_preis
        speichere_globalen_speicher(db)
        st.success(f"Preis für {f_auswahl} wurde live auf {neuer_preis} € aktualisiert!")
        st.rerun()

# ==============================================================================
# BEREICH 3: SAATENKALENDER
# ==============================================================================
elif bereich == "📅 Saatenkalender":
    st.title("📅 LS25 Frucht- und Erntekalender")
    st.caption("Übersicht aller aktiven Früchte auf dem Server.")
    
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
        # Namen schick anzeigen
        df_felder["besitzer"] = df_felder["besitzer"].map(HOF_MAPPING)
        st.dataframe(df_felder, use_container_width=True, hide_index=True)
    else:
        st.info("Es sind noch keine Felder registriert.")
        
    st.write("---")
    col_add, col_edit = st.columns(2)
    
    with col_add:
        st.subheader(" Feld hinzufügen")
        f_id = st.number_input("Feldnummer:", min_value=1, step=1)
        f_besitzer = st.selectbox("Besitzer Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x], key="add_f_bes")
        f_groesse = st.number_input("Größe (ha):", min_value=0.1, step=0.1)
        f_frucht = st.selectbox("Aktuelle Frucht:", db["fruchtarten"], key="add_f_fru")
        f_status = st.selectbox("Feldstatus:", LISTE_STATUS, key="add_f_stat")
        
        if st.button("Feld global eintragen"):
            # Prüfen ob ID schon da
            if any(x['id'] == f_id for x in db["felder"]):
                st.error("Feldnummer existiert bereits!")
            else:
                neues_feld = {"id": int(f_id), "besitzer": f_besitzer, "groesse": f_groesse, "frucht": f_frucht, "status": f_status}
                db["felder"].append(neues_feld)
                speichere_globalen_speicher(db)
                st.success("Feld registriert!")
                st.rerun()
                
    with col_edit:
        st.subheader(" Feldstatus live updaten")
        if db["felder"]:
            f_id_waehl = st.selectbox("Feld zum Bearbeiten:", [x["id"] for x in db["felder"]])
            f_neu_status = st.selectbox("Neuer Status:", LISTE_STATUS, key="edit_f_stat")
            f_neu_frucht = st.selectbox("Neue Frucht drauf:", db["fruchtarten"], key="edit_f_fru")
            
            if st.button("Feld aktualisieren"):
                for feld in db["felder"]:
                    if feld["id"] == f_id_waehl:
                        feld["status"] = f_neu_status
                        feld["frucht"] = f_neu_frucht
                        break
                speichere_globalen_speicher(db)
                st.success(f"Feld {f_id_waehl} live geupdated!")
                st.rerun()

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
        st.info("Keine Maschinen im Fuhrpark eingetragen.")
        
    st.write("---")
    st.subheader("➕ Neue Maschine registrieren")
    m_hof = st.selectbox("Gehört Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    m_typ = st.selectbox("Kategorie:", ["Traktor", "Drescher", "Häcksler", "Sämaschine", "Gülle/Mist", "Transport", "Sonstiges"])
    m_name = st.text_input("Genaue Mod/Modell-Bezeichnung:", placeholder="z.B. Fendt Vario 942")
    
    if st.button("Maschine für alle eintragen"):
        if m_name:
            neue_m_id = max([x["id"] for x in db["maschinen"]], default=0) + 1
            neue_masch = {"id": neue_m_id, "hof": m_m_hof if 'm_m_hof' in locals() else m_hof, "typ": m_typ, "name": m_name, "status": "Frei"}
            db["maschinen"].append(neue_masch)
            speichere_globalen_speicher(db)
            st.success("Maschine erfolgreich im Server-Fuhrpark!")
            st.rerun()

# ==============================================================================
# BEREICH 6: LU-AUFTRAGSBUCH
# ==============================================================================
elif bereich == "💼 LU-Auftragsbuch":
    st.title("💼 Lohnunternehmen & Auftragsbuch")
    
    if db["auftraege"]:
        df_auf = pd.DataFrame(db["auftraege"])
        df_auf["kunde"] = df_auf["kunde"].map(HOF_MAPPING)
        st.dataframe(df_auf, use_container_width=True, hide_index=True)
    else:
        st.info("Aktuell keine offenen oder aktiven Lohnaufträge.")
        
    st.write("---")
    st.subheader("📌 Neuen Auftrag für das Team erstellen")
    
    a_kunde = st.selectbox("Auftraggeber (Kunde):", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
    a_typ = st.selectbox("Arbeitsart:", ["Pflügen", "Grubbern", "Säen", "Düngen", "Kalken", "Dreschen / Ernten", "Häckseln", "Ballen pressen"])
    a_feld = st.number_input("Auf Feld Nummer:", min_value=1, step=1)
    a_preis = st.number_input("Verhandeltes Honorar (€):", min_value=0.0, step=100.0)
    
    if st.button("Auftrag live ausschreiben"):
        neuer_a_id = max([x["id"] for x in db["auftraege"]], default=0) + 1
        neu_auftrag = {"id": neuer_a_id, "kunde": a_kunde, "typ": a_typ, "feld": int(a_feld), "preis": a_preis, "status": "Offen"}
        db["auftraege"].append(neu_auftrag)
        speichere_globalen_speicher(db)
        st.success("Auftrag im Board ausgehängt!")
        st.rerun()

# ==============================================================================
# BEREICH 7: MOD-FRÜCHTE HINZUFÜGEN
# ==============================================================================
elif bereich == "🌱 Mod-Früchte hinzufügen":
    st.title("🌱 Neue Mod-Früchte für den Server registrieren")
    st.write("Wenn du Mods mit neuen Fruchtarten auf dem LS-Server nutzt, kannst du sie hier live für alle ins Tool einpflegen.")
    
    neue_frucht = st.text_input("Name der Frucht (z.B. Roggen, Dinkel, Klee):").strip()
    neu_saat = st.multiselect("In welchen Monaten wird gesät?", LISTE_MONATE)
    neu_ernte = st.multiselect("In welchen Monaten wird geerntet?", LISTE_MONATE)
    std_preis = st.number_input("Standard-Startpreis pro 1000L (€):", min_value=10.0, value=800.0, step=50.0)
    
    if st.button("🚀 Frucht auf dem Server aktivieren"):
        if neue_frucht:
            if neue_frucht in db["fruchtarten"]:
                st.warning("Diese Frucht gibt es schon auf dem Server!")
            else:
                # 1. Fruchtliste erweitern
                db["fruchtarten"].append(neue_frucht)
                # 2. Kalendermonate umrechnen
                saat_indices = [LISTE_MONATE.index(m) + 1 for m in neu_saat]
                ernte_indices = [LISTE_MONATE.index(m) + 1 for m in neu_ernte]
                db["kalender"][neue_frucht] = {"sa": saat_indices, "er": ernte_indices}
                # 3. Standardpreis setzen
                db["preise"][neue_frucht] = std_preis
                
                # Cloud-Speicher überschreiben
                speichere_globalen_speicher(db)
                st.success(f"Genial! '{neue_frucht}' wurde live für alle Bereiche und Spieler freigeschaltet!")
                st.rerun()
        else:
            st.error("Bitte gib einen Namen für die Frucht ein.")
