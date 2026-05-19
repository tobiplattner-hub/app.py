import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

# ==============================================================================
# 1. SEITEN-KONFIGURATION
# ==============================================================================
st.set_page_config(page_title="LS25 Hof-Manager", layout="wide")

# (Hier würden deine Hilfsfunktionen stehen: lade_maschinen_aus_sheets, lade_kunden_aus_sheets, erstelle_universal_pdf, etc.)
# ... (Ich behalte die Grundstruktur bei, um den Code kompakt zu halten) ...

DB_DATEI = "ls25_multiplayer_live_data.json"

def lade_globalen_speicher():
    if not os.path.exists(DB_DATEI):
        return generiere_standard_daten()
    with open(DB_DATEI, "r", encoding="utf-8") as f:
        return json.load(f)

def speichere_globalen_speicher(daten):
    with open(DB_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=4)

db = lade_globalen_speicher()
HOF_MAPPING = {k: v["name"] for k, v in db["hoefe"].items()}

# ==============================================================================
# HAUPTMENÜ (Sidebar)
# ==============================================================================
bereich = st.sidebar.radio("Menüpunkt:", [
    "📊 Dashboard & Finanzen", "💼 LU-Auftragsbuch", "🌾 Warenverkauf", 
    "🚜 Fuhrpark", "📈 Preise", "🗺️ Feldverwaltung", "📅 Kalender", "📦 Hof-Lagerverwaltung"
])

# ==============================================================================
# BEREICH 8: HOF-LAGERVERWALTUNG (VOLLSTÄNDIGER CODE)
# ==============================================================================
if bereich == "📦 Hof-Lagerverwaltung":
    st.title("📦 Hof-Lagerverwaltung & Silomanagement")
    
    aktueller_m = db.get("aktueller_monat", "Januar")
    
    # 1. Hilfs-Logik: Silage-Gärung Status prüfen
    fertige_silage_pro_hof = {"Hof 1": 0, "Hof 2": 0, "Hof 3": 0}
    if db.get("silage_gärung"):
        for g in db["silage_gärung"]:
            idx_start = MONATE_LISTE.index(g["start_monat"])
            idx_bereit = (idx_start + g["dauer"]) % 12
            idx_akt = MONATE_LISTE.index(aktueller_m)
            
            # Logik für Gärung
            schon_fertig = (idx_start <= idx_bereit and (idx_akt >= idx_bereit or idx_akt < idx_start)) or \
                           (idx_start > idx_bereit and (idx_bereit <= idx_akt < idx_start))
            if schon_fertig:
                fertige_silage_pro_hof[g["hof"]] += g["menge"]
    
    # 2. Tabelle erstellen
    lager_daten = []
    for h_id in ["Hof 1", "Hof 2", "Hof 3"]:
        for gut, menge in db["lager"].get(h_id, {}).items():
            if menge > 0:
                kategorie = "Loses Material"
                if any(x in gut.lower() for x in ["palette", "saatgut"]): kategorie = "Paletten-Ware"
                elif "ballen" in gut.lower(): kategorie = "Ballen-Ware"
                elif "kalk" in gut.lower(): kategorie = "Betriebsmittel"
                
                lager_daten.append({"Hof": HOF_MAPPING[h_id], "Warenname": gut, "Kategorie": kategorie, "Menge (L)": menge})
        
        if fertige_silage_pro_hof[h_id] > 0:
            lager_daten.append({"Hof": HOF_MAPPING[h_id], "Warenname": "Silage (Silo - BEREIT)", "Kategorie": "Silo-Produkt", "Menge (L)": fertige_silage_pro_hof[h_id]})

    # 3. Anzeige
    if lager_daten:
        st.dataframe(pd.DataFrame(lager_daten), use_container_width=True, hide_index=True)
    
    # 4. Buchungsmaske
    with st.expander("👉 Buchung erfassen", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            l_hof = st.selectbox("Hof:", ["Hof 1", "Hof 2", "Hof 3"], format_func=lambda x: HOF_MAPPING[x])
            l_typ = st.radio("Aktion:", ["➕ Einlagern", "➖ Auslagern"], horizontal=True)
            
            if "Auslagern" in l_typ:
                vorhandene = [d["Warenname"] for d in lager_daten if d["Hof"] == HOF_MAPPING[l_hof]]
                l_name = st.selectbox("Waren:", sorted(list(set(vorhandene)))) if vorhandene else ""
            else:
                l_name = st.text_input("Warenname:")
        with col2:
            menge = st.number_input("Menge (L):", min_value=1, value=1000)
            kat = st.selectbox("Kategorie:", ["Loses Material", "Paletten-Ware", "Ballen-Ware", "Betriebsmittel", "Silo-Produkt"])
        
        if st.button("💾 Speichern"):
            if "Einlagern" in l_typ:
                if l_hof not in db["lager"]: db["lager"][l_hof] = {}
                db["lager"][l_hof][l_name] = db["lager"][l_hof].get(l_name, 0) + menge
                if "Silo" in kat: db["silage_gärung"].append({"hof": l_hof, "menge": menge, "start_monat": aktueller_m, "dauer": 2})
            else:
                if l_name in db["lager"].get(l_hof, {}):
                    db["lager"][l_hof][l_name] -= menge
            speichere_globalen_speicher(db)
            st.rerun()

# ==============================================================================
# HINWEIS: Hier fügst du die restlichen 'elif'-Bereiche aus deinem bisherigen Code ein.
# ==============================================================================
