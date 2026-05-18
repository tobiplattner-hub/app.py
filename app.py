import streamlit as st
import pandas as pd
import json
import os

# ---------------------------------------------------------
# SEITEN-KONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="LS25 LU- & Hof-Manager LIVE", layout="wide")

# ---------------------------------------------------------
# DIE EINFACHE DATEI-DATENBANK (DOKUMENTEN-SPEICHER)
# ---------------------------------------------------------
# Diese Datei wird direkt auf dem Server erstellt und speichert alles dauerhaft ab
DB_DATEI = "multiplayer_live_speicher.json"

def lade_globalen_speicher():
    """Lädt die Spieldaten für alle Spieler aus der gemeinsamen Datei"""
    if not os.path.exists(DB_DATEI):
        # Standard-Daten erstellen, falls die Datei noch nicht existiert
        default_daten = {
            "hoefe": {
                "Hof 1": {"name": "Hof 1 - Hauptbetrieb", "konto": 500000.0},
                "Hof 2": {"name": "Hof 2 - Bio-Betrieb", "konto": 350000.0},
                "Hof 3": {"name": "Hof 3 - Freier Verbund", "konto": 200000.0}
            },
            "fruchtarten": ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Kartoffeln"],
            "kalender": {
                "Weizen": {"sa": [1, 2], "er": [5, 6]},
                "Gerste": {"sa": [1, 2], "er": [5]},
                "Raps": {"sa": [6, 7], "er": [5]},
                "Gras": {"sa": [1, 2, 3, 4], "er": [2, 3, 4, 5]}
            }
        }
        speichere_globalen_speicher(default_daten)
        return default_daten
    
    with open(DB_DATEI, "r", encoding="utf-8") as f:
        return json.load(f)

def speichere_globalen_speicher(daten):
    """Schreibt die Änderungen sofort in die Datei, damit alle Spieler es sehen"""
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

# ---------------------------------------------------------
# DATEN LADEN
# ---------------------------------------------------------
# Bei jedem Laden/Klick ziehen wir uns den echten Server-Stand
global_db = lade_globalen_speicher()

hoefe_daten = global_db["hoefe"]
frucht_liste = global_db["fruchtarten"]
kalender_daten = global_db["kalender"]

LISTE_MONATE = ["März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember", "Januar", "Februar"]

# ---------------------------------------------------------
# HAUPTANZEIGE
# ---------------------------------------------------------
st.title("🚜 LS25 Live-Multiplayer Hof-Manager")
st.info("Dieses Tool läuft jetzt über eine serverbasierte Live-Synchronisation! Jede Änderung ist sofort für alle sichtbar.")

# Kontostände anzeigen
st.subheader("Aktuelle Höfe & Finanzen")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label=hoefe_daten["Hof 1"]["name"], value=f"{hoefe_daten['Hof 1']['konto']:,.2f} €")
with col2:
    st.metric(label=hoefe_daten["Hof 2"]["name"], value=f"{hoefe_daten['Hof 2']['konto']:,.2f} €")
with col3:
    st.metric(label=hoefe_daten["Hof 3"]["name"], value=f"{hoefe_daten['Hof 3']['konto']:,.2f} €")

st.write("---")

# ---------------------------------------------------------
# SIDEBAR: MANAGEMENT (Änderungen gehen direkt in die Datei)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Server-Einstellungen")

# 1. Hofnamen anpassen
with st.sidebar.expander("📝 Hofnamen live ändern"):
    h1_new = st.text_input("Name Hof 1:", value=hoefe_daten["Hof 1"]["name"])
    h2_new = st.text_input("Name Hof 2:", value=hoefe_daten["Hof 2"]["name"])
    h3_new = st.text_input("Name Hof 3:", value=hoefe_daten["Hof 3"]["name"])
    
    if st.button("Namen für ALLE speichern"):
        global_db["hoefe"]["Hof 1"]["name"] = h1_new
        global_db["hoefe"]["Hof 2"]["name"] = h2_new
        global_db["hoefe"]["Hof 3"]["name"] = h3_new
        
        # In die Datei auf dem Server wegspeichern
        speichere_globalen_speicher(global_db)
        st.success("Hofnamen global aktualisiert!")
        st.rerun()

# 2. Mod-Früchte & Kalender anpassen
with st.sidebar.expander("🌱 Mod-Früchte & Kalender"):
    st.subheader("Neue Frucht registrieren")
    neue_frucht = st.text_input("Name der Mod-Frucht:", placeholder="z.B. Dinkel").strip()
    neu_saat = st.multiselect("Sämonate:", LISTE_MONATE)
    neu_ernte = st.multiselect("Erntemonate:", LISTE_MONATE)
    
    if st.button("➕ Frucht global hinzufügen"):
        if neue_frucht and neue_frucht not in frucht_liste:
            # Fruchtliste erweitern
            global_db["fruchtarten"].append(neue_frucht)
            
            # Kalendermonate (als Zahlen 1-12) berechnen
            saat_indices = [LISTE_MONATE.index(m) + 1 for m in neu_saat]
            ernte_indices = [LISTE_MONATE.index(m) + 1 for m in neu_ernte]
            global_db["kalender"][neue_frucht] = {"sa": saat_indices, "er": ernte_indices}
            
            # Speicher updaten
            speichere_globalen_speicher(global_db)
            
            st.success(f"{neue_frucht} ist jetzt für alle verfügbar!")
            st.rerun()

# ---------------------------------------------------------
# FRUCHTKALENDER-ÜBERSICHT
# ---------------------------------------------------------
st.subheader("Registrierte Früchte & Saatenkalender")
for f in frucht_liste:
    k = kalender_daten.get(f, {"sa": [], "er": []})
    saat_namen = [LISTE_MONATE[i-1] for i in k["sa"]]
    ernte_namen = [LISTE_MONATE[i-1] for i in k["er"]]
    st.write(f"🌾 **{f}** — Aussaat: `{', '.join(saat_namen) if saat_namen else 'Keine'}` | Ernte: `{', '.join(ernte_namen) if ernte_namen else 'Keine'}`")
