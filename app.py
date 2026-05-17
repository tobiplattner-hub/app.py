import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

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
        "auftrags_store": [],
        "fuhrpark_store": {}  # Umgestellt auf ein Dictionary für Maschinenname -> Stunden
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

if "_global_daten_geladen" not in st.session_state:
    gespeicherte_daten = lade_gesamte_daten()
    st.session_state._global_hof_store = gespeicherte_daten.get("hof_store", [])
    st.session_state._global_lager_store = gespeicherte_daten.get("lager_store", {})
    st.session_state._global_bestell_store = gespeicherte_daten.get("bestell_store", [])
    st.session_state._global_felder_store = gespeicherte_daten.get("felder_store", [])
    st.session_state._global_fruchtarten = gespeicherte_daten.get("fruchtarten", [])
    st.session_state._global_finanzen = gespeicherte_daten.get("finanzen", {})
    st.session_state._global_lager_grenzwerte = gespeicherte_daten.get("lager_grenzwerte", {})
    st.session_state._global_auftrags_store = gespeicherte_daten.get("auftrags_store", [])
    st.session_state._global_fuhrpark_store = gespeicherte_daten.get("fuhrpark_store", {})
    if isinstance(st.session_state._global_fuhrpark_store, list):  # Migration alter Listendaten falls nötig
        st.session_state._global_fuhrpark_store = {}
    st.session_state._global_daten_geladen = True

def speichere_gesamte_daten():
    daten_zum_speichern = {
        "hof_store": st.session_state._global_hof_store,
        "lager_store": st.session_state._global_lager_store,
        "bestell_store": st.session_state._global_bestell_store,
        "felder_store": st.session_state._global_felder_store,
        "fruchtarten": st.session_state._global_fruchtarten,
        "finanzen": st.session_state._global_finanzen,
        "lager_grenzwerte": st.session_state._global_lager_grenzwerte,
        "auftrags_store": st.session_state._global_auftrags_store,
        "fuhrpark_store": st.session_state._global_fuhrpark_store
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
# FLEXIBLE SUCHE NACH DER LOGODATEI
# ---------------------------------------------------------
def finde_logo_datei():
    moegliche_namen = [
        "logo.png", "logo.png.jpeg", "logo.png.jpg", 
        "logo.jpeg", "logo.jpg", "logo.PNG", "logo.JPEG"
    ]
    for dateiname in moegliche_namen:
        if os.path.exists(dateiname):
            return dateiname
    return None

# ---------------------------------------------------------
# PDF GENERATOR MIT FLEXIBLER LOGO-ERKENNUNG
# ---------------------------------------------------------
class ManagementPDF(FPDF):
    def header(self):
        logo_pfad = finde_logo_datei()
        
        if logo_pfad:
            self.image(logo_pfad, x=10, y=10, w=25)
            start_x = 38
        else:
            self.set_fill_color(34, 139, 34) 
            self.rect(10, 10, 12, 12, "F")
            start_x = 25
        
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 30, 30)
        self.set_x(start_x)
        self.cell(0, 10, "PLATTNER & AUER AGRARSERVICE", ln=True)
        
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(100, 100, 100)
        self.set_x(start_x)
        self.cell(0, 4, "Ihr Partner fuer professionelle Lohnarbeit & Maschinenverleih", ln=True)
        
        self.line(10, 38, 200, 38) 
        self.ln(18)
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Seite {self.page_no()} | Generiert mit Hof-Manager OS", align="C")

def generate_invoice_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum, titel="RECHNUNG"):
    pdf = ManagementPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, f"In-Game Datum: {ingame_datum} | Nr: #RE-{rechnungs_id:04d}", ln=True, align="R")
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, titel, ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, f"Empfaenger: {safe_str(kunden_name)}", ln=True)
    pdf.ln(10)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 8, " Posten / Beschreibung", border=1, fill=True)
    pdf.cell(30, 8, "Menge", border=1, align="C", fill=True)
    pdf.cell(40, 8, "Einzelpreis", border=1, align="R", fill=True)
    pdf.cell(40, 8, "Gesamt", border=1, align="R", fill=True)
    pdf.ln(8)
    
    summe = 0
    pdf.set_font("Helvetica", size=11)
    for p in posten:
        pdf.cell(80, 8, f" {safe_str(p['name'])}", border=1)
        pdf.cell(30, 8, f"{p['menge']} {p['einheit']}", border=1, align="C")
        pdf.cell(40, 8, f"{fmt_float(p['preis'])} EUR", border=1, align="R")
        pdf.cell(40, 8, f"{fmt_float(p['gesamt'])} EUR", border=1, align="R")
        pdf.ln(8)
        summe += p['gesamt']
        
    rabatt_betrag = summe * (rabatt_prozent / 100)
    total = summe - rabatt_betrag
    
    pdf.ln(4)
    if rabatt_prozent > 0:
        pdf.cell(150, 8, f"Zwischensumme:", align="R")
        pdf.cell(40, 8, f"{fmt_float(summe)} EUR", align="R", ln=True)
        pdf.cell(150, 8, f"Rabatt ({rabatt_prozent}%):", align="R")
        pdf.cell(40, 8, f"-{fmt_float(rabatt_betrag)} EUR", align="R", ln=True)
        
    pdf.ln(2)
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
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else ["Müller Agrar", "Hof Lehmann", "Bio-Hof Weber"]

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []
if "global_verbrauch_kalk" not in st.session_state: st.session_state.global_verbrauch_kalk = 2000
if "global_verbrauch_dueng" not in st.session_state: st.session_state.global_verbrauch_dueng = 160
if "global_verbrauch_saat" not in st.session_state: st.session_state.global_verbrauch_saat = 150
if "global_verbrauch_herbi" not in st.session_state: st.session_state.global_verbrauch_herbi = 100
if "temp_lu_maschinen" not in st.session_state: st.session_state.temp_lu_maschinen = []

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
for k, v in st.session_state._global_lager_store.items():
    st.sidebar.write(f"🔹 {k.capitalize()}: **{fmt_int(v)} L**")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", [
    "💰 Ernte & Verbrauchsraten", 
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", 
    "🛒 Material & Aufträge", 
    "📝 LU-Auftragsbuch",
    "🚛 Fuhrpark-Manager",
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
        calc_frucht = st.selectbox("Verkaufte Fruchtart:", st.session_state._global_fruchtarten, key="calc_erloes_frucht")
        calc_menge = st.number_input("Geerntete Gesamtmenge (in Litern):", min_value=0, value=10000, step=1000, key="calc_erloes_menge")
        calc_preis_pro_1k = st.number_input("Marktpreis (€ pro 1.000 Liter):", min_value=0.0, value=850.0, step=50.0, key="calc_erloes_preis")
        
        errechneter_erloes = (calc_menge / 1000.0) * calc_preis_pro_1k
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
                    "In-Game Datum": full_ingame_date, "Sort_Jahr": int(erloes_jahr), "Sort_Monat": erloes_monat,
                    "Typ": "Einnahme", "Nummer": f"#EV-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                    "Details": f"Ernteverkauf: {fmt_int(calc_menge)}L {calc_frucht}", "Betrag (EUR)": errechneter_erloes
                })
                st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                speichere_gesamte_daten()
                st.rerun()

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
        
        st.markdown("##### ⚙️ Spezifische Verbrauchsraten (L/ha):")
        f_rate_kalk = st.number_input("Kalk-Rate (L/ha):", value=int(st.session_state.global_verbrauch_kalk))
        f_rate_saat = st.number_input("Saatgut-Rate (L/ha):", value=int(st.session_state.global_verbrauch_saat))
        f_rate_dueng = st.number_input("Dünger-Rate (L/ha):", value=int(st.session_state.global_verbrauch_dueng))

        neue_frucht = st.text_input("➕ Feldfrüchte erweitern:", placeholder="Hier eintippen...")
        if st.button("✨ Fruchtart registrieren"):
            if neue_frucht.strip() and neue_frucht.strip() not in st.session_state._global_fruchtarten:
                st.session_state._global_fruchtarten.append(neue_frucht.strip())
                st.session_state._global_fruchtarten.sort()
                speichere_gesamte_daten()
                st.rerun()
        
        if st.button("💾 Feld in Datenbank eintragen", type="primary", use_container_width=True):
            if f_nummer.strip():
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
            with st.expander(f"🗺️ {f['nummer']} — ({fmt_float(f['groesse'])} ha) — 🌾 {f.get('frucht', 'Unbekannt')}"):
                c_inf, c_act1, c_act2, c_act3, c_del = st.columns([2, 1, 1, 1, 1])
                bedarf_kalk = f["groesse"] * f.get("rate_kalk", 2000)
                bedarf_saat = f["groesse"] * f.get("rate_saat", 150)
                bedarf_dueng = f["groesse"] * f.get("rate_dueng", 160)
                
                with c_inf:
                    st.text(f"⚪ Kalk: {fmt_int(f['kalk_verbraucht'])}L\n🌱 Saat: {fmt_int(f['saat_verbraucht'])}L\n🧪 Dünger: {fmt_int(f['dueng_verbraucht'])}L")
                
                if c_act1.button(f"⚪ Kalken ({fmt_int(bedarf_kalk)}L)", key=f"kalk_{idx}"):
                    if st.session_state._global_lager_store.get("kalk", 0) >= bedarf_kalk:
                        st.session_state._global_lager_store["kalk"] -= bedarf_kalk
                        st.session_state._global_felder_store[idx]["kalk_verbraucht"] += bedarf_kalk
                        speichere_gesamte_daten()
                        st.rerun()
                    else: st.error("Zu wenig Kalk im Lager!")
                if c_act2.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}"):
                    if st.session_state._global_lager_store.get("saat", 0) >= bedarf_saat:
                        st.session_state._global_lager_store["saat"] -= bedarf_saat
                        st.session_state._global_felder_store[idx]["saat_verbraucht"] += bedarf_saat
                        speichere_gesamte_daten()
                        st.rerun()
                    else: st.error("Zu wenig Saatgut im Lager!")
                if c_act3.button(f"🧪 Düngen ({fmt_int(bedarf_dueng)}L)", key=f"dueng_{idx}"):
                    if st.session_state._global_lager_store.get("dueng", 0) >= bedarf_dueng:
                        st.session_state._global_lager_store["dueng"] -= bedarf_dueng
                        st.session_state._global_felder_store[idx]["dueng_verbraucht"] += bedarf_dueng
                        speichere_gesamte_daten()
                        st.rerun()
                    else: st.error("Zu wenig Dünger im Lager!")
                if c_del.button(f"🗑️ Löschen", key=f"del_f_{idx}"):
                    st.session_state._global_felder_store.pop(idx)
                    speichere_gesamte_daten()
                    st.rerun()

# ---------------------------------------------------------
# SEITE 3: RECHNUNGEN
# ---------------------------------------------------------
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
    col_eingabe, col_liste = st.columns([1, 1.2])
    
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
            auswahl = st.selectbox("Maschine/Gerät (aus Google Sheet):", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
            menge = st.number_input("Stunden (h):", min_value=0.1, value=1.0)
            standard_preis = float(preis_dict.get(auswahl, 75.0)) if preis_dict else 75.0
            e_p = st.number_input("Preis pro Stunde (€/h):", value=standard_preis)
            einheit_str = "h"
            
        if st.button("➕ Posten hinzufügen", use_container_width=True):
            if str(auswahl).strip():
                st.session_state.rechnungs_posten.append({"name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p})
                st.rerun()

    with col_liste:
        st.subheader("Rechnungsdaten & Vorschau")
        k_name = st.selectbox("Empfänger:", aktuelle_kunden)
        rabatt = st.slider("Rabatt (%)", 0, 50, 0)
        c_m, c_j = st.columns(2)
        re_monat = c_m.selectbox("Monat:", LISTE_MONATE, key="re_m")
        re_jahr = c_j.number_input("Jahr:", min_value=1, value=1, key="re_j")

        if st.session_state.rechnungs_posten:
            st.markdown("---")
            st.markdown("**Aktuelle Rechnungsposten:**")
            
            for idx, p in enumerate(st.session_state.rechnungs_posten):
                c_p_info, c_p_del = st.columns([5, 1])
                c_p_info.write(f"🔹 **{p['name']}**: {p['menge']} {p['einheit']} x {fmt_float(p['preis'])} € = **{fmt_float(p['gesamt'])} €**")
                if c_p_del.button("🗑️", key=f"del_posten_{idx}"):
                    st.session_state.rechnungs_posten.pop(idx)
                    st.rerun()

    if st.session_state.rechnungs_posten:
        st.write("---")
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        
        st.markdown(f"### 💵 Endbetrag (inkl. {rabatt}% Rabatt): {fmt_float(total)} €")
        
        c_b1, c_b2 = st.columns(2)
        pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st.session_state._global_finanzen.get("naechste_rechnung_id", 1), full_ingame_date)
        c_b1.download_button("📥 PDF mit Logo generieren", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        
        if c_b2.button("💾 Als Einnahme buchen & abbuchen", type="primary", use_container_width=True):
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

# ---------------------------------------------------------
# SEITE 4: MATERIAL & AUFTRÄGE
# ---------------------------------------------------------
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material-Lagerbestand & Grenzwert-Überwachung")
    
    c_l1, c_l2, c_l3, c_l4, c_l5 = st.columns(5)
    materialien = ["saat", "kalk", "dueng", "herbi", "diesel"]
    werte = {}
    
    for c, mat in zip([c_l1, c_l2, c_l3, c_l4, c_l5], materialien):
        with c:
            st.markdown(f"### {mat.upper()}")
            werte[f"v_{mat}"] = st.number_input("Aktueller Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store.get(mat, 0)), key=f"input_val_{mat}")
            werte[f"g_{mat}"] = st.number_input("Kritischer Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get(mat, 1000)), key=f"input_grenz_{mat}")
            
            if werte[f"v_{mat}"] <= werte[f"g_{mat}"]:
                st.error("🚨 Nachfüllen empfohlen!")
            else:
                st.success("✅ Bestand OK")
            
    if st.button("💾 Lagerkonfiguration保存", use_container_width=True, type="primary"):
        for mat in materialien:
            st.session_state._global_lager_store[mat] = werte[f"v_{mat}"]
            st.session_state._global_lager_grenzwerte[mat] = werte[f"g_{mat}"]
        speichere_gesamte_daten()
        st.rerun()

# ---------------------------------------------------------
# SEITE 5: LU-AUFTRAGSBUCH
# ---------------------------------------------------------
elif menu == "📝 LU-Auftragsbuch":
    st.title("📝 LU-Auftragsbuch & Multi-Maschinenverleih")
    col_a, col_b = st.columns([1.1, 1.4])
    
    with col_a:
        st.subheader("➕ Auftrag / Verleih zusammenstellen")
        a_kunde = st.selectbox("Kunde:", aktuelle_kunden, key="lu_kunde")
        a_einheit = st.selectbox("Abrechnungs-Typ:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Stk (Fixpreis)"], key="lu_einheit")
        
        einheit_map = {"Nach Arbeitsstunden (h)": "h", "Nach Feldfläche (ha)": "ha", "Stk (Fixpreis)": "Stk"}
        v_einheit = einheit_map[a_einheit]
        
        a_feld = st.text_input("Einsatzort / Zweck:", placeholder="z.B. Feld 18 / Verleih-Wochenende", key="lu_ort")
        
        if v_einheit == "h":
            st.markdown("#### 🚜 Maschinen für diesen Auftrag hinzufügen")
            masch_auswahl = st.selectbox("Maschine aus Preisliste:", options=list(preis_dict.keys()) if preis_dict else ["Keine Geräte gefunden"])
            geholter_preis = float(preis_dict.get(masch_auswahl, 50.0)) if preis_dict else 50.0
            
            st.info(f"💰 Automatisch ermittelter Preis: **{fmt_float(geholter_preis)} €/h**")
            
            if st.button("➕ Maschine zum Auftrag packen", use_container_width=True):
                if masch_auswahl and masch_auswahl not in [m["name"] for m in st.session_state.temp_lu_maschinen]:
                    st.session_state.temp_lu_maschinen.append({
                        "name": masch_auswahl, "preis_h": geholter_preis, "anfangs_h": 0.0, "end_h": 0.0
                    })
                    st.rerun()
            
            if st.session_state.temp_lu_maschinen:
                st.markdown("**Ausgewählte Geräte:**")
                for t_idx, m in enumerate(st.session_state.temp_lu_maschinen):
                    c_mname, c_mbtn = st.columns([4, 1])
                    c_mname.write(f"• {m['name']} ({fmt_float(m['preis_h'])} €/h)")
                    if c_mbtn.button("🗑️", key=f"del_temp_{t_idx}"):
                        st.session_state.temp_lu_maschinen.pop(t_idx)
                        st.rerun()
        else:
            a_arbeit = st.text_input("Dienstleistung / Arbeitsschritt:", placeholder="z.B. Dreschen, Mulchen", key="lu_arbeit")
            a_menge = st.number_input("Menge / Fläche:", min_value=0.1, value=1.0, key="lu_menge")
            a_preis = st.number_input("Preis pro Einheit (€):", min_value=0.0, value=100.0, key="lu_preis_einheit")

        st.markdown("---")
        a_status = st.selectbox("Status bei Eintragung:", ["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"], key="lu_status")
        c_m, c_j = st.columns(2)
        lu_monat = c_m.selectbox("Plan-Monat:", LISTE_MONATE, key="lu_m")
        lu_jahr = c_j.number_input("Plan-Jahr:", min_value=1, value=1, key="lu_j")
        
        if st.button("💾 Gesamten Auftrag im Buch speichern", type="primary", use_container_width=True):
            if a_feld.strip():
                if v_einheit == "h":
                    if st.session_state.temp_lu_maschinen:
                        st.session_state._global_auftrags_store.append({
                            "kunde": a_kunde, "ort": a_feld.strip(), "einheit": "h",
                            "status": a_status, "monat": lu_monat, "jahr": int(lu_jahr),
                            "maschinen": st.session_state.temp_lu_maschinen.copy(),
                            "arbeit": "Kombinierter Maschinenverleih"
                        })
                        st.session_state.temp_lu_maschinen = [] 
                        speichere_gesamte_daten()
                        st.rerun()
                    else:
                        st.error("Bitte füge mindestens eine Maschine hinzu!")
                else:
                    if a_arbeit.strip():
                        st.session_state._global_auftrags_store.append({
                            "kunde": a_kunde, "ort": a_feld.strip(), "arbeit": a_arbeit.strip(), 
                            "status": a_status, "menge": a_menge, "einheit": v_einheit, 
                            "preis_einheit": a_preis, "lohn": a_menge * a_preis,
                            "monat": lu_monat, "jahr": int(lu_jahr), "maschinen": []
                        })
                        speichere_gesamte_daten()
                        st.rerun()

    with col_b:
        st.subheader("📋 Aktive LU- & Verleihaufträge")
        if st.session_state._global_auftrags_store:
            for idx, aut in enumerate(st.session_state._global_auftrags_store):
                with st.container(border=True):
                    c1, c2 = st.columns([3.5, 1.5])
                    
                    v_einheit = aut.get('einheit', 'ha')
                    c1.markdown(f"🗓️ **J{aut.get('jahr', 1)}-{aut.get('monat', '01 - Jan')}** | **Kunde:** {aut['kunde']}")
                    c1.markdown(f"📍 **Einsatzort/Zweck:** {aut['ort']}")
                    
                    total_auftragswert = 0.0
                    posten_fuer_pdf = []
                    
                    if v_einheit == "h":
                        c1.markdown("##### ⏱️ Betriebsstunden-Zähler pro Gerät:")
                        liste_maschinen = aut.get("maschinen", [])
                        
                        for m_idx, maschine in enumerate(liste_maschinen):
                            c1.write(f"⚙️ **{maschine['name']}** ({fmt_float(maschine['preis_h'])} €/h)")
                            
                            cx_start, cx_ende = c1.columns(2)
                            anf_val = cx_start.number_input("Start (h):", min_value=0.0, value=float(maschine.get('anfangs_h', 0.0)), step=0.1, key=f"anf_{idx}_{m_idx}")
                            end_val = cx_ende.number_input("Ende (h):", min_value=anf_val, value=float(max(anf_val, maschine.get('end_h', 0.0))), step=0.1, key=f"end_{idx}_{m_idx}")
                            
                            if anf_val != maschine.get('anfangs_h', 0.0) or end_val != maschine.get('end_h', 0.0):
                                st.session_state._global_auftrags_store[idx]['maschinen'][m_idx]['anfangs_h'] = anf_val
                                st.session_state._global_auftrags_store[idx]['maschinen'][m_idx]['end_h'] = end_val
                                speichere_gesamte_daten()
                                st.rerun()
                                
                            diff_h = end_val - anf_val
                            subtotal = diff_h * maschine['preis_h']
                            total_auftragswert += subtotal
                            
                            c1.caption(f"➔ Zeit: {fmt_float(diff_h)} h | Zwischensumme: {fmt_float(subtotal)} €")
                            
                            posten_fuer_pdf.append({
                                "name": f"Verleih: {maschine['name']}", "menge": diff_h, "einheit": "h", "preis": maschine['preis_h'], "gesamt": subtotal
                            })
                    else:
                        c1.markdown(f"🛠️ **Arbeit:** {aut['arbeit']}")
                        v_menge = aut.get('menge', 1.0)
                        v_preis = aut.get('preis_einheit', 0.0)
                        total_auftragswert = v_menge * v_preis
                        
                        c1.write(f"Menge: {fmt_float(v_menge)} {v_einheit} | Preis: {fmt_float(v_preis)} €/{v_einheit}")
                        
                        posten_fuer_pdf.append({
                            "name": aut['arbeit'], "menge": v_menge, "einheit": v_einheit, "preis": v_preis, "gesamt": total_auftragswert
                        })

                    with c2:
                        st.markdown(f"### {fmt_float(total_auftragswert)} €")
                        neuer_status = st.selectbox("Status:", ["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"], 
                                                   index=["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"].index(aut['status']),
                                                   key=f"status_change_{idx}")
                        
                        if neuer_status != aut['status']:
                            st.session_state._global_auftrags_store[idx]['status'] = neuer_status
                            speichere_gesamte_daten()
                            st.rerun()

                        if total_auftragswert > 0:
                            ingame_datum = f"J{aut.get('jahr', 1)}-{aut.get('monat', '01 - Jan')}"
                            pdf_data = generate_invoice_pdf(aut['kunde'], posten_fuer_pdf, 0, 
                                                           st.session_state._global_finanzen.get("naechste_rechnung_id", 1), 
                                                           ingame_datum, titel="RECHNUNG / LEISTUNGSNACHWEIS")
                            
                            st.download_button("📄 PDF Export", data=pdf_data, 
                                              file_name=f"LU_{aut['kunde']}_{idx}.pdf", 
                                              mime="application/pdf", key=f"dl_{idx}", use_container_width=True)

                        if st.button("💾 Buchen & Löschen", key=f"finish_job_{idx}", type="primary", use_container_width=True):
                            ingame_datum = f"J{aut.get('jahr', 1)}-{aut.get('monat', '01 - Jan')}"
                            st.session_state._global_finanzen["einnahmen"] += total_auftragswert
                            st.session_state._global_finanzen["historie"].append({
                                "In-Game Datum": ingame_datum, "Sort_Jahr": int(aut.get('jahr', 1)), "Sort_Monat": aut.get('monat', '01 - Jan'),
                                "Typ": "Einnahme", "Nummer": f"#LU-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                                "Details": f"LU-Auftrag {aut['kunde']}: {aut['arbeit']}", "Betrag (EUR)": total_auftragswert
                            })
                            st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                            st.session_state._global_auftrags_store.pop(idx)
                            speichere_gesamte_daten()
                            st.rerun()
        else:
            st.info("Keine aktiven Aufträge im Buch vorhanden.")

# ---------------------------------------------------------
# SEITE 6: REPARIERTER FUHRPARK-MANAGER (NUR MIT GOOGLE SHEETS DATA)
# ---------------------------------------------------------
elif menu == "🚛 Fuhrpark-Manager":
    st.title("🚛 Fuhrpark- & Wartungsmanager (Google Sheet Live-Synchronisation)")
    
    col_f1, col_f2 = st.columns([1, 1.5])
    
    with col_f1:
        st.subheader("📝 Maschine auf dem Hof aktivieren")
        if preis_dict:
            m_waehlen = st.selectbox("Maschine aus deiner Preisliste:", options=list(preis_dict.keys()))
            m_h = st.number_input("Aktueller Zählerstand / Betriebsstunden (h):", min_value=0.0, step=0.1, value=0.0)
            
            if st.button("💾 In aktiven Fuhrpark aufnehmen", type="primary", use_container_width=True):
                # Fügt die Maschine dem Store hinzu (Standardwert wird gesetzt)
                st.session_state._global_fuhrpark_store[m_waehlen] = m_h
                speichere_gesamte_daten()
                st.rerun()
        else:
            st.warning("Keine Maschinen in der Google-Sheet-Preisliste gefunden. Bitte überprüfe die Tabelle.")
                
    with col_f2:
        st.subheader("📋 Aktiv bewirtschafteter Fuhrpark")
        if st.session_state._global_fuhrpark_store:
            # Iteriere über das saubere Name -> Stunden Dictionary
            for f_name, f_stunden in list(st.session_state._global_fuhrpark_store.items()):
                with st.container(border=True):
                    c_fn, c_fh, c_fdel = st.columns([2.5, 1.5, 0.5])
                    
                    # Holt den aktuellen Miet/Arbeitspreis direkt live aus dem Sheet
                    live_preis = preis_dict.get(f_name, 0.0)
                    c_fn.markdown(f"**{f_name}**  \n`Verrechnungssatz: {fmt_float(live_preis)} €/h`")
                    
                    # Stunden updaten
                    neue_stunden = c_fh.number_input(f"Betriebsstunden (h)", min_value=0.0, value=float(f_stunden), step=0.1, key=f"f_h_{f_name}")
                    if neue_stunden != f_stunden:
                        st.session_state._global_fuhrpark_store[f_name] = neue_stunden
                        speichere_gesamte_daten()
                        st.rerun()
                        
                    if c_fdel.button("🗑️", key=f"del_f_mach_{f_name}"):
                        del st.session_state._global_fuhrpark_store[f_name]
                        speichere_gesamte_daten()
                        st.rerun()
        else:
            st.info("Aktuell befinden sich keine aktiven Maschinen auf dem Hof. Aktiviere links dein erstes Gerät!")

# ---------------------------------------------------------
# SEITE 7: DETAILLIERTES KASSENBUCH
# ---------------------------------------------------------
elif menu == "📖 Detailliertes Kassenbuch":
    st.title("📖 Detailliertes Kassenbuch & Finanzanalyse")
    
    # Kacheln
    einn = st.session_state._global_finanzen.get("einnahmen", 0.0)
    ausg = st.session_state._global_finanzen.get("ausgaben", 0.0)
    start_s = st.session_state._global_finanzen.get("start_saldo", 0.0)
    aktuell = start_s + einn - ausg
    
    c_k1, c_k2, c_k3 = st.columns(3)
    c_k1.metric("Gesamteinnahmen", f"{fmt_float(einn)} €", delta=f"+{fmt_float(einn)} €" if einn > 0 else None)
    c_k2.metric("Gesamtausgaben", f"{fmt_float(ausg)} €", delta=f"-{fmt_float(ausg)} €" if ausg > 0 else None, delta_color="inverse")
    c_k3.metric("Aktueller Kontostand", f"{fmt_float(aktuell)} €")
    
    st.markdown("---")
    
    # EXPANDER FÜR MANUELLE BUCHUNGEN
    with st.expander("➕ Spontane Buchung manuell eintragen (Händler, Werkstatt, etc.)"):
        c_man1, c_man2, c_man3 = st.columns(3)
        man_monat = c_man1.selectbox("In-Game Monat:", LISTE_MONATE, key="man_m")
        man_jahr = c_man2.number_input("In-Game Jahr:", min_value=1, value=1, key="man_j")
        man_details = c_man3.text_input("Verwendungszweck / Details:", placeholder="z.B. Diesel gekauft, Werkstattkosten")
        
        c_man4, c_man5 = st.columns(2)
        man_betrag = c_man4.number_input("Betrag (€):", min_value=0.01, value=100.0, step=10.0)
        
        st.write("")
        c_btn_ein, c_btn_aus = st.columns(2)
        
        if c_btn_ein.button("🟩 Als Einnahme buchen", use_container_width=True):
            if man_details.strip():
                full_ingame_date = f"J{man_jahr}-{man_monat}"
                st.session_state._global_finanzen["einnahmen"] += man_betrag
                st.session_state._global_finanzen["historie"].append({
                    "In-Game Datum": full_ingame_date, "Sort_Jahr": int(man_jahr), "Sort_Monat": man_monat,
                    "Typ": "Einnahme", "Nummer": f"#MAN-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                    "Details": f"Manuell: {man_details.strip()}", "Betrag (EUR)": man_betrag
                })
                st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                speichere_gesamte_daten()
                st.success("Einnahme erfolgreich gebucht!")
                st.rerun()
            else:
                st.error("Bitte gib einen Verwendungszweck an!")

        if c_btn_aus.button("🟥 Als Ausgabe buchen", use_container_width=True):
            if man_details.strip():
                full_ingame_date = f"J{man_jahr}-{man_monat}"
                st.session_state._global_finanzen["ausgaben"] += man_betrag
                st.session_state._global_finanzen["historie"].append({
                    "In-Game Datum": full_ingame_date, "Sort_Jahr": int(man_jahr), "Sort_Monat": man_monat,
                    "Typ": "Ausgabe", "Nummer": f"#MAN-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}",
                    "Details": f"Manuell: {man_details.strip()}", "Betrag (EUR)": man_betrag
                })
                st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                speichere_gesamte_daten()
                st.success("Ausgabe erfolgreich gebucht!")
                st.rerun()
            else:
                st.error("Bitte gib einen Verwendungszweck an!")

    st.markdown("---")
    historie_liste = st.session_state._global_finanzen.get("historie", [])
    
    if historie_liste:
        df_hist = pd.DataFrame(historie_liste)
        
        with st.expander("🔍 Buchungen filtern & durchsuchen"):
            f_col1, f_col2 = st.columns(2)
            filter_typ = f_col1.selectbox("Nach Buchungstyp filtern:", ["Alle Einträge", "Nur Einnahmen", "Nur Ausgaben"])
            suchbegriff = f_col2.text_input("Details durchsuchen (z.B. Kundenname, Frucht, Manuell):")
        
        df_gefiltert = df_hist.copy()
        if filter_typ == "Nur Einnahmen":
            df_gefiltert = df_gefiltert[df_gefiltert["Typ"] == "Einnahme"]
        elif filter_typ == "Nur Ausgaben":
            df_gefiltert = df_gefiltert[df_gefiltert["Typ"] == "Ausgabe"]
            
        if suchbegriff.strip():
            df_gefiltert = df_gefiltert[df_gefiltert["Details"].str.contains(suchbegriff, case=False, na=False)]
            
        df_gefiltert = df_gefiltert.iloc[::-1] # Neueste oben
        
        if not df_gefiltert.empty:
            st.subheader(f"📋 Detaillierte Auflistung ({len(df_gefiltert)} Buchungen)")
            df_anzeige = df_gefiltert.copy()
            df_anzeige["Betrag (EUR)"] = df_anzeige["Betrag (EUR)"].apply(lambda x: f"{fmt_float(x)} €")
            
            st.dataframe(
                df_anzeige[["In-Game Datum", "Nummer", "Typ", "Details", "Betrag (EUR)"]],
                use_container_width=True,
                hide_index=True
            )
            
            csv_data = df_gefiltert[["In-Game Datum", "Nummer", "Typ", "Details", "Betrag (EUR)"]].to_csv(index=False, encoding="utf-8")
            st.download_button(
                label="📥 Kassenbuch als CSV exportieren",
                data=csv_data,
                file_name=f"kassenbuch_export_{date.today()}.csv",
                mime="text/csv",
            )
        else:
            st.info("Keine Einträge gefunden, die auf die Filtereinstellungen passen.")
            
        st.write("")
        with st.expander("🚨 Gefahrenzone (Daten zurücksetzen)"):
            st.warning("Achtung: Das Löschen der Historie setzt alle Einnahmen, Ausgaben und Buchungen unwiderruflich zurück!")
            if st.button("💥 Komplette Finanzhistorie löschen", type="primary"):
                st.session_state._global_finanzen["historie"] = []
                st.session_state._global_finanzen["einnahmen"] = 0.0
                st.session_state._global_finanzen["ausgaben"] = 0.0
                speichere_gesamte_daten()
                st.rerun()
    else:
        st.info("Noch keine Buchungen im Kassenbuch vorhanden.")

# Automatisches Speichern am Ende jeder Interaktion
speichere_gesamte_daten()
