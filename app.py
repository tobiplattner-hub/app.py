import streamlit as st
import pandas as pd
import datetime
import os

# ---------------------------------------------------------
# SEITEN-KONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="LS25 LU- & Hof-Manager LIVE", layout="wide")

# ---------------------------------------------------------
# DIE EINFACHE CLOUD-DATENBANK INITIALISIEREN
# ---------------------------------------------------------
# Hier aktivieren wir einen internen Cloud-Speicher, der für alle Spieler synchron ist
db = st.connection("kv_storage", type="dict")

LISTE_MONATE = ["März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember", "Januar", "Februar"]

# ---------------------------------------------------------
# STANDARD-DATEN (Falls die Datenbank ganz frisch und leer ist)
# ---------------------------------------------------------
if "hoefe" not in db:
    db["hoefe"] = {
        "Hof 1": {"name": "Hof 1 - Hauptbetrieb", "konto": 500000.0},
        "Hof 2": {"name": "Hof 2 - Bio-Betrieb", "konto": 350000.0},
        "Hof 3": {"name": "Hof 3 - Freier Verbund", "konto": 200000.0}
    }

if "fruchtarten" not in db:
    db["fruchtarten"] = ["Weizen", "Gerste", "Raps", "Gras", "Mais", "Kartoffeln"]

if "kalender" not in db:
    db["kalender"] = {
        "Weizen": {"sa": [1, 2], "er": [5, 6]},
        "Gerste": {"sa": [1, 2], "er": [5]},
        "Raps": {"sa": [6, 7], "er": [5]},
        "Gras": {"sa": [1, 2, 3, 4], "er": [2, 3, 4, 5]}
    }

# ---------------------------------------------------------
# LIVE-DATEN AUS DER CLOUD HOLEN
# ---------------------------------------------------------
# Jedes Mal wenn ein Spieler klickt, laden wir den aktuellen Cloud-Stand
hoefe_daten = db["hoefe"]
frucht_liste = db["fruchtarten"]
kalender_daten = db["kalender"]

# ---------------------------------------------------------
# HAUPTANZEIGE
# ---------------------------------------------------------
st.title("🚜 LS25 Live-Multiplayer Hof-Manager")
st.info("Dieses Tool ist jetzt live! Jede Änderung wird sofort für alle Spieler auf dem Server gespeichert.")

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
# SIDEBAR: MANAGEMENT (Änderungen gehen direkt in die Cloud)
# ---------------------------------------------------------
st.sidebar.title("⚙️ Server-Einstellungen")

# 1. Hofnamen anpassen
with st.sidebar.expander("📝 Hofnamen live ändern"):
    h1_new = st.text_input("Name Hof 1:", value=hoefe_daten["Hof 1"]["name"])
    h2_new = st.text_input("Name Hof 2:", value=hoefe_daten["Hof 2"]["name"])
    h3_new = st.text_input("Name Hof 3:", value=hoefe_daten["Hof 3"]["name"])
    
    if st.button("Namen für ALLE speichern"):
        hoefe_daten["Hof 1"]["name"] = h1_new
        hoefe_daten["Hof 2"]["name"] = h2_new
        hoefe_daten["Hof 3"]["name"] = h3_new
        # Direkt zurück in die Cloud schreiben
        db["hoefe"] = hoefe_daten
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
            frucht_liste.append(neue_frucht)
            db["fruchtarten"] = frucht_liste
            
            # Kalendermonate (als Zahlen 1-12) speichern
            saat_indices = [LISTE_MONATE.index(m) + 1 for m in neu_saat]
            ernte_indices = [LISTE_MONATE.index(m) + 1 for m in neu_ernte]
            kalender_daten[neue_frucht] = {"sa": saat_indices, "er": ernte_indices}
            db["kalender"] = kalender_daten
            
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
