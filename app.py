import streamlit as set_page_config
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
            "Pappel", "Zuckerrohr", "Baumwolle", "Reis", "Langkornreis", "Spinat"
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
        "produktionen_store": [],
        "paletten_lager": {}
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
        "paletten_lager": st.session_state._global_paletten_lager
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(daten_zum_speichern, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fehler beim Sichern: {e}")

# Initialisierung über session_state
if "_global_daten_geladen" not in st.session_state:
    gespeicherte_daten = lade_gesamte_daten()
    st.session_state._global_hof_store = gespeicherte_daten["hof_store"]
    st.session_state._global_lager_store = gespeicherte_daten["lager_store"]
    st.session_state._global_bestell_store = gespeicherte_daten["bestell_store"]
    st.session_state._global_felder_store = gespeicherte_daten["felder_store"]
    st.session_state._global_fruchtarten = gespeicherte_daten["fruchtarten"]
    st.session_state._global_finanzen = gespeicherte_daten["finanzen"]
    st.session_state._global_lager_grenzwerte = gespeicherte_daten.get("lager_grenzwerte", {"saat": 1000, "kalk": 3000, "dueng": 1000, "herbi": 500, "diesel": 1000})
    st.session_state._global_produktionen_store = gespeicherte_daten.get("produktionen_store", [])
    st.session_state._global_paletten_lager = gespeicherte_daten.get("paletten_lager", {})
    st.session_state._global_daten_geladen = True

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

def generate_single_order_pdf(auftrag):
    pdf = ManagementPDF()
    pdf.add_page()
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, "LU-AUFTRAGSBELEG / BESTELLUNG", ln=True)
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 8, "Kunde / Hofname:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag["Kunde"]), border=0, ln=True)
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 8, "In-Game Datum:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag["Eingang"]), border=0, ln=True)
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 8, "Vereinbarter Preis:", border=0)
    pdf.set_font("Helvetica", size=12)
    auftrags_preis = auftrag.get("Preis", 0.0)
    pdf.cell(0, 8, f"{fmt_float(auftrags_preis)} EUR", border=0, ln=True)
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(50, 8, "Aktueller Status:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag["Status"]), border=0, ln=True)
    
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Arbeitsbeschreibung / Details:", ln=True)
    pdf.ln(2)
    pdf.set_x(65)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, safe_str(auftrag["Aufgabe"]))
    
    pdf.ln(20)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, "Generiert via LS25 Hof-Manager. Zur Abrechnung bitte das Rechnungs-Tool nutzen.", ln=True, align="C")
    
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
einn = st.session_state._global_finanzen["einnahmen"]
ausg = st.session_state._global_finanzen["ausgaben"]
aktuelle_hof_kasse = st.session_state._global_finanzen["start_saldo"] + einn - ausg
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")

st.sidebar.markdown("---")
st.sidebar.title("📦 Live-Lagerbestand")
st.sidebar.write(f"🌱 Saatgut: **{fmt_int(st.session_state._global_lager_store['saat'])} L**")
st.sidebar.write(f"⚪ Kalk: **{fmt_int(st.session_state._global_lager_store['kalk'])} L**")
st.sidebar.write(f"🧪 Dünger: **{fmt_int(st.session_state._global_lager_store['dueng'])} L**")
st.sidebar.write(f"🌿 Herbizid: **{fmt_int(st.session_state._global_lager_store['herbi'])} L**")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", [
    "💰 Ernte & Verbrauchsraten", 
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", 
    "🛒 Material & Aufträge", 
    "🏭 Produktionen",
    "📦 Manuelle Lagerverwaltung",
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
        
        # Berechnung des Gewinns
        errechneter_erloes = (calc_menge / 1000.0) * calc_preis_pro_1k
        
        st.markdown("### 📊 Voraussichtlicher Ertrag:")
        st.success(f"💵 Gesamterlös: **{fmt_float(errechneter_erloes)} €**")
        
        st.write("---")
        st.markdown("##### 📥 Erlös direkt verbuchen:")
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
                    "Nummer": f"#EV-{st.session_state._global_finanzen['naechste_rechnung_id']:04d}",
                    "Details": f"Ernteverkauf: {fmt_int(calc_menge)}L {calc_frucht}", 
                    "Betrag (EUR)": errechneter_erloes
                })
                st.session_state._global_finanzen["naechste_rechnung_id"] += 1
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
    st.info(f"Nächste Rechnungsnummer: #RE-{st.session_state._global_finanzen['naechste_rechnung_id']:04d}")

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
            pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st.session_state._global_finanzen["naechste_rechnung_id"], full_ingame_date)
            col_b1.download_button("📥 PDF laden", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as e:
            col_b1.error(f"PDF-Vorschau Fehler: {e}")
        
        if col_b2.button("💾 Als Einnahme buchen", type="primary", use_container_width=True):
            st.session_state._global_finanzen["einnahmen"] += total
            st.session_state._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": int(re_jahr), "Sort_Monat": re_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st.session_state._global_finanzen['naechste_rechnung_id']:04d}",
                "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st.session_state._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            speichere_gesamte_daten()
            st.rerun()

    st.write("---")
    st.subheader("📑 Ausgestellte Rechnungen verwalten")
    rechnungs_liste = [h for h in st.session_state._global_finanzen["historie"] if h["Typ"] == "Einnahme" and h["Nummer"].startswith("#RE-")]
    
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
                            "Typ": "Ausgabe", "Nummer": f"#BS-{st.session_state._global_finanzen['naechste_bestellung_id']:04d}",
                            "Details": f"Automatische Nachbestellung: {info['name']} (+{empfohlene_bestellmenge}L)", "Betrag (EUR)": 0.0
                        })
                        st.session_state._global_finanzen["naechste_bestellung_id"] += 1
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
            st.rerun()
            
        st.write("---")
        st.subheader("📉 Reiner Material-Einkaufswagen")
        order_saat = st.number_input("Saatgut kaufen (L):", min_value=0, step=1000, value=0)
        if st.button("🛒 Einkaufswagen verbuchen"):
            if order_saat > 0:
                st.session_state._global_lager_store["saat"] += order_saat
                speichere_gesamte_daten()
                st.success(f"{order_saat}L Saatgut gekauft!")
                st.rerun()

    with tab_auftraege:
        st.subheader("📝 LU-Auftragsbuch")
        k_name = st.text_input("Kunde / Hofname für Auftrag:")
        aufgabe = st.text_area("Aufgabenbeschreibung:")
        preis = st.number_input("Vereinbarter Preis (€):", min_value=0.0, value=0.0)
        
        if st.button("💾 Auftrag registrieren"):
            if k_name and aufgabe:
                st.session_state._global_bestell_store.append({
                    "Kunde": k_name, "Aufgabe": aufgabe, "Preis": preis, "Status": "Offen", "Eingang": str(date.today())
                })
                speichere_gesamte_daten()
                st.success("Auftrag hinzugefügt!")
                st.rerun()

        if st.session_state._global_bestell_store:
            st.write("---")
            for idx, a in enumerate(st.session_state._global_bestell_store):
                st.write(f"**{a['Kunde']}**: {a['Aufgabe']} ({fmt_float(a['Preis'])} €) - Status: {a['Status']}")

# ---------------------------------------------------------
# SEITE 5: PRODUKTIONEN (VEREINFACHTE KALKULATION)
# ---------------------------------------------------------
elif menu == "🏭 Produktionen":
    st.title("🏭 Produktions-Bedarfsrechner (Vereinfachte Kalkulation)")
    st.info("Hier kannst du berechnen, wie viel Rohware du für dein jährliches Produktionsziel benötigst. Es erfolgt keine automatische Lagerbuchung.")

    col_prod_ein, col_prod_liste = st.columns([1, 1])
    
    with col_prod_ein:
        st.subheader("➕ Neues Rezept kalkulieren")
        p_name = st.text_input("Name der Produktion:", placeholder="z.B. Ölmühle, Bäckerei")
        p_ziel = st.number_input("Jährliches Produktionsziel (Ausgabe in Liter):", min_value=1, value=10000, step=1000)
        
        st.markdown("##### 🌾 Benötigte Rohwaren pro 1.000L Fertigprodukt:")
        rohstoff_1 = st.text_input("Rohstoff 1 Name:", placeholder="z.B. Raps")
        rohstoff_1_bedarf = st.number_input("Bedarf für 1.000L Produkt (in Litern):", min_value=1, value=2000, step=100)
        
        rohstoff_2 = st.text_input("Rohstoff 2 Name (Optional):", placeholder="z.B. Wasser")
        rohstoff_2_bedarf = st.number_input("Bedarf für 1.000L Produkt (Optional):", min_value=0, value=0, step=100)

        if st.button("💾 Rezept speichern & berechnen", type="primary", use_container_width=True):
            if p_name.strip() and rohstoff_1.strip():
                # Alten Speicher säubern falls vorhanden und neu anhängen
                st.session_state._global_produktionen_store.append({
                    "name": p_name.strip(),
                    "ziel": p_ziel,
                    "r1_name": rohstoff_1.strip(),
                    "r1_bedarf": rohstoff_1_bedarf,
                    "r2_name": rohstoff_2.strip() if rohstoff_2.strip() else None,
                    "r2_bedarf": rohstoff_2_bedarf
                })
                speichere_gesamte_daten()
                st.rerun()

    with col_prod_liste:
        st.subheader("📋 Kalkulierte Jahrestrends & Rezepte")
        if not st.session_state._global_produktionen_store:
            st.info("Noch keine Produktionen zur Kalkulation angelegt.")
        else:
            for idx, prod in enumerate(st.session_state._global_produktionen_store):
                faktor = prod["ziel"] / 1000.0
                j_bedarf_1 = faktor * prod["r1_bedarf"]
                
                with st.container(border=True):
                    st.markdown(f"### 🏭 {prod['name']}")
                    st.markdown(f"**Geplante Jahresproduktion:** {fmt_int(prod['ziel'])} Liter")
                    st.write(f"Required **{prod['r1_name']}** pro Jahr: **{fmt_int(j_bedarf_1)} L** (Basis: {prod['r1_bedarf']}L/1k)")
                    
                    if prod.get("r2_name"):
                        j_bedarf_2 = faktor * prod["r2_bedarf"]
                        st.write(f"Required **{prod['r2_name']}** pro Jahr: **{fmt_int(j_bedarf_2)} L** (Basis: {prod['r2_bedarf']}L/1k)")
                    
                    if st.button("🗑️ Kalkulation löschen", key=f"del_prod_{idx}"):
                        st.session_state._global_produktionen_store.pop(idx)
                        speichere_gesamte_daten()
                        st.rerun()

# ---------------------------------------------------------
# NEUE SEITE 6: MANUELLE LAGERVERWALTUNG
# ---------------------------------------------------------
elif menu == "📦 Manuelle Lagerverwaltung":
    st.title("📦 Manuelle Lagerverwaltung")
    st.markdown("Hier kannst du Paletten, Ballen und sonstige Güter manuell erfassen. Die Umrechnung in Liter erfolgt vollautomatisch.")

    # Formular zum Hinzufügen von Beständen
    col_input, col_view = st.columns([1, 1])
    
    with col_input:
        st.subheader("📥 Neuen Posten einlagern")
        typ_auswahl = st.selectbox("Ladungsträger Typ:", ["Palette (1.000 L)", "Silageballen (Variabel)", "Strohballen (Variabel)", "Eck-Paletten (1.000 L)", "Stückgut / Sonstiges"])
        name_gut = st.text_input("Inhalt / Name des Guts:", placeholder="z.B. Siliermittel, Erdbeeren, Wolle")
        anzahl = st.number_input("Anzahl / Menge (Stück):", min_value=1, value=1, step=1)
        
        # Liter Logik je nach Auswahl
        if "Palette" in typ_auswahl or "Eck" in typ_auswahl:
            liter_pro_einheit = 1000
            st.disabled = True
            st.info("Einheit fix auf 1.000 Liter gesetzt.")
        else:
            liter_pro_einheit = st.number_input("Größe in Liter pro Stück/Ballen:", min_value=1, value=1200, step=100)

        if st.button("💾 Bestand manuell einbuchen", type="primary", use_container_width=True):
            if name_gut.strip():
                schluessel = name_gut.strip()
                gesamt_liter = anzahl * liter_pro_einheit
                
                # Prüfen ob Gut bereits existiert, falls ja, addieren
                if schluessel in st.session_state._global_paletten_lager:
                    st.session_state._global_paletten_lager[schluessel]["anzahl"] += anzahl
                    st.session_state._global_paletten_lager[schluessel]["gesamt_liter"] += gesamt_liter
                else:
                    st.session_state._global_paletten_lager[schluessel] = {
                        "typ": typ_auswahl,
                        "anzahl": anzahl,
                        "liter_pro_stk": liter_pro_einheit,
                        "gesamt_liter": gesamt_liter
                    }
                speichere_gesamte_daten()
                st.success(f"{anzahl}x {schluessel} erfolgreich verbucht!")
                st.rerun()

    with col_view:
        st.subheader("📋 Aktuelle Bestandsliste (Manuell)")
        if not st.session_state._global_paletten_lager:
            st.info("Das manuelle Lager ist aktuell leer.")
        else:
            # Tabelle rendern
            lager_daten = []
            for k, v in st.session_state._global_paletten_lager.items():
                lager_daten.append({
                    "Ware": k,
                    "Typ": v["typ"],
                    "Anzahl (Stk)": fmt_int(v["anzahl"]),
                    "Liter / Stück": fmt_int(v["liter_pro_stk"]),
                    "Gesamt-Volumen": f"{fmt_int(v['gesamt_liter'])} L"
                })
            df_lager = pd.DataFrame(lager_daten)
            st.dataframe(df_lager, use_container_width=True, hide_index=True)
            
            st.write("---")
            st.markdown("##### 🛠️ Bestand editieren / löschen")
            auswahl_loeschen = st.selectbox("Ware auswählen:", list(st.session_state._global_paletten_lager.keys()))
            
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.button("🗑️ Komplett löschen", type="secondary", use_container_width=True):
                st.session_state._global_paletten_lager.pop(auswahl_loeschen)
                speichere_gesamte_daten()
                st.rerun()
                
            if c_ed2.button("🔄 Bestand nullen (0 Stk)", use_container_width=True):
                st.session_state._global_paletten_lager[auswahl_loeschen]["anzahl"] = 0
                st.session_state._global_paletten_lager[auswahl_loeschen]["gesamt_liter"] = 0
                speichere_gesamte_daten()
                st.rerun()

# ---------------------------------------------------------
# SEITE 7: DETAILLIERTES KASSENBUCH
# ---------------------------------------------------------
elif menu == "📖 Detailliertes Kassenbuch":
    st.title("📖 Detailliertes Hof-Kassenbuch")
    
    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("Start-Saldo", f"{fmt_float(st.session_state._global_finanzen['start_saldo'])} €")
    col_k2.metric("Gesamteinnahmen", f"{fmt_float(st.session_state._global_finanzen['einnahmen'])} €")
    col_k3.metric("Gesamtausgaben", f"{fmt_float(st.session_state._global_finanzen['ausgaben'])} €")
    
    st.write("---")
    st.subheader("📝 Manueller Buchungssatz (Korrektur)")
    c_f1, c_f2, c_f3, c_f4 = st.columns(4)
    
    b_typ = c_f1.selectbox("Buchungs-Typ:", ["Einnahme", "Ausgabe"])
    b_det = c_f2.text_input("Buchungstext:", placeholder="z.B. Maschinenmiete, Feldpacht")
    b_bet = c_f3.number_input("Betrag in €:", min_value=0.0, value=100.0, step=50.0)
    
    if c_f4.button("⚡ Buchung ausführen", use_container_width=True):
        if b_det.strip():
            if b_typ == "Einnahme":
                st.session_state._global_finanzen["einnahmen"] += b_bet
            else:
                st.session_state._global_finanzen["ausgaben"] += b_bet
                
            st.session_state._global_finanzen["historie"].append({
                "In-Game Datum": "Manuell", "Sort_Jahr": 1, "Sort_Monat": "01 - Jan",
                "Typ": b_typ, "Nummer": "#MANUELL", "Details": b_det.strip(), "Betrag (EUR)": b_bet
            })
            speichere_gesamte_daten()
            st.rerun()
            
    st.write("---")
    st.subheader("📜 Transaktionshistorie")
    if st.session_state._global_finanzen["historie"]:
        df_hist = pd.DataFrame(st.session_state._global_finanzen["historie"])
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
    else:
        st.info("Bisher wurden keine Transaktionen durchgeführt.")
