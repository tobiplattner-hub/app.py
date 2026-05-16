import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# ---------------------------------------------------------
# DATEN-SPEICHERUNG & LADEN (AUTOMATISCHER SCHUTZ VOR DATENVERLUST)
# ---------------------------------------------------------
DATA_FILE = "hof_manager_daten.json"

def lade_gesamte_daten():
    """Lädt alle gespeicherten Zustände von der Festplatte oder gibt Standardwerte zurück"""
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
        }
    }
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                geladene_daten = json.load(f)
                # Sicherstellen, dass alle Schlüssel aus den Standarddaten existieren
                for k, v in standard_daten.items():
                    if k not in geladene_daten:
                        geladene_daten[k] = v
                return geladene_daten
        except:
            return standard_daten
    return standard_daten

def speichere_gesamte_daten():
    """Sichert den aktuellen Zustand aller globalen Stores auf der Festplatte"""
    daten_zum_speichern = {
        "hof_store": st._global_hof_store,
        "lager_store": st._global_lager_store,
        "bestell_store": st._global_bestell_store,
        "felder_store": st._global_felder_store,
        "fruchtarten": st._global_fruchtarten,
        "finanzen": st._global_finanzen
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(daten_zum_speichern, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fehler beim automatischen Sichern der Daten: {e}")

# Initialisiere die globalen Variablen einmalig aus der Datei
if not hasattr(st, "_global_daten_geladen"):
    gespeicherte_daten = lade_gesamte_daten()
    st._global_hof_store = gespeicherte_daten["hof_store"]
    st._global_lager_store = gespeicherte_daten["lager_store"]
    st._global_bestell_store = gespeicherte_daten["bestell_store"]
    st._global_felder_store = gespeicherte_daten["felder_store"]
    st._global_fruchtarten = gespeicherte_daten["fruchtarten"]
    st._global_finanzen = gespeicherte_daten["finanzen"]
    st._global_daten_geladen = True

LISTE_MONATE = [
    "01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", 
    "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", 
    "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"
]

# ---------------------------------------------------------
# HILFSFUNKTIONEN
# ---------------------------------------------------------
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR', '⏳': '', '🚜': '', '🌾': ''}
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
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "LU-BETRIEB MANAGEMENT & LOGISTIK", ln=True)
        self.line(10, 20, 200, 20)
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
    return pdf.output(dest='S').encode('latin1')

def generate_auftragslog_pdf(auftraege_liste):
    pdf = ManagementPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "AKTUELL REGISTRIERTE LU-AUFTRAEGE", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 8, "Kunde / Hof", border=1)
    pdf.cell(85, 8, "Aufgabe / Beschreibung", border=1)
    pdf.cell(30, 8, "In-Game Datum", border=1)
    pdf.cell(40, 8, "Status", border=1)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", size=10)
    for a in auftraege_liste:
        pdf.cell(35, 8, safe_str(a['Kunde']), border=1)
        pdf.cell(85, 8, safe_str(a['Aufgabe']), border=1)
        pdf.cell(30, 8, safe_str(a['Eingang']), border=1)
        pdf.cell(40, 8, safe_str(a['Status']), border=1)
        pdf.ln(8)
        
    return pdf.output(dest='S').encode('latin1')

def generate_einzel_auftrag_pdf(auftrag):
    pdf = ManagementPDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "ARBEITSNACHWEIS / DIENSTLEISTUNG", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(45, 8, "Kunde / Empfaenger:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag['Kunde']), border=0, ln=True)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(45, 8, "Datum der Erfassung:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag['Eingang']), border=0, ln=True)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(45, 8, "Bearbeitungs-Status:", border=0)
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 8, safe_str(auftrag['Status']), border=0, ln=True)
    
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Durchgefuehrte Arbeiten / Bestellung:", ln=True)
    pdf.ln(4)
    
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, f"- {safe_str(auftrag['Aufgabe'])}", border=1)
    
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(90, 8, "Unterschrift Lohnunternehmer", border="T", align="C")
    pdf.set_x(120)
    pdf.cell(80, 8, "Unterschrift Kunde", border="T", align="C")
    
    return pdf.output(dest='S').encode('latin1')


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

# Verbrauchs-Standards im Session State halten
if "global_verbrauch_kalk" not in st.session_state: st.session_state.global_verbrauch_kalk = 2000
if "global_verbrauch_dueng" not in st.session_state: st.session_state.global_verbrauch_dueng = 160
if "global_verbrauch_saat" not in st.session_state: st.session_state.global_verbrauch_saat = 150
if "global_verbrauch_herbi" not in st.session_state: st.session_state.global_verbrauch_herbi = 100

PROD_DATA = {
    "Getreidemühle: Weizen zu Mehl": (15, 11, 2400, "Weizen", "Mehl"),
    "Bäckerei: Brot": (18, 9, 1200, "Mehl", "Brot"),
    "Ölmühle: Rapsöl": (20, 10, 720, "Raps", "Rapsöl"),
    "Molkerei: Käse": (15, 11, 1440, "Milch", "Käse")
}

# ---------------------------------------------------------
# SIDEBAR LIVE-ANZEIGE
# ---------------------------------------------------------
st.sidebar.title("💰 Hof-Kasse (Live)")
einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
aktuelle_hof_kasse = st._global_finanzen["start_saldo"] + einn - ausg
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")

st.sidebar.markdown("---")
st.sidebar.title("📦 Live-Lagerbestand")
st.sidebar.write(f"🌱 Saatgut: **{fmt_int(st._global_lager_store['saat'])} L**")
st.sidebar.write(f"⚪ Kalk: **{fmt_int(st._global_lager_store['kalk'])} L**")
st.sidebar.write(f"🧪 Dünger: **{fmt_int(st._global_lager_store['dueng'])} L**")
st.sidebar.write(f"🌿 Herbizid: **{fmt_int(st._global_lager_store['herbi'])} L**")

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", [
    "💰 Ernte & Verbrauchsraten", 
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", 
    "🛒 Material & Aufträge", 
    "🏭 Produktionen",
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
        
    with col2:
        st.subheader("🧪 Schneller Feldbedarf-Rechner")
        ha = st.number_input("Hektar Testfläche (ha):", min_value=0.1, value=1.0, step=0.1)
        st.markdown(f"### Benötigtes Material für {ha} ha:")
        st.write(f"⚪ Kalk: **{fmt_int(ha * st.session_state.global_verbrauch_kalk)} Liter**")
        st.write(f"🧪 Dünger: **{fmt_int(ha * st.session_state.global_verbrauch_dueng)} Liter**")
        st.write(f"🌱 Saatgut: **{fmt_int(ha * st.session_state.global_verbrauch_saat)} Liter**")
        st.write(f"🌿 Herbizid: **{fmt_int(ha * st.session_state.global_verbrauch_herbi)} Liter**")

# ---------------------------------------------------------
# SEITE 2: MEINE FELDER & ANBAU
# ---------------------------------------------------------
elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung mit automatischer Lagerbuchung")
    st.markdown("Verwalte deine Felder für **The Pichonniere Valley**. Führe Feldarbeiten direkt hier aus, um Material live aus dem Silo zu entnehmen!")

    col_feld_ein, col_feld_stats = st.columns([1, 1])
    
    with col_feld_ein:
        st.subheader("📝 Neues Feld registrieren")
        f_nummer = st.text_input("Feld-ID / Nummer:", placeholder="z.B. Feld 4")
        f_groesse = st.number_input("Feldgröße in Hektar (ha):", min_value=0.01, value=2.0, step=0.1, format="%.2f")
        
        f_frucht = st.selectbox("Geplante / Aktuelle Frucht:", st._global_fruchtarten)
        
        neue_frucht = st.text_input("➕ Feldfrüchte erweitern (z.B. Ackerbohnen):", placeholder="Hier eintippen...")
        if st.button("✨ Fruchtart registrieren"):
            if neue_frucht.strip() and neue_frucht.strip() not in st._global_fruchtarten:
                st._global_fruchtarten.append(neue_frucht.strip())
                st._global_fruchtarten.sort()
                speichere_gesamte_daten()
                st.success(f"'{neue_frucht.strip()}' wurde zur Liste hinzugefügt und gesichert!")
                st.rerun()
        
        if st.button("💾 Feld in Datenbank eintragen", type="primary", use_container_width=True):
            if f_nummer.strip():
                existiert = False
                for idx, feld in enumerate(st._global_felder_store):
                    if feld["nummer"].lower() == f_nummer.strip().lower():
                        st._global_felder_store[idx] = {
                            "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                            "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0
                        }
                        existiert = True
                        break
                if not existiert:
                    st._global_felder_store.append({
                        "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                        "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0
                    })
                speichere_gesamte_daten()
                st.rerun()

    with col_feld_stats:
        st.subheader("📊 Betriebszusammenfassung")
        if st._global_felder_store:
            ges_ha = sum(f["groesse"] for f in st._global_felder_store)
            st.metric("Gesamtfläche unter Bewirtschaftung", f"{fmt_float(ges_ha)} ha")
            st.info("💡 Nutze die Aktionsknöpfe unten in der Tabelle, wenn du ein Feld real im Spiel bearbeitest.")
        else:
            st.info("Noch keine Felder registriert.")

    if st._global_felder_store:
        st.write("---")
        st.subheader("📋 Gekaufte Felder & Feldarbeits-Konsole")
        
        for idx, f in enumerate(st._global_felder_store):
            with st.expander(f"🗺️ {f['nummer']} — ({fmt_float(f['groesse'])} ha) — Aktuell: {f['frucht']}", expanded=True):
                c_inf, c_act1, c_act2, c_act3, c_act4 = st.columns([2, 1, 1, 1, 1])
                
                bedarf_kalk = f["groesse"] * st.session_state.global_verbrauch_kalk
                bedarf_saat = f["groesse"] * st.session_state.global_verbrauch_saat
                bedarf_dueng = f["groesse"] * st.session_state.global_verbrauch_dueng
                bedarf_herbi = f["groesse"] * st.session_state.global_verbrauch_herbi
                
                with c_inf:
                    st.write(f"**Verbrauchter Durchgang:**")
                    st.text(f"⚪ Kalk: {fmt_int(f['kalk_verbraucht'])}L | 🌱 Saat: {fmt_int(f['saat_verbraucht'])}L\n🧪 Dünger: {fmt_int(f['dueng_verbraucht'])}L | 🌿 Herbi: {fmt_int(f['herbi_verbraucht'])}L")
                
                if c_act1.button(f"⚪ Kalken ({fmt_int(bedarf_kalk)}L)", key=f"kalk_{idx}"):
                    if st._global_lager_store["kalk"] >= bedarf_kalk:
                        st._global_lager_store["kalk"] -= bedarf_kalk
                        st._global_felder_store[idx]["kalk_verbraucht"] += bedarf_kalk
                        speichere_gesamte_daten()
                        st.success(f"{fmt_int(bedarf_kalk)}L Kalk aus Silo entnommen!")
                        st.rerun()
                    else:
                        st.error("🚨 Nicht genug Kalk im Hof-Bestand!")
                        
                if c_act2.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}"):
                    if st._global_lager_store["saat"] >= bedarf_saat:
                        st._global_lager_store["saat"] -= bedarf_saat
                        st._global_felder_store[idx]["saat_verbraucht"] += bedarf_saat
                        speichere_gesamte_daten()
                        st.success(f"{fmt_int(bedarf_saat)}L Saatgut verbraucht!")
                        st.rerun()
                    else:
                        st.error("🚨 Nicht genug Saatgut im Hof-Bestand!")

                if c_act3.button(f"🧪 Düngen ({fmt_int(bedarf_dueng)}L)", key=f"dueng_{idx}"):
                    if st._global_lager_store["dueng"] >= bedarf_dueng:
                        st._global_lager_store["dueng"] -= bedarf_dueng
                        st._global_felder_store[idx]["dueng_verbraucht"] += bedarf_dueng
                        speichere_gesamte_daten()
                        st.success(f"{fmt_int(bedarf_dueng)}L Dünger verbraucht!")
                        st.rerun()
                    else:
                        st.error("🚨 Nicht genug Dünger im Hof-Bestand!")

                if c_act4.button(f"🔄 Reset Feld", key=f"res_{idx}"):
                    st._global_felder_store[idx]["saat_verbraucht"] = 0.0
                    st._global_felder_store[idx]["dueng_verbraucht"] = 0.0
                    st._global_felder_store[idx]["kalk_verbraucht"] = 0.0
                    st._global_felder_store[idx]["herbi_verbraucht"] = 0.0
                    speichere_gesamte_daten()
                    st.rerun()
                    
        st.write("---")
        c_del1, c_del2 = st.columns([1, 2])
        opt_del = [f["nummer"] for f in st._global_felder_store]
        f_del = c_del1.selectbox("Feld komplett löschen:", options=opt_del)
        if c_del2.button("❌ Feld komplett aus Datenbank entfernen", use_container_width=True):
            st._global_felder_store = [f for f in st._global_felder_store if f["nummer"] != f_del]
            speichere_gesamte_daten()
            st.rerun()

# ---------------------------------------------------------
# SEITE 3: RECHNUNGEN
# ---------------------------------------------------------
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
    st.info(f"Nächste Rechnungsnummer auf dem Server: **#RE-{st._global_finanzen['naechste_rechnung_id']:04d}**")

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
            auswahl = st.selectbox("Maschine / Service aus Google-Sheet:", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
            menge = st.number_input("Gefahrene Stunden (h):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Stunde (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
            einheit_str = "h"
            
        if st.button("➕ Posten zur Rechnung hinzufügen", use_container_width=True):
            if auswahl.strip():
                st.session_state.rechnungs_posten.append({"name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p})
                st.rerun()

    with col_liste:
        st.subheader("Rechnungsdaten & Vorschau")
        k_name = st.selectbox("Empfänger (Kunde):", aktuelle_kunden) if aktuelle_kunden else st.text_input("Empfänger (Hofname):")
        rabatt = st.slider("Rabatt auf Gesamtsumme (%)", 0, 50, 0)
        
        c_m, c_j = st.columns(2)
        re_monat = c_m.selectbox("In-Game Monat:", LISTE_MONATE, key="re_m")
        re_jahr = c_j.number_input("In-Game Jahr:", min_value=1, value=1, key="re_j")

    if st.session_state.rechnungs_posten:
        st.write("---")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        st.dataframe(df_preview[["name", "menge", "einheit", "preis", "gesamt"]], use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        pdf_data = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st._global_finanzen["naechste_rechnung_id"], full_ingame_date)
        
        col_b1, col_b2 = st.columns(2)
        col_b1.download_button("📥 PDF laden", data=pdf_data, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        
        if col_b2.button("💾 Als Einnahme buchen", type="primary", use_container_width=True):
            st._global_finanzen["einnahmen"] += total
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": int(re_jahr), "Sort_Monat": re_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st._global_finanzen['naechste_rechnung_id']:04d}",
                "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            speichere_gesamte_daten()
            st.rerun()

# ---------------------------------------------------------
# SEITE 4: MATERIAL & AUFTRÄGE
# ---------------------------------------------------------
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material & LU-Bestellungen")
    
    tab_lager, tab_auftraege = st.tabs(["📦 Silo & Einkauf", "📝 LU-Auftragsbuch"])
    
    with tab_lager:
        st.subheader("⚙️ Manuelle Lager-Korrektur / Silo-Befüllung")
        c_l1, c_l2, c_l3, c_l4, c_l5 = st.columns(5)
        
        v_saat = c_l1.number_input("Saatgut (L):", min_value=0, value=int(st._global_lager_store["saat"]), step=500)
        v_kalk = c_l2.number_input("Kalk (L):", min_value=0, value=int(st._global_lager_store["kalk"]), step=1000)
        v_dueng = c_l3.number_input
