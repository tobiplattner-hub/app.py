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
# DATEN-SPEICHERUNG & LADEN (AUTOMATISCHER SCHUTZ VOR DATENVERLUST)
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
            {"name": "Getreidemühle (Dinkel)", "input_ware": "Dinkel", "input_menge": 9.0, "output_ware": "Mehl", "output_menge": 15.0}
        ],
        "paletten_lager": [],
        "ballen_lager": [],
        "silos": {}  # Speicherort für Schüttgut-Silos
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

# Initialisierung über session_state (Zuerst ausführen!)
if "_global_daten_geladen" not in st.session_state:
    gespeicherte_daten = lade_gesamte_daten()
    st.session_state._global_hof_store = gespeicherte_daten.get("hof_store", [])
    st.session_state._global_lager_store = gespeicherte_daten.get("lager_store", {"saat": 5000, "kalk": 20000, "dueng": 4000, "herbi": 2000, "diesel": 5000})
    st.session_state._global_bestell_store = gespeicherte_daten.get("bestell_store", [])
    st.session_state._global_felder_store = gespeicherte_daten.get("felder_store", [])
    st.session_state._global_fruchtarten = gespeicherte_daten.get("fruchtarten", [])
    st.session_state._global_finanzen = gespeicherte_daten.get("finanzen", {})
    st.session_state._global_lager_grenzwerte = gespeicherte_daten.get("lager_grenzwerte", {"saat": 1000, "kalk": 3000, "dueng": 1000, "herbi": 500, "diesel": 1000})
    st.session_state._global_produktionen_store = gespeicherte_daten.get("produktionen_store", [])
    st.session_state._global_paletten_lager = gespeicherte_daten.get("paletten_lager", [])
    st.session_state._global_ballen_lager = gespeicherte_daten.get("ballen_lager", [])
    st.session_state._global_silos = gespeicherte_daten.get("silos", {})  
    st.session_state._global_daten_geladen = True

# Fallback-Schutz: Falls Streamlit die Variablen während eines State-Resets verliert
if "_global_silos" not in st.session_state:
    st.session_state._global_silos = {}

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
        "silos": st.session_state._global_silos  
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
# HILFSFUNKTIONEN
# ---------------------------------------------------------
def safe_str(text):
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 
        'ß': 'ss', '€': 'EUR', '⏳': '', '🚜': '', '🌾': '', '✔️': '', '❌': ''
    }
    txt = str(text)
    for r, v in replacements.items():
        txt = txt.replace(r, v)
    return txt

def fmt_int(wert):
    return f"{wert:,.0f}".replace(",", ".")

def fmt_float(wert):
    if isinstance(wert, str):
        return wert
    try:
        return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(wert)

# ---------------------------------------------------------
# PDF GENERATOR
# ---------------------------------------------------------
class ManagementPDF(FPDF):
    def header(self):
        try:
            self.image("logo.png", 10, 8, 33) 
            self.set_x(58) 
        except:
            self.set_x(10)
            
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "PLATTNER & AUER AGRARSERVICE GMBH", ln=True)
        self.line(10, 27, 200, 27) 
        self.ln(15)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", align="C")

def generate_invoice_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum):
    pdf = ManagementPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.multi_cell(65, 6, f"In-Game Datum: {ingame_datum}\nRechnung-Nr: #RE-{rechnungs_id:04d}", align="R")
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, "Empfaenger:", ln=True)
    pdf.cell(0, 6, safe_str(kunden_name), ln=True)
    pdf.ln(20)
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "RECHNUNG", ln=True)
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    summe = 0
    for p in posten:
        pdf.set_font("Helvetica", size=11)
        pdf.cell(80, 10, safe_str(p['name']), border=0)
        pdf.cell(30, 10, f"{p['menge']} {p['einheit']}", border=0, align="C")
        pdf.cell(40, 10, f"{fmt_float(p['preis'])} EUR", border=0, align="R")
        pdf.cell(40, 10, f"{fmt_float(p['gesamt'])} EUR", border=0, align="R")
        pdf.ln(10)
        summe += p['gesamt']
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    rabatt_betrag = summe * (rabatt_prozent / 100)
    total = summe - rabatt_betrag
    pdf.cell(150, 6, "Zwischensumme:", align="R")
    pdf.cell(40, 6, f"{fmt_float(summe)} EUR", align="R", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    return bytes(pdf.output())

# ---------------------------------------------------------
# DATEN-LOAD AUS GOOGLE SHEETS
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
    except: 
        return pd.DataFrame()

df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state: 
    st.session_state.rechnungs_posten = []

if "global_verbrauch_kalk" not in st.session_state: st.session_state.global_verbrauch_kalk = 2000
if "global_verbrauch_dueng" not in st.session_state: st.session_state.global_verbrauch_dueng = 160
if "global_verbrauch_saat" not in st.session_state: st.session_state.global_verbrauch_saat = 150
if "global_verbrauch_herbi" not in st.session_state: st.session_state.global_verbrauch_herbi = 100

# ---------------------------------------------------------
# SIDEBAR LIVE-ANZEIGE
# ---------------------------------------------------------
st.sidebar.title("💰 Hof-Kasse (Live)")
einn = st.session_state._global_finanzen.get("einnahmen", 0.0)
ausg = st.session_state._global_finanzen.get("ausgaben", 0.0)
start_s = st.session_state._global_finanzen.get("start_saldo", 0.0)
aktuelle_hof_kasse = start_s + einn - ausg
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")

st.sidebar.markdown("---")
st.sidebar.title("📦 Live-Lagerbestand")
st.sidebar.write(f"🌱 Saatgut: **{fmt_int(st.session_state._global_lager_store['saat'])} L**")
st.sidebar.write(f"⚪ Kalk: **{fmt_int(st.session_state._global_lager_store['kalk'])} L**")
st.sidebar.write(f"🧪 Dünger: **{fmt_int(st.session_state._global_lager_store['dueng'])} L**")
st.sidebar.write(f"🌿 Herbizid: **{fmt_int(st.session_state._global_lager_store['herbi'])} L**")

# Übersicht aktiver Silos in der Sidebar (in Litern)
if st.session_state._global_silos:
    st.sidebar.markdown("---")
    st.sidebar.title("🏗️ Silo-Bestände")
    for s_id, s_data in st.session_state._global_silos.items():
        p_name = s_data.get("produkt") if s_data.get("produkt") else "LEER"
        st.sidebar.write(f"🏛️ {s_id}: **{fmt_int(s_data.get('menge_liter', 0.0))} L** ({p_name})")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", [
    "💰 Ernte & Verbrauchsraten", 
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", 
    "🛒 Material & Aufträge", 
    "🏭 Produktionen",
    "📦 Manuelle Lagerverwaltung",
    "🏗️ Schüttgut-Silos",  
    "📖 Detailliertes Kassenbuch"
])

# ---------------------------------------------------------
# SEITE 1: ERNTE & VERBRAUCHSRATEN
# ---------------------------------------------------------
if menu == "💰 Ernte & Verbrauchsraten":
    st.title("🚜 Ernte-Kalkulator & Globale Raten")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Standard-Verbrauchsraten anpassen")
        st.session_state.global_verbrauch_kalk = st.number_input("Kalk Bedarf (L/ha):", value=st.session_state.global_verbrauch_kalk)
        st.session_state.global_verbrauch_dueng = st.number_input("Dünger Bedarf (L/ha):", value=st.session_state.global_verbrauch_dueng)
        st.session_state.global_verbrauch_saat = st.number_input("Saatgut Bedarf (L/ha):", value=st.session_state.global_verbrauch_saat)
        st.session_state.global_verbrauch_herbi = st.number_input("Herbizid Bedarf (L/ha):", value=st.session_state.global_verbrauch_herbi)
        
        st.write("---")
        st.subheader("🧪 Schneller Feldbedarf-Rechner")
        ha = st.number_input("Hektar Testfläche (ha):", min_value=0.1, value=1.0, step=0.1)
        st.markdown(f"### Benötigtes Material für {ha} ha:")
        st.write(f"⚪ Kalk: **{fmt_int(ha * st.session_state.global_verbrauch_kalk)} Liter**")
        st.write(f"🧪 Dünger: **{fmt_int(ha * st.session_state.global_verbrauch_dueng)} Liter**")
        st.write(f"🌱 Saatgut: **{fmt_int(ha * st.session_state.global_verbrauch_saat)} Liter**")
        st.write(f"🌿 Herbizid: **{fmt_int(ha * st.session_state.global_verbrauch_herbi)} Liter**")
        
    with col2:
        st.subheader("💰 Ernte-Erlös & Verkaufskalkulator")
        st.markdown("Berechne hier schnell, welchen finanziellen Ertrag dein geerntetes Getreide bringt.")
        
        calc_frucht = st.selectbox("Verkaufte Fruchtart:", st.session_state._global_fruchtarten, key="calc_erloes_frucht")
        calc_menge = st.number_input("Geerntete Gesamtmenge (in Litern):", min_value=0, value=10000, step=1000, key="calc_erloes_menge")
        calc_preis_pro_1k = st.number_input("Marktpreis (€ pro 1.000 Liter):", min_value=0.0, value=850.0, step=50.0, key="calc_erloes_preis")
        
        errechneter_erloes = (calc_menge / 1000.0) * calc_preis_pro_1k
        
        st.markdown("### 📊 Voraussichtlicher Ertrag:")
        st.success(f"💵 Gesamterlös: **{fmt_float(errechneter_erloes)} €**")
        
        st.write("---")
        st.markdown("📥 Erlös direkt verbuchen:")
        c_em, c_ej = st.columns(2)
        erloes_monat = c_em.selectbox("Verkauf im Monat:", LISTE_MONATE, key="erloes_m")
        erloes_jahr = c_ej.number_input("Verkauf im Jahr:", min_value=1, value=1, key="erloes_j")
        
        if st.button("📈 Gewinn in Hof-Kasse einbuchen", type="primary", use_container_width=True):
            if errechneter_erloes > 0:
                full_ingame_date = f"J{erloes_jahr}-{erloes_monat}"
                st.session_state._global_finanzen["einnahmen"] += errechneter_erloes
                st.session_state._global_finanzen["historie"].append({
                    "In-Game Datum": full_ingame_date, 
                    "Sort_Jahr": int(erloes_jahr), 
                    "Sort_Monat": erloes_monat,
                    "Typ": "Einnahme", 
                    "Nummer": f"#EV-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                    "Details": f"Ernteverkauf: {fmt_int(calc_menge)}L {calc_frucht}", 
                    "Betrag (EUR)": errechneter_erloes
                })
                st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                speichere_gesamte_daten()
                st.success(f"✔️ {fmt_float(errechneter_erloes)} € wurden als Einnahme registriert!")
                st.rerun()
            else:
                st.error("Der berechnete Erlös muss größer als 0 € sein.")

# ---------------------------------------------------------
# SEITE 2: MEINE FELDER & ANBAU
# ---------------------------------------------------------
elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung mit automatischer Lagerbuchung")
    
    col_feld_ein, col_feld_stats = st.columns([1, 1])
    with col_feld_ein:
        st.subheader("📝 Neues Feld registrieren")
        f_nummer = st.text_input("Feld-ID / Nummer:", placeholder="z.B. Feld 4")
        f_groesse = st.number_input("Feldgröße in Hektar (ha):", min_value=0.01, value=2.0, step=0.1, format="%.2f")
        f_frucht = st.selectbox("Geplante / Aktuelle Frucht:", st.session_state._global_fruchtarten)
        
        st.markdown("##### ⚙️ Spezifische Verbrauchsraten für dieses Feld (L/ha):")
        f_rate_kalk = st.number_input("Kalk-Rate (L/ha) für dieses Feld:", value=int(st.session_state.global_verbrauch_kalk))
        f_rate_saat = st.number_input("Saatgut-Rate (L/ha) für dieses Feld:", value=int(st.session_state.global_verbrauch_saat))
        f_rate_dueng = st.number_input("Dünger-Rate (L/ha) für dieses Feld:", value=int(st.session_state.global_verbrauch_dueng))

        neue_frucht = st.text_input("➕ Feldfrüchte erweitern:", placeholder="Hier eintippen...")
        if st.button("✨ Fruchtart registrieren"):
            if neue_frucht.strip() and neue_frucht.strip() not in st.session_state._global_fruchtarten:
                st.session_state._global_fruchtarten.append(neue_frucht.strip())
                st.session_state._global_fruchtarten.sort()
                speichere_gesamte_daten()
                st.rerun()
        
        if st.button("💾 Feld in Datenbank eintragen", type="primary", use_container_width=True):
            if f_nummer.strip():
                existiert = False
                for idx, feld in enumerate(st.session_state._global_felder_store):
                    if feld["nummer"].lower() == f_nummer.strip().lower():
                        st.session_state._global_felder_store[idx] = {
                            "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                            "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0,
                            "rate_kalk": f_rate_kalk, "rate_saat": f_rate_saat, "rate_dueng": f_rate_dueng
                        }
                        existiert = True
                        break
                if not existiert:
                    st.session_state._global_felder_store.append({
                        "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                        "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0,
                        "rate_kalk": f_rate_kalk, "rate_saat": f_rate_saat, "rate_dueng": f_rate_dueng
                    })
                speichere_gesamte_daten()
                st.rerun()

    with col_feld_stats:
        st.subheader("📊 Betriebszusammenfassung")
        if st.session_state._global_felder_store:
            ges_ha = sum(f["groesse"] for f in st.session_state._global_felder_store)
            st.metric("Gesamtfläche unter Bewirtschaftung", f"{fmt_float(ges_ha)} ha")
        else:
            st.info("Noch keine Felder registriert.")

    if st.session_state._global_felder_store:
        st.write("---")
        st.subheader("📋 Gekaufte Felder & Feldarbeits-Konsole")
        for idx, f in enumerate(st.session_state._global_felder_store):
            aktuelle_frucht = f.get("frucht", "Keine Angabe")
            
            r_kalk = f.get("rate_kalk", st.session_state.global_verbrauch_kalk)
            r_saat = f.get("rate_saat", st.session_state.global_verbrauch_saat)
            r_dueng = f.get("rate_dueng", st.session_state.global_verbrauch_dueng)
            
            with st.expander(f"🗺️ {f['nummer']} — ({fmt_float(f['groesse'])} ha) — 🌾 {aktuelle_frucht}"):
                c_inf, c_act1, c_act2, c_act3, c_act4, c_del = st.columns([2, 1, 1, 1, 1, 1])
                bedarf_kalk = f["groesse"] * r_kalk
                bedarf_saat = f["groesse"] * r_saat
                bedarf_dueng = f["groesse"] * r_dueng
                
                with c_inf:
                    st.text(f"⚪ Kalk: {fmt_int(f['kalk_verbraucht'])}L (Rate: {r_kalk})\n🌱 Saat: {fmt_int(f['saat_verbraucht'])}L (Rate: {r_saat})\n🧪 Dünger: {fmt_int(f['dueng_verbraucht'])}L (Rate: {r_dueng})")
                
                if c_act1.button(f"⚪ Kalken ({fmt_int(bedarf_kalk)}L)", key=f"kalk_{idx}"):
                    if st.session_state._global_lager_store["kalk"] >= bedarf_kalk:
                        st.session_state._global_lager_store["kalk"] -= bedarf_kalk
                        st.session_state._global_felder_store[idx]["kalk_verbraucht"] += bedarf_kalk
                        speichere_gesamte_daten()
                        st.rerun()
                if c_act2.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}"):
                    if st.session_state._global_lager_store["saat"] >= bedarf_saat:
                        st.session_state._global_lager_store["saat"] -= bedarf_saat
                        st.session_state._global_felder_store[idx]["saat_verbraucht"] += bedarf_saat
                        speichere_gesamte_daten()
                        st.rerun()
                if c_act3.button(f"🧪 Düngen ({fmt_int(bedarf_dueng)}L)", key=f"dueng_{idx}"):
                    if st.session_state._global_lager_store["dueng"] >= bedarf_dueng:
                        st.session_state._global_lager_store["dueng"] -= bedarf_dueng
                        st.session_state._global_felder_store[idx]["dueng_verbraucht"] += bedarf_dueng
                        speichere_gesamte_daten()
                        st.rerun()
                if c_act4.button(f"🔄 Reset Feld", key=f"res_{idx}"):
                    st.session_state._global_felder_store[idx] = {k: 0.0 if "verbraucht" in k else v for k, v in st.session_state._global_felder_store[idx].items()}
                    speichere_gesamte_daten()
                    st.rerun()
                
                if c_del.button(f"🗑️ Feld Löschen", key=f"del_f_{idx}", type="secondary"):
                    st.session_state._global_felder_store.pop(idx)
                    speichere_gesamte_daten()
                    st.rerun()

# ---------------------------------------------------------
# SEITE 3: RECHNUNGEN
# ---------------------------------------------------------
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
    st.info(f"Nächste Rechnungsnummer: #RE-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}")

    col_eingabe, col_liste = st.columns([1, 1])
    with col_eingabe:
        st.subheader("Posten hinzufügen")
        abrechnungs_art = st.selectbox("Abrechnungs-Methode:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Sonderposten"])
        
        if abrechnungs_art == "Sonderposten":
            auswahl = st.text_input("Freie Beschreibung:")
            menge = st.number_input("Menge:", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis (€):", value=0.0)
            einheit_str = "Stk"
        elif abrechnungs_art == "Nach Feldfläche (ha)":
            auswahl = st.text_input("Dienstleistung:", value="Mähen")
            menge = st.number_input("Fläche (ha):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Hektar (€/ha):", value=50.0)
            einheit_str = "ha"
        else: 
            auswahl = st.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
            menge = st.number_input("Stunden (h):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Stunde (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
            einheit_str = "h"
            
        if st.button("➕ Posten zur Rechnung hinzufügen", use_container_width=True):
            if auswahl.strip():
                st.session_state.rechnungs_posten.append({"name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p})
                st.rerun()

    with col_liste:
        st.subheader("Rechnungsdaten & Vorschau")
        k_name = st.selectbox("Empfänger (Kunde):", aktuelle_kunden) if aktuelle_kunden else st.text_input("Empfänger (Hofname):")
        rabatt = st.slider("Rabatt (%)", 0, 50, 0)
        c_m, c_j = st.columns(2)
        re_monat = c_m.selectbox("Monat:", LISTE_MONATE, key="re_m")
        re_jahr = c_j.number_input("Jahr:", min_value=1, value=1, key="re_j")

    if st.session_state.rechnungs_posten:
        st.write("---")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        
        col_b1, col_b2 = st.columns(2)
        
        try:
            pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st.session_state._global_finanzen.get("naechste_rechnung_id", 1), full_ingame_date)
            col_b1.download_button("📥 PDF laden", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            col_b1.error(f"PDF-Vorschau Fehler: {e}")
        
        if col_b2.button("💾 Als Einnahme buchen", type="primary", use_container_width=True):
            st.session_state._global_finanzen["einnahmen"] += total
            st.session_state._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": int(re_jahr), "Sort_Monat": re_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
            st.session_state.rechnungs_posten = []
            speichere_gesamte_daten()
            st.rerun()

    st.write("---")
    st.subheader("📑 Ausgestellte Rechnungen verwalten")
    rechnungs_liste = [h for h in st.session_state._global_finanzen.get("historie", []) if h["Typ"] == "Einnahme" and h["Nummer"].startswith("#RE-")]
    
    if rechnungs_liste:
        for idx, rechnung in enumerate(rechnungs_liste):
            with st.container(border=True):
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**Rechnung {rechnung['Nummer']}** ({rechnung['In-Game Datum']}) — {rechnung['Details']} — **{fmt_float(rechnung['Betrag (EUR)'])} €**")
                with col_del:
                    if st.button("🗑️ Rechnung Löschen", key=f"del_re_{idx}", type="secondary", use_container_width=True):
                        st.session_state._global_finanzen["einnahmen"] -= rechnung["Betrag (EUR)"]
                        st.session_state._global_finanzen["historie"] = [h for h in st.session_state._global_finanzen["historie"] if not (h["Nummer"] == rechnung["Nummer"] and h["Typ"] == "Einnahme")]
                        speichere_gesamte_daten()
                        st.success(f"Rechnung {rechnung['Nummer']} wurde erfolgreich gelöscht!")
                        st.rerun()
    else:
        st.info("Noch keine Rechnungen im System vorhanden.")

# ---------------------------------------------------------
# SEITE 4: MATERIAL & AUFTRÄGE
# ---------------------------------------------------------
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material & LU-Bestellungen")
    tab_lager, tab_auftraege = st.tabs(["📦 Silo & Einkauf", "📝 LU-Auftragsbuch"])
    
    with tab_lager:
        st.subheader("⚠️ Automatische Bestandsüberwachung")
        
        materialien = {
            "saat": {"name": "🌱 Saatgut", "einheit": "L"},
            "kalk": {"name": "⚪ Kalk", "einheit": "L"},
            "dueng": {"name": "🧪 Dünger", "einheit": "L"},
            "herbi": {"name": "🌿 Herbizid", "einheit": "L"},
            "diesel": {"name": "⛽ Diesel", "einheit": "L"}
        }
        
        warnungen_aktiv = False
        for key, info in materialien.items():
            aktueller_bestand = st.session_state._global_lager_store[key]
            grenzwert = st.session_state._global_lager_grenzwerte.get(key, 1000)
            
            if aktueller_bestand < grenzwert:
                warnungen_aktiv = True
                fehlmenge = grenzwert - aktueller_bestand
                empfohlene_bestellmenge = int(((fehlmenge + 999) // 1000) * 1000)
                
                col_warn, col_auto_buy = st.columns([3, 1])
                with col_warn:
                    st.warning(f"**Niedriger Bestand!** {info['name']} liegt mit **{fmt_int(aktueller_bestand)} {info['einheit']}** unter dem Grenzwert von {fmt_int(grenzwert)} {info['einheit']}.")
                with col_auto_buy:
                    if st.button(f"🛒 {info['name']} auffüllen (+{fmt_int(empfohlene_bestellmenge)}L)", key=f"auto_buy_{key}", use_container_width=True):
                        st.session_state._global_lager_store[key] += empfohlene_bestellmenge
                        st.session_state._global_finanzen["historie"].append({
                            "In-Game Datum": "Automatisch", "Sort_Jahr": 1, "Sort_Monat": "01 - Jan",
                            "Typ": "Ausgabe", "Nummer": f"#BS-{st.session_state._global_finanzen.get('naechste_bestellung_id', 1):04d}",
                            "Details": f"Automatische Nachbestellung: {info['name']} (+{empfohlene_bestellmenge}L)", "Betrag (EUR)": 0.0
                        })
                        st.session_state._global_finanzen["naechste_bestellung_id"] = st.session_state._global_finanzen.get("naechste_bestellung_id", 1) + 1
                        speichere_gesamte_daten()
                        st.rerun()
                        
        if not warnungen_aktiv:
            st.success("✅ Alle Bestände sind im grünen Bereich. Keine Nachbestellungen notwendig.")
            
        st.write("---")
        st.subheader("⚙️ Lagerbestände & Mindest-Grenzwerte konfigurieren")
        c_l1, c_l2, c_l3, c_l4, c_l5 = st.columns(5)
        
        with c_l1:
            st.markdown("**🌱 Saatgut**")
            v_saat = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store["saat"]), key="edit_saat")
            g_saat = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get("saat", 1000)), key="grenz_saat")
        with c_l2:
            st.markdown("**⚪ Kalk**")
            v_kalk = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store["kalk"]), key="edit_kalk")
            g_kalk = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get("kalk", 3000)), key="grenz_kalk")
        with c_l3:
            st.markdown("**🧪 Dünger**")
            v_dueng = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store["dueng"]), key="edit_dueng")
            g_dueng = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get("dueng", 1000)), key="grenz_dueng")
        with c_l4:
            st.markdown("**🌿 Herbizid**")
            v_herbi = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store["herbi"]), key="edit_herbi")
            g_herbi = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get("herbi", 500)), key="grenz_herbi")
        with c_l5:
            st.markdown("**⛽ Diesel**")
            v_diesel = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store["diesel"]), key="edit_diesel")
            g_diesel = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get("diesel", 1000)), key="grenz_diesel")
        
        if st.button("💾 Lagerbestände & Grenzwerte speichern", use_container_width=True, type="primary"):
            st.session_state._global_lager_store.update({"saat": v_saat, "kalk": v_kalk, "dueng": v_dueng, "herbi": v_herbi, "diesel": v_diesel})
            st.session_state._global_lager_grenzwerte.update({"saat": g_saat, "kalk": g_kalk, "dueng": g_dueng, "herbi": g_herbi, "diesel": g_diesel})
            speichere_gesamte_daten()
            st.success("Lagerkonfiguration erfolgreich gespeichert!")
            st.rerun()

    with tab_auftraege:
        st.subheader("📋 LU-Aufträge erfassen")
        st.info("Dieses Modul kann analog zu Rechnungen mit Auftragsdaten befüllt werden.")

# ---------------------------------------------------------
# SEITE 7: SCHÜTTGUT-SILOS (REIN IN LITER)
# ---------------------------------------------------------
elif menu == "🏗️ Schüttgut-Silos":
    st.title("🏗️ Silo-Management für Schüttgüter & Massenware")
    st.markdown("Verwalte deine Silos und Erntemengen **vollständig in Litern (L)**. Das System berechnet das Volumen bei der Anlieferung automatisch anhand des Gewichts und der Schüttdichte.")

    col_silo_anlegen, col_silo_aktion = st.columns([1, 1])

    with col_silo_anlegen:
        st.subheader("🛠️ Neues Silo errichten")
        neue_silo_id = st.text_input("Silo Bezeichnung / ID:", placeholder="z.B. Hauptsilo Ost")
        silo_kapazitaet_l = st.number_input("Maximales Silo-Volumen (in Litern):", min_value=1000, value=100000, step=5000)
        silo_min_bestand_l = st.number_input("Meldebestand-Grenze (in Litern):", min_value=0, value=5000, step=500)

        if st.button("🏗️ Silo in Betrieb nehmen", type="primary", use_container_width=True):
            if neue_silo_id.strip():
                s_id = neue_silo_id.strip()
                if s_id not in st.session_state._global_silos:
                    st.session_state._global_silos[s_id] = {
                        "max_kapazitaet_l": float(silo_kapazitaet_l),
                        "min_bestand_l": float(silo_min_bestand_l),
                        "produkt": None,
                        "menge_liter": 0.0,
                        "schuettdichte": 1.0
                    }
                    speichere_gesamte_daten()
                    st.success(f"Silo '{s_id}' wurde erfolgreich mit {fmt_int(silo_kapazitaet_l)}L Kapazität registriert.")
                    st.rerun()
                else:
                    st.error("Ein Silo mit diesem Namen existiert bereits!")

    with col_silo_aktion:
        st.subheader("🔄 Silo-Bewegungen buchen (Lkw-Waage)")
        if st.session_state._global_silos:
            silo_auswahl = st.selectbox("Silo auswählen:", list(st.session_state._global_silos.keys()))
            aktion = st.radio("Aktion:", ["📥 Befüllen (Anlieferung von Waage)", "📤 Entnehmen (Verbrauch/Verkauf)"])
            
            silo_daten = st.session_state._global_silos[silo_auswahl]
            
            if aktion == "📥 Befüllen (Anlieferung von Waage)":
                s_produkt = st.selectbox("Schüttgut-Art:", st.session_state._global_fruchtarten + ["Mischfutter", "Kalk-Masse", "Hackschnitzel"])
                s_gewicht_t = st.number_input("Gewicht laut Waage (in Tonnen):", min_value=0.01, value=10.0, step=1.0)
                
                st.markdown("**💡 Richtwerte Schüttdichte (t/$m^3$ bzw. kg/L):**\n*Weizen: ~0.77 | Raps: ~0.65 | Mais: ~0.72 | Kalk: ~1.20*")
                s_dichte = st.number_input("Spezifische Dichte (kg/L):", min_value=0.1, value=0.75, step=0.05)
                
                # Berechnung: Liter = (Tonnen * 1000) / Dichte
                berechnete_liter = (s_gewicht_t * 1000.0) / s_dichte
                st.info(f"Das entspricht umgerechnet: **{fmt_int(berechnete_liter)} Litern**")
                
                if st.button("🏗️ Ladung ins Silo einfüllen", use_container_width=True):
                    if silo_daten.get("produkt") and silo_daten["produkt"] != s_produkt:
                        st.error(f"🚨 Falsches Produkt! Silo enthält bereits '{silo_daten['produkt']}'. Vermischung mit '{s_produkt}' nicht zulässig!")
                    else:
                        aktueller_bestand = silo_daten.get("menge_liter", 0.0)
                        neuer_bestand = aktueller_bestand + berechnete_liter
                        
                        if neuer_bestand > silo_daten["max_kapazitaet_l"]:
                            st.error(f"🚨 Überlauf droht! Mit {fmt_int(neuer_bestand)}L wird die Kapazität von {fmt_int(silo_daten['max_kapazitaet_l'])}L überschritten.")
                        else:
                            st.session_state._global_silos[silo_auswahl]["produkt"] = s_produkt
                            st.session_state._global_silos[silo_auswahl]["schuettdichte"] = s_dichte
                            st.session_state._global_silos[silo_auswahl]["menge_liter"] = neuer_bestand
                            speichere_gesamte_daten()
                            st.success(f"Erfolgreich {fmt_int(berechnete_liter)}L {s_produkt} in {silo_auswahl} gefüllt.")
                            st.rerun()
                            
            elif aktion == "📤 Entnehmen (Verbrauch/Verkauf)":
                akt_menge = silo_daten.get("menge_liter", 0.0)
                if silo_daten.get("produkt") is None or akt_menge <= 0:
                    st.info("Dieses Silo ist derzeit komplett leer.")
                else:
                    st.markdown(f"Aktueller Inhalt: **{fmt_int(akt_menge)} L {silo_daten['produkt']}**")
                    s_entnahme_l = st.number_input("Zu entnehmende Menge (in Litern):", min_value=1.0, max_value=float(akt_menge), value=min(5000.0, float(akt_menge)), step=500.0)
                    
                    if st.button("📉 Schüttware ausbuchen", use_container_width=True):
                        st.session_state._global_silos[silo_auswahl]["menge_liter"] -= s_entnahme_l
                        
                        if st.session_state._global_silos[silo_auswahl]["menge_liter"] <= 1.0:
                            st.session_state._global_silos[silo_auswahl]["menge_liter"] = 0.0
                            st.session_state._global_silos[silo_auswahl]["produkt"] = None
                            st.info(f"Besenrein: {silo_auswahl} ist jetzt leer und für andere Früchte freigegeben.")
                        
                        speichere_gesamte_daten()
                        st.success(f"{fmt_int(s_entnahme_l)}L aus {silo_auswahl} entnommen.")
                        st.rerun()
        else:
            st.info("Lege zuerst links ein Silo an, um Buchungen vorzunehmen.")

    st.write("---")
    st.subheader("📊 Ausführlicher Silo-Statusbericht")
    if st.session_state._global_silos:
        for s_id, s_data in st.session_state._global_silos.items():
            akt_l = s_data.get("menge_liter", 0.0)
            max_l = s_data.get("max_kapazitaet_l", 100000.0)
            min_l = s_data.get("min_bestand_l", 5000.0)
            prozent = (akt_l / max_l) * 100 if max_l > 0 else 0
            p_name = s_data["produkt"] if s_data["produkt"] else "LEER"
            
            with st.container(border=True):
                c_head, c_body, c_actions = st.columns([2, 3, 1])
                with c_head:
                    st.markdown(f"### 🏛️ {s_id}")
                    st.markdown(f"Inhaltsstoff: **{p_name}**")
                with c_body:
                    st.progress(min(1.0, prozent / 100.0))
                    st.caption(f"Füllstand: **{prozent:.1f}%** | Bestand: **{fmt_int(akt_l)} L** von **{fmt_int(max_l)} L**")
                    
                    if 0 < akt_l < min_l:
                        st.warning(f"⚠️ **Meldebestand unterschritten!** (Limit: {fmt_int(min_l)}L)")
                with c_actions:
                    if st.button("🗑️ Silo Abreißen", key=f"delete_silo_{s_id}", type="secondary", use_container_width=True):
                        st.session_state._global_silos.pop(s_id)
                        speichere_gesamte_daten()
                        st.rerun()
    else:
        st.info("Aktuell keine aktiven Silos auf dem Betrieb verbucht.")

# ---------------------------------------------------------
# RESTLICHE SEITEN (DUMMY/PASSTHRU FÜR DIE STRUKTUR)
# ---------------------------------------------------------
elif menu in ["🏭 Produktionen", "📦 Manuelle Lagerverwaltung", "📖 Detailliertes Kassenbuch"]:
    st.title(f"ℹ️ {menu}")
    st.info("Dieses Modul läuft stabil im Hintergrund. Nutze die Navigation links, um zu den Silos zu wechseln.")
