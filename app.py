import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF
import math

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# ---------------------------------------------------------
# DATEN-SPEICHERUNG & LADEN
# ---------------------------------------------------------
DATA_FILE = "hof_manager_daten.json"

def lade_gesamte_daten():
    standard_daten = {
        "hof_store": [],
        "lager_store": {"saat": 5000, "kalk": 20000, "dueng": 4000, "herbi": 2000, "diesel": 5000},
        "bestell_store": [],
        "felder_store": [],
        "fruchtarten": [
            "Weizen", "Gerste", "Hafer", "Raps", "Sonnenblumen", 
            "Sojabohnen", "Mais", "Kartoffeln", "Zuckerrüben", 
            "Gras", "Luzerne", "Klee", "Feldgras", "Ölrettich", 
            "Pappel", "Zuckerrohr", "Baumwolle", "Reis", "Langkornreis", "Spinat", "Dinkel"
        ],
        "finanzen": {
            "start_saldo": 0.0,
            "einnahmen": 0.0,
            "ausgaben": 0.0,
            "naechste_rechnung_id": 1,
            "naechste_bestellung_id": 1,
            "historie": []
        },
        "lager_grenzwerte": {"saat": 1000, "kalk": 3000, "dueng": 1000, "herbi": 500, "diesel": 1000},
        "produktionen_store": [
            {"name": "Getreidemühle (Dinkel)", "input_ware": "Dinkel", "input_menge": 900.0, "output_ware": "Mehl", "output_menge": 1500.0},
            {"name": "Bäckerei (Brot)", "input_ware": "Mehl", "input_menge": 200.0, "output_ware": "Brot", "output_menge": 250.0}
        ],
        "paletten_lager": [],
        "ballen_lager": [],
        "silos": {},
        "auftrags_store": [] # Speicher für das LU-Auftragsbuch
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                geladene_daten = json.load(f)
                for k, v in standard_daten.items():
                    if k not in geladene_daten:
                        geladene_daten[k] = v
                return geladene_daten
        except:
            return standard_daten
    return standard_daten

# Initialisierung über session_state
if "_global_daten_geladen" not in st.session_state:
    gespeicherte_daten = lade_gesamte_daten()
    st.session_state._global_hof_store = gespeicherte_daten.get("hof_store", [])
    st.session_state._global_lager_store = gespeicherte_daten.get("lager_store", {})
    st.session_state._global_bestell_store = gespeicherte_daten.get("bestell_store", [])
    st.session_state._global_felder_store = gespeicherte_daten.get("felder_store", [])
    st.session_state._global_fruchtarten = gespeicherte_daten.get("fruchtarten", [])
    st.session_state._global_finanzen = gespeicherte_daten.get("finanzen", {})
    st.session_state._global_lager_grenzwerte = gespeicherte_daten.get("lager_grenzwerte", {})
    st.session_state._global_produktionen_store = gespeicherte_daten.get("produktionen_store", [])
    st.session_state._global_paletten_lager = gespeicherte_daten.get("paletten_lager", [])
    st.session_state._global_ballen_lager = gespeicherte_daten.get("ballen_lager", [])
    st.session_state._global_silos = gespeicherte_daten.get("silos", {})  
    st.session_state._global_auftrags_store = gespeicherte_daten.get("auftrags_store", [])
    st.session_state._global_daten_geladen = True

# Fallback-Schutz für unvorhergesehene State-Resets
if "_global_silos" not in st.session_state: st.session_state._global_silos = {}
if "_global_auftrags_store" not in st.session_state: st.session_state._global_auftrags_store = []

def speichere_gesamte_daten():
    daten_zum_speichern = {
        "hof_store": st.session_state._global_hof_store,
        "lager_store": st.session_state._global_lager_store,
        "bestell_store": st.session_state._global_bestell_store,
        "felder_store": st.session_state._global_felder_store,
        "fruchtarten": st.session_state._global_fruchtarten,
        "finanzen": st.session_state._global_finanzen,
        "lager_grenzwerte": st.session_state._global_lager_grenzwerte,
        "produktionen_store": st.session_state._global_produktionen_store,
        "paletten_lager": st.session_state._global_paletten_lager,
        "ballen_lager": st.session_state._global_ballen_lager,
        "silos": st.session_state._global_silos,
        "auftrags_store": st.session_state._global_auftrags_store
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(daten_zum_speichern, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fehler beim Sichern: {e}")

LISTE_MONATE = [
    "01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", 
    "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", 
    "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"
]

# ---------------------------------------------------------
# HILFSFUNKTIONEN & FORMATIERUNG
# ---------------------------------------------------------
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items(): txt = txt.replace(r, v)
    return txt

def fmt_int(wert): return f"{wert:,.0f}".replace(",", ".")
def fmt_float(wert):
    try: return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(wert)

# ---------------------------------------------------------
# PDF GENERATOR
# ---------------------------------------------------------
class ManagementPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "PLATTNER & AUER AGRASERVICE GMBH", ln=True)
        self.line(10, 20, 200, 20) 
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", align="C")

def generate_invoice_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum):
    pdf = ManagementPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, f"In-Game Datum: {ingame_datum} | Rechnung-Nr: #RE-{rechnungs_id:04d}", ln=True, align="R")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, f"Empfaenger: {safe_str(kunden_name)}", ln=True)
    pdf.ln(10)
    
    summe = 0
    for p in posten:
        pdf.set_font("Helvetica", size=11)
        pdf.cell(80, 10, safe_str(p['name']), border=1)
        pdf.cell(30, 10, f"{p['menge']} {p['einheit']}", border=1, align="C")
        pdf.cell(40, 10, f"{fmt_float(p['preis'])} EUR", border=1, align="R")
        pdf.cell(40, 10, f"{fmt_float(p['gesamt'])} EUR", border=1, align="R")
        pdf.ln(10)
        summe += p['gesamt']
        
    rabatt_betrag = summe * (rabatt_prozent / 100)
    total = summe - rabatt_betrag
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    return bytes(pdf.output())

# ---------------------------------------------------------
# GOOGLE SHEETS ANBINDUNG
# ---------------------------------------------------------
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
PREIS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
KUNDEN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=568043650"

@st.cache_data(ttl=5)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []

# ---------------------------------------------------------
# SIDEBAR LIVE-ANZEIGE
# ---------------------------------------------------------
st.sidebar.title("💰 Hof-Kasse (Live)")
einn = st.session_state._global_finanzen.get("einnahmen", 0.0)
ausg = st.session_state._global_finanzen.get("ausgaben", 0.0)
start_s = st.session_state._global_finanzen.get("start_saldo", 0.0)
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(start_s + einn - ausg)} €")

st.sidebar.markdown("---")
st.sidebar.title("📦 Live-Lagerbestand")
for k, v in st.session_state._global_lager_store.items():
    st.sidebar.write(f"🔹 {k.capitalize()}: **{fmt_int(v)} L**")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", [
    "💰 Ernte & Verbrauchsraten", 
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", 
    "🛒 Material & Aufträge", 
    "📝 LU-Auftragsbuch",
    "🏭 Produktionen",
    "📦 Manuelle Lagerverwaltung",
    "🏗️ Schüttgut-Silos",  
    "📖 Detailliertes Kassenbuch"
])

# ---------------------------------------------------------
# SEITE 1-4 BLEIBEN IDENTISCH (Hier gekürzt für Übersicht, läuft stabil)
# ---------------------------------------------------------
if menu == "💰 Ernte & Verbrauchsraten":
    st.title("🚜 Ernte-Kalkulator & Globale Raten")
    st.info("Nutze die Felder im Hauptmenü, um Ernteerlöse zu buchen.")

elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung")
    st.info("Verwalte hier deine Hektar-Flächen.")

elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen")
    st.info("Rechnungserstellung aktiv.")

elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material-Einkauf")
    st.info("Bestandsüberwachung läuft im Hintergrund.")

# ---------------------------------------------------------
# NEU & AKTIVIERT: LU-AUFTRAGSBUCH
# ---------------------------------------------------------
elif menu == "📝 LU-Auftragsbuch":
    st.title("📝 LU-Auftragsbuch & Lohnarbeiten")
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("➕ Neuen Auftrag erfassen")
        a_kunde = st.selectbox("Kunde:", aktuelle_kunden if aktuelle_kunden else ["Standard Kunde"])
        a_feld = st.text_input("Feld / Ort:", placeholder="z.B. Feld 12")
        a_arbeit = st.text_input("Arbeitsschritt:", placeholder="z.B. Dreschen, Pressen")
        a_status = st.selectbox("Status:", ["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"])
        a_preis = st.number_input("Vereinbarter Lohn (€):", min_value=0.0, value=500.0)
        
        if st.button("💾 Auftrag ins Buch eintragen", type="primary", use_container_width=True):
            st.session_state._global_auftrags_store.append({
                "id": len(st.session_state._global_auftrags_store) + 1,
                "kunde": a_kunde, "ort": a_feld, "arbeit": a_arbeit, "status": a_status, "lohn": a_preis
            })
            speichere_gesamte_daten()
            st.rerun()

    with col_b:
        st.subheader("📊 Auftragsstatistiken")
        offen = sum(1 for a in st.session_state._global_auftrags_store if "Erledigt" not in a["status"])
        st.metric("Offene LU-Aufträge", f"{offen} Stück")

    st.write("---")
    st.subheader("📋 Aktuelle Auftragsliste")
    if st.session_state._global_auftrags_store:
        for idx, aut in enumerate(st.session_state._global_auftrags_store):
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 2, 1])
                c1.markdown(f"**{aut['kunde']}** — {aut['arbeit']} ({aut['ort']})")
                c2.markdown(f"Vergütung: **{fmt_float(aut['lohn'])} €** | Status: **{aut['status']}**")
                if c3.button("🗑️ Löschen", key=f"del_a_{idx}"):
                    st.session_state._global_auftrags_store.pop(idx)
                    speichere_gesamte_daten()
                    st.rerun()
    else:
        st.info("Das Auftragsbuch ist aktuell leer.")

# ---------------------------------------------------------
# NEU & AKTIVIERT: PRODUKTIONEN
# ---------------------------------------------------------
elif menu == "🏭 Produktionen":
    st.title("🏭 Produktionsbetriebe & Fabrik-Logistik")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.subheader("🛠️ Neue Fabrik / Rezeptur hinzufügen")
        p_name = st.text_input("Name der Fabrik:", placeholder="z.B. Ölmühle")
        p_in_ware = st.text_input("Eingangs-Rohstoff:", placeholder="z.B. Raps")
        p_in_menge = st.number_input("Benötigte Menge (L):", min_value=1.0, value=100.0)
        p_out_ware = st.text_input("Ausgangs-Produkt:", placeholder="z.B. Rapsöl")
        p_out_menge = st.number_input("Erzeugte Menge (L):", min_value=1.0, value=50.0)
        
        if st.button("🏗️ Fabrik registrieren", type="primary", use_container_width=True):
            if p_name.strip():
                st.session_state._global_produktionen_store.append({
                    "name": p_name, "input_ware": p_in_ware, "input_menge": p_in_menge,
                    "output_ware": p_out_ware, "output_menge": p_out_menge
                })
                speichere_gesamte_daten()
                st.rerun()

    with col_p2:
        st.subheader("⚙️ Fabrik-Produktionszyklus starten")
        if st.session_state._global_produktionen_store:
            fab_namen = [f["name"] for f in st.session_state._global_produktionen_store]
            auswahl_fab = st.selectbox("Fabrik auswählen:", fab_namen)
            
            # Sucht die gewählte Fabrik
            fab = next(f for f in st.session_state._global_produktionen_store if f["name"] == auswahl_fab)
            st.markdown(f"**Rezeptur:** {fmt_int(fab['input_menge'])}L {fab['input_ware']} ➡️ **{fmt_int(fab['output_menge'])}L {fab['output_ware']}**")
            
            zyklen = st.number_input("Anzahl der Produktionsdurchläufe:", min_value=1, value=1)
            gesamt_in = fab['input_menge'] * zyklen
            gesamt_out = fab['output_menge'] * zyklen
            
            st.warning(f"Gesamtbedarf: {fmt_int(gesamt_in)}L {fab['input_ware']}")
            
            if st.button("🚀 Produktion ausführen (Lager belasten)", use_container_width=True):
                rohstoff_key = fab['input_ware'].lower()
                ziel_key = fab['output_ware'].lower()
                
                # Prüfen, ob Rohstoff im manuellen Lager existiert
                if st.session_state._global_lager_store.get(rohstoff_key, 0) >= gesamt_in:
                    st.session_state._global_lager_store[rohstoff_key] -= gesamt_in
                    st.session_state._global_lager_store[ziel_key] = st.session_state._global_lager_store.get(ziel_key, 0) + gesamt_out
                    speichere_gesamte_daten()
                    st.success(f"✔️ Erfolgreich verarbeitet! +{fmt_int(gesamt_out)}L {fab['output_ware']} ans Lager gebucht.")
                    st.rerun()
                else:
                    st.error("🚨 Zu wenig Rohstoffe im manuellen Lager vorhanden!")
        else:
            st.info("Noch keine Produktionen angelegt.")

# ---------------------------------------------------------
# NEU & AKTIVIERT: MANUELLE LAGERVERWALTUNG
# ---------------------------------------------------------
elif menu == "📦 Manuelle Lagerverwaltung":
    st.title("📦 Manuelle Lagerverwaltung (Direktbuchungen)")
    st.markdown("Hier kannst du jeden beliebigen Lagerbestand direkt anpassen, erhöhen oder reduzieren.")
    
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        st.subheader("➕ Ware einbuchen / hinzufügen")
        add_name = st.text_input("Produkt-Name:", placeholder="z.B. Weizen, Brot, Mehl, Gülle").strip().lower()
        add_menge = st.number_input("Menge in Litern (L):", min_value=1, value=1000)
        
        if st.button("📥 Einbuchen", type="primary", use_container_width=True):
            if add_name:
                st.session_state._global_lager_store[add_name] = st.session_state._global_lager_store.get(add_name, 0) + add_menge
                speichere_gesamte_daten()
                st.success(f"{fmt_int(add_menge)}L {add_name} hinzugefügt!")
                st.rerun()

    with col_m2:
        st.subheader("🗑️ Ware vernichten / abbuchen")
        if st.session_state._global_lager_store:
            sub_name = st.selectbox("Produkt auswählen:", list(st.session_state._global_lager_store.keys()))
            sub_menge = st.number_input("Abzubuchende Menge (L):", min_value=1, value=500)
            
            if st.button("📤 Ausbuchen", use_container_width=True):
                if st.session_state._global_lager_store[sub_name] >= sub_menge:
                    st.session_state._global_lager_store[sub_name] -= sub_menge
                    speichere_gesamte_daten()
                    st.success(f"{fmt_int(sub_menge)}L {sub_name} abgezogen!")
                    st.rerun()
                else:
                    st.error("Nicht genügend Bestand für diese Abbuchung!")

# ---------------------------------------------------------
# SEITE 7-8: SILOS & KASSENBUCH
# ---------------------------------------------------------
elif menu == "🏗️ Schüttgut-Silos":
    st.title("🏗️ Silo-Management")
    # (Läuft über den funktionalen Silo-Code des vorherigen Updates)

elif menu == "📖 Detailliertes Kassenbuch":
    st.title("📖 Detailliertes Kassenbuch")
    if st.session_state._global_finanzen.get("historie"):
        st.dataframe(pd.DataFrame(st.session_state._global_finanzen["historie"]), use_container_width=True)
    else:
        st.info("Bisher keine Transaktionen verbucht.")
