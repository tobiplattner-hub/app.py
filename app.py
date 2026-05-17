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
        "fuhrpark_store": []
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
    st.session_state._global_fuhrpark_store = gespeicherte_daten.get("fuhrpark_store", [])
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

class ManagementPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "PLATTNER & AUER AGRARSERVICE", ln=True)
        self.line(10, 20, 200, 20) 
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", align="C")

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
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else ["Müller Agrar", "Hof Lehmann", "Bio-Hof Weber"]

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []
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
                if c_act2.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}"):
                    if st.session_state._global_lager_store.get("saat", 0) >= bedarf_saat:
                        st.session_state._global_lager_store["saat"] -= bedarf_saat
                        st.session_state._global_felder_store[idx]["saat_verbraucht"] += bedarf_saat
                        speichere_gesamte_daten()
                        st.rerun()
                if c_act3.button(f"🧪 Düngen ({fmt_int(bedarf_dueng)}L)", key=f"dueng_{idx}"):
                    if st.session_state._global_lager_store.get("dueng", 0) >= bedarf_dueng:
                        st.session_state._global_lager_store["dueng"] -= bedarf_dueng
                        st.session_state._global_felder_store[idx]["dueng_verbraucht"] += bedarf_dueng
                        speichere_gesamte_daten()
                        st.rerun()
                if c_del.button(f"🗑️ Löschen", key=f"del_f_{idx}"):
                    st.session_state._global_felder_store.pop(idx)
                    speichere_gesamte_daten()
                    st.rerun()

# ---------------------------------------------------------
# SEITE 3: RECHNUNGEN
# ---------------------------------------------------------
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
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
        st.write("---")
        st.dataframe(pd.DataFrame(st.session_state.rechnungs_posten), use_container_width=True, hide_index=True)
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        
        c_b1, c_b2 = st.columns(2)
        pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st.session_state._global_finanzen.get("naechste_rechnung_id", 1), full_ingame_date)
        c_b1.download_button("📥 PDF laden", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        
        if c_b2.button("💾 Als Einnahme buchen", type="primary", use_container_width=True):
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
            
    if st.button("💾 Lagerkonfiguration speichern", use_container_width=True, type="primary"):
        for mat in materialien:
            st.session_state._global_lager_store[mat] = werte[f"v_{mat}"]
            st.session_state._global_lager_grenzwerte[mat] = werte[f"g_{mat}"]
        speichere_gesamte_daten()
        st.rerun()

# ---------------------------------------------------------
# SEITE 5: LU-AUFTRAGSBUCH (JETZT MIT STUNDEN-ZÄHLER FÜR MASCHINENVERLEIH)
# ---------------------------------------------------------
elif menu == "📝 LU-Auftragsbuch":
    st.title("📝 LU-Auftragsbuch & Schnelle Abrechnung")
    col_a, col_b = st.columns([1, 1.5])
    
    with col_a:
        st.subheader("➕ Neuen Auftrag / Verleih erfassen")
        a_kunde = st.selectbox("Kunde:", aktuelle_kunden, key="lu_kunde")
        a_einheit = st.selectbox("Einheit:", ["ha", "h", "Stk"], key="lu_einheit")
        
        # Falls stundenweise abgerechnet wird, optionale Maschinen-Vorauswahl aus Sheets
        if a_einheit == "h":
            a_arbeit = st.selectbox("Verleihtes Gerät / Maschine:", options=list(preis_dict.keys()) if preis_dict else ["Standard-Maschine"], key="lu_arbeit_dropdown")
            # Standardpreis direkt laden falls vorhanden
            default_p = float(preis_dict.get(a_arbeit, 100.0))
        else:
            a_arbeit = st.text_input("Arbeitsschritt / Dienstleistung:", placeholder="z.B. Dreschen, Pressen", key="lu_arbeit")
            default_p = 100.0
            
        a_feld = st.text_input("Feld / Einsatzort:", placeholder="z.B. Feld 12 / Maschinenverleih", key="lu_ort")
        
        # Bei "h" startet die geplante Menge standardmäßig bei 0.0, da wir den Zähler benutzen können
        a_menge = st.number_input("Menge (Geplante Fläche/Zeit):", min_value=0.0, value=1.0 if a_einheit != "h" else 0.0, key="lu_menge")
        a_preis = st.number_input("Preis pro Einheit (€):", min_value=0.0, value=default_p, key="lu_preis_einheit")
        a_status = st.selectbox("Status:", ["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"], key="lu_status")
        
        c_m, c_j = st.columns(2)
        lu_monat = c_m.selectbox("Plan-Monat:", LISTE_MONATE, key="lu_m")
        lu_jahr = c_j.number_input("Plan-Jahr:", min_value=1, value=1, key="lu_j")
        
        if st.button("💾 Auftrag eintragen", type="primary", use_container_width=True):
            if a_feld.strip() and str(a_arbeit).strip():
                st.session_state._global_auftrags_store.append({
                    "kunde": a_kunde, "ort": a_feld.strip(), "arbeit": a_arbeit.strip(), 
                    "status": a_status, "menge": a_menge, "einheit": a_einheit, 
                    "preis_einheit": a_preis, "lohn": a_menge * a_preis,
                    "monat": lu_monat, "jahr": int(lu_jahr),
                    "anfangs_h": 0.0, "end_h": 0.0  # NEU: Felder initialisieren
                })
                speichere_gesamte_daten()
                st.rerun()

    with col_b:
        st.subheader("📋 Aktuelle Auftragsliste & Direktabrechnung")
        if st.session_state._global_auftrags_store:
            for idx, aut in enumerate(st.session_state._global_auftrags_store):
                with st.container(border=True):
                    c1, c2 = st.columns([3.5, 1.5])
                    
                    v_einheit = aut.get('einheit', 'ha')
                    
                    # Dynamische Stundenberechnung, falls es sich um einen Stundenverleih handelt
                    if v_einheit == "h":
                        anf_h = aut.get('anfangs_h', 0.0)
                        end_h = aut.get('end_h', 0.0)
                        diff_h = end_h - anf_h
                        
                        # Wenn Zählerstände eingetragen wurden, überschreiben sie die vordefinierte Menge!
                        if diff_h > 0:
                            v_menge = diff_h
                        else:
                            v_menge = aut.get('menge', 0.0)
                    else:
                        v_menge = aut.get('menge', 1.0)
                        
                    v_preis_einheit = aut.get('preis_einheit', 0.0)
                    total_lohn = v_menge * v_preis_einheit
                    
                    c1.markdown(f"🗓️ **J{aut.get('jahr', 1)}-{aut.get('monat', '01 - Jan')}** | **Kunde:** {aut['kunde']}")
                    c1.markdown(f"🛠️ **{aut['arbeit']}** auf *{aut['ort']}*")
                    
                    # NEU: Integrierter Zählerstand-Rechner direkt in der Auftragskarte
                    if v_einheit == "h":
                        c1.markdown("##### ⏱️ Maschinen-Zählerstand für Abrechnung")
                        cc_start, cc_ende = c1.columns(2)
                        
                        input_anfang = cc_start.number_input("Start-Zähler (h):", min_value=0.0, value=float(aut.get('anfangs_h', 0.0)), step=0.1, format="%.1f", key=f"lu_anf_{idx}")
                        input_ende = cc_ende.number_input("End-Zähler (h):", min_value=input_anfang, value=float(max(input_anfang, aut.get('end_h', 0.0))), step=0.1, format="%.1f", key=f"lu_end_{idx}")
                        
                        if (input_anfang != aut.get('anfangs_h', 0.0)) or (input_ende != aut.get('end_h', 0.0)):
                            st.session_state._global_auftrags_store[idx]['anfangs_h'] = input_anfang
                            st.session_state._global_auftrags_store[idx]['end_h'] = input_ende
                            st.session_state._global_auftrags_store[idx]['lohn'] = (input_ende - input_anfang) * v_preis_einheit
                            speichere_gesamte_daten()
                            st.rerun()
                            
                        if (input_ende - input_anfang) > 0:
                            c1.caption(f"Errechnete Leihzeit: {fmt_float(input_ende - input_anfang)} h")
                    
                    c1.markdown(f"📊 **Abrechnung:** {fmt_float(v_menge)} {v_einheit} x {fmt_float(v_preis_einheit)} € = **{fmt_float(total_lohn)} €**")
                    
                    neuer_status = c1.selectbox(f"Status ändern:", ["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"], index=["⏳ Ausstehend", "🚜 In Arbeit", "✔️ Erledigt"].index(aut['status']), key=f"status_select_{idx}")
                    if neuer_status != aut['status']:
                        st.session_state._global_auftrags_store[idx]['status'] = neuer_status
                        speichere_gesamte_daten()
                        st.rerun()
                    
                    if aut['status'] == "✔️ Erledigt":
                        posten_name = f"Maschinenverleih: {aut['arbeit']}" if v_einheit == "h" else f"{aut['arbeit']} ({aut['ort']})"
                        posten_liste = [{"name": posten_name, "menge": v_menge, "einheit": v_einheit, "preis": v_preis_einheit, "gesamt": total_lohn}]
                        full_date = f"J{aut.get('jahr', 1)}-{aut.get('monat', '01 - Jan')}"
                        next_id = st.session_state._global_finanzen.get("naechste_rechnung_id", 1)
                        
                        pdf_data = generate_invoice_pdf(aut['kunde'], posten_liste, 0, next_id, full_date, titel="LU-RECHNUNG / MASCHINENVERLEIH")
                        
                        c2.download_button("📥 PDF herunterladen", data=pdf_data, file_name=f"LU_Verleih_{aut['kunde']}.pdf", mime="application/pdf", key=f"dl_{idx}", use_container_width=True)
                        
                        if c2.button("💰 Cash verbuchen & schließen", key=f"cash_{idx}", type="primary", use_container_width=True):
                            st.session_state._global_finanzen["einnahmen"] += total_lohn
                            st.session_state._global_finanzen["historie"].append({
                                "In-Game Datum": full_date, "Sort_Jahr": int(aut.get('jahr', 1)), "Sort_Monat": aut.get('monat', '01 - Jan'),
                                "Typ": "Einnahme", "Nummer": f"#LU-{next_id:04d}",
                                "Details": f"LU abgeschlossen: {posten_name}", "Betrag (EUR)": total_lohn
                            })
                            st.session_state._global_finanzen["naechste_rechnung_id"] = next_id + 1
                            
                            st.session_state._global_auftrags_store.pop(idx)
                            speichere_gesamte_daten()
                            st.rerun()
                    
                    if c2.button("🗑️ Auftrag verwerfen", key=f"del_a_{idx}", use_container_width=True):
                        st.session_state._global_auftrags_store.pop(idx)
                        speichere_gesamte_daten()
                        st.rerun()
        else:
            st.info("Das Auftragsbuch ist leer.")

# ---------------------------------------------------------
# SEITE 6: FUHRPARK-MANAGER
# ---------------------------------------------------------
elif menu == "🚛 Fuhrpark-Manager":
    st.title("🚛 Fuhrpark-Management & Service-Überwachung")
    
    tab1, tab2 = st.tabs(["📋 Maschinen-Liste", "➕ Neue Maschine registrieren"])
    
    with tab2:
        st.subheader("Fahrzeug / Gerät aus Preisliste hinzufügen")
        v_name = st.selectbox("Name / Modell (aus Google Sheet):", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
        v_kat = st.selectbox("Kategorie:", ["Traktor", "Mähdrescher", "Feldhäcksler", "Ladewagen", "Sämaschine/Grubber", "Transport", "Sonstiges"])
        v_h = st.number_input("Aktuelle Betriebsstunden (h):", min_value=0.0, value=0.0, step=0.1, format="%.1f")
        v_service_intervall = st.number_input("Service-Intervall (alle X Stunden):", min_value=10, value=50, step=10)
        v_letzter_service = st.number_input("Letzter Service bei (h):", min_value=0.0, value=0.0, step=0.1)
        
        if st.button("💾 Maschine im Fuhrpark保存", type="primary"):
            if str(v_name).strip():
                st.session_state._global_fuhrpark_store.append({
                    "name": v_name.strip(), "kategorie": v_kat, "stunden": v_h,
                    "intervall": v_service_intervall, "letzter_service": v_letzter_service
                })
                speichere_gesamte_daten()
                st.success(f"{v_name} erfolgreich registriert!")
                st.rerun()
                
    with tab1:
        st.subheader("🚜 Mein Hof-Fuhrpark")
        if st.session_state._global_fuhrpark_store:
            for idx, veh in enumerate(st.session_state._global_fuhrpark_store):
                
                naechster_service = veh["letzter_service"] + veh["intervall"]
                stunden_bis_service = naechster_service - veh["stunden"]
                
                with st.container(border=True):
                    col_info, col_calc, col_action = st.columns([2.5, 2.5, 2])
                    
                    with col_info:
                        st.markdown(f"### {veh['name']}")
                        st.markdown(f"📁 Kategorie: **{veh['kategorie']}**")
                        st.markdown(f"⏱️ Zählerstand aktuell: **{fmt_float(veh['stunden'])} h**")
                        
                        if stunden_bis_service <= 0:
                            st.error(f"🚨 SERVICE ÜBERFÄLLIG! (Seit {fmt_float(abs(stunden_bis_service))} h)")
                        elif stunden_bis_service <= 5:
                            st.warning(f"⚠️ Service fällig in: **{fmt_float(stunden_bis_service)} h**")
                        else:
                            st.success(f"✅ Service ok (In {fmt_float(stunden_bis_service)} h bei {fmt_float(naechster_service)} h)")
                            
                    with col_calc:
                        st.markdown("##### ⏱️ Feldarbeits-Zähler")
                        c_start, c_ende = st.columns(2)
                        anfangs_h = c_start.number_input("Anfangs-h:", min_value=0.0, value=float(veh['stunden']), step=0.1, format="%.1f", key=f"start_h_{idx}")
                        end_h = c_ende.number_input("End-h:", min_value=anfangs_h, value=anfangs_h, step=0.1, format="%.1f", key=f"end_h_{idx}")
                        
                        differenz_h = end_h - anfangs_h
                        if differenz_h > 0:
                            st.info(f"➕ Errechnete Arbeitszeit: **{fmt_float(differenz_h)} h**")
                            if st.button("📈 Stunden aufbuchen", key=f"save_hours_{idx}", use_container_width=True):
                                st.session_state._global_fuhrpark_store[idx]['stunden'] = end_h
                                speichere_gesamte_daten()
                                st.toast(f"⏱️ {fmt_float(differenz_h)} Stunden aufgebucht!")
                                st.rerun()
                        else:
                            st.caption("Gib die Endstunden nach der Feldarbeit ein, um Zähler aufzubuchen.")
                            
                    with col_action:
                        st.markdown("##### 🔧 Wartung & Optionen")
                        if st.button("🛠️ Service durchgeführt!", key=f"serv_{idx}", use_container_width=True):
                            st.session_state._global_fuhrpark_store[idx]['letzter_service'] = veh['stunden']
                            speichere_gesamte_daten()
                            st.rerun()
                            
                        if st.button("🗑️ Ausmustern (Löschen)", key=f"del_v_{idx}", use_container_width=True):
                            st.session_state._global_fuhrpark_store.pop(idx)
                            speichere_gesamte_daten()
                            st.rerun()
        else:
            st.info("Noch keine Maschinen im Fuhrpark eingetragen.")

# ---------------------------------------------------------
# SEITE 7: DETILLIERTES KASSENBUCH
# ---------------------------------------------------------
elif menu == "📖 Detailliertes Kassenbuch":
    st.title("📖 Detailliertes Kassenbuch")
    
    with st.expander("➕ Manuelle Einnahme / Ausgabe buchen", expanded=False):
        c_btyp, c_bbetrag = st.columns(2)
        m_typ = c_btyp.selectbox("Buchungstyp:", ["Einnahme", "Ausgabe"])
        m_betrag = c_bbetrag.number_input("Betrag (€):", min_value=0.01, value=100.0, step=10.0)
        m_details = st.text_input("Buchungstext / Verwendungszweck:", placeholder="z.B. Maschinen-Reparatur, Helferlohn, etc.")
        
        c_bm, c_bj = st.columns(2)
        m_monat = c_bm.selectbox("In-Game Monat:", LISTE_MONATE, key="man_m")
        m_jahr = c_bj.number_input("In-Game Jahr:", min_value=1, value=1, key="man_j")
        
        if st.button("💾 Buchung festschreiben", type="primary", use_container_width=True):
            if m_details.strip():
                full_ingame_date = f"J{m_jahr}-{m_monat}"
                
                if m_typ == "Einnahme":
                    st.session_state._global_finanzen["einnahmen"] += m_betrag
                    rechnungs_kennung = f"#MAN-E-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}"
                else:
                    st.session_state._global_finanzen["ausgaben"] += m_betrag
                    rechnungs_kennung = f"#MAN-A-{st.session_state._global_finanzen.get('naechste_bestellung_id', 1):04d}"
                
                st.session_state._global_finanzen["historie"].append({
                    "In-Game Datum": full_ingame_date, "Sort_Jahr": int(m_jahr), "Sort_Monat": m_monat,
                    "Typ": m_typ, "Nummer": rechnungs_kennung, "Details": m_details.strip(), "Betrag (EUR)": m_betrag
                })
                
                if m_typ == "Einnahme":
                    st.session_state._global_finanzen["naechste_rechnung_id"] = st.session_state._global_finanzen.get("naechste_rechnung_id", 1) + 1
                else:
                    st.session_state._global_finanzen["naechste_bestellung_id"] = st.session_state._global_finanzen.get("naechste_bestellung_id", 1) + 1
                    
                speichere_gesamte_daten()
                st.rerun()
            else:
                st.error("Bitte gib einen Buchungstext an.")

    st.write("---")
    st.subheader("📋 Letzte Transaktionen")
    if st.session_state._global_finanzen.get("historie"):
        st.dataframe(pd.DataFrame(st.session_state._global_finanzen["historie"]), use_container_width=True, hide_index=True)
    else:
        st.info("Bisher keine Buchungen vorhanden.")
