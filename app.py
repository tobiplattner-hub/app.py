import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# ---------------------------------------------------------
# LS25 ANBAUKALENDER-DATEN (Offizielle In-Game Monate)
# ---------------------------------------------------------
# Definition von Erlaubten Aussaatmonaten (Sa) und Erntemonaten (Er) laut LS25 Standard
LS25_KALENDER = {
    "Weizen": {"sa": [3, 4, 8, 9, 10], "er": [6, 7, 8]},
    "Gerste": {"sa": [8, 9, 10], "er": [5, 6, 7]},
    "Hafer": {"sa": [2, 3, 4], "er": [7, 8]},
    "Raps": {"sa": [7, 8], "er": [6, 7, 8]},
    "Sonnenblumen": {"sa": [3, 4], "er": [9, 10]},
    "Sojabohnen": {"sa": [3, 4, 5], "er": [9, 10, 11]},
    "Mais": {"sa": [3, 4], "er": [9, 10, 11]},
    "Kartoffeln": {"sa": [3, 4], "er": [7, 8, 9, 10]},
    "Zuckerrüben": {"sa": [2, 3, 4], "er": [9, 10, 11]},
    "Gras": {"sa": [2, 3, 4, 8, 9, 10], "er": [3, 4, 5, 6, 7, 8, 9, 10]},
    "Ölrettich": {"sa": [2, 3, 4, 5, 6, 7, 8, 9], "er": []}, # Gründüngung
    "Pappel": {"sa": [2, 3, 4, 5, 6, 7, 8], "er": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 1]},
    "Zuckerrohr": {"sa": [2, 3, 4], "er": [9, 10, 11]},
    "Baumwolle": {"sa": [2, 3], "er": [9, 10]},
    "Reis": {"sa": [3, 4], "er": [8, 9]},
    "Langkornreis": {"sa": [3, 4], "er": [8, 9]},
    "Spinat": {"sa": [2, 3, 7, 8], "er": [4, 5, 9, 10]},
    "Dinkel": {"sa": [8, 9, 10], "er": [6, 7]}
}

LISTE_MONATE = [
    "01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", 
    "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", 
    "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"
]

def extrahiere_monat_int(monat_str):
    try:
        return int(monat_str.split(" - ")[0])
    except:
        return 1

def berechne_erntestatus(frucht,saat_monat_str, aktueller_monat_str):
    if not saat_monat_str or saat_monat_str == "Nicht gesät":
        return "⏳ Brachland / Bereit", "gray"
        
    if frucht not in LS25_KALENDER:
        return "🌾 Unbekannte Frucht (Wachstum manuell prüfen)", "blue"
        
    akt_m = extrahiere_monat_int(aktueller_monat_str)
    kalender = LS25_KALENDER[frucht]
    
    if akt_m in kalender["er"]:
        return "🟢 REIF ZUR ERNTE!", "green"
        
    # Prüfen, ob die Erntezeit für diese Frucht in diesem Jahr schon vorbei ist
    if len(kalender["er"]) > 0 and akt_m > max(kalender["er"]):
        return "🚨 ERNTEZEIT VERPASST! (Gefahr von Verdorren)", "red"
        
    return "🌱 Im Wachstum", "blue"

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
            "Gras", "Ölrettich", "Pappel", "Zuckerrohr", "Baumwolle", "Reis", "Langkornreis", "Spinat", "Dinkel"
        ],
        "finanzen": {
            "start_saldo": 0.0, "einnahmen": 0.0, "ausgaben": 0.0,
            "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []
        },
        "lager_grenzwerte": {"saat": 1000, "kalk": 3000, "dueng": 1000, "herbi": 500, "diesel": 1000},
        "auftrags_store": [],
        "fuhrpark_store": {},
        "aktueller_ingame_monat": "03 - Mrz",
        "aktuelles_ingame_jahr": 1
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
    st.session_state._global_ingame_monat = gespeicherte_daten.get("aktueller_ingame_monat", "03 - Mrz")
    st.session_state._global_ingame_jahr = gespeicherte_daten.get("aktuelles_ingame_jahr", 1)
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
        "fuhrpark_store": st.session_state._global_fuhrpark_store,
        "aktueller_ingame_monat": st.session_state._global_ingame_monat,
        "aktuelles_ingame_jahr": st.session_state._global_ingame_jahr
    }
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(daten_zum_speichern, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Fehler beim Sichern: {e}")

def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items(): txt = txt.replace(r, v)
    return txt

def fmt_int(wert): return f"{wert:,.0f}".replace(",", ".")
def fmt_float(wert):
    try: return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except: return str(wert)

def finde_logo_datei():
    for dateiname in ["logo.png", "logo.png.jpeg", "logo.png.jpg", "logo.jpeg", "logo.jpg", "logo.PNG", "logo.JPEG"]:
        if os.path.exists(dateiname): return dateiname
    return None

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
    total = summe - (summe * (rabatt_prozent / 100))
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    return bytes(pdf.output())

# Google Sheets Anbindung
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
# SIDEBAR LIVE-ANZEIGE & GLOBALE IN-GAME ZEIT
# ---------------------------------------------------------
st.sidebar.title("📅 Globale Hof-Zeit")
c_sb_m, c_sb_j = st.sidebar.columns(2)

try: idx_m = LISTE_MONATE.index(st.session_state._global_ingame_monat)
except: idx_m = 2

neuer_globaler_monat = c_sb_m.selectbox("Aktueller Monat:", LISTE_MONATE, index=idx_m)
neues_globales_jahr = c_sb_j.number_input("Jahr:", min_value=1, value=int(st.session_state._global_ingame_jahr))

if neuer_globaler_monat != st.session_state._global_ingame_monat or neues_globales_jahr != st.session_state._global_ingame_jahr:
    st.session_state._global_ingame_monat = neuer_globaler_monat
    st.session_state._global_ingame_jahr = neues_globales_jahr
    speichere_gesamte_daten()
    st.rerun()

st.sidebar.markdown("---")
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
        st.subheader("⚙️ Standard-Verbrauchsraten")
        st.session_state.global_verbrauch_kalk = st.number_input("Kalk Bedarf (L/ha):", value=st.session_state.global_verbrauch_kalk)
        st.session_state.global_verbrauch_dueng = st.number_input("Dünger Bedarf (L/ha):", value=st.session_state.global_verbrauch_dueng)
        st.session_state.global_verbrauch_saat = st.number_input("Saatgut Bedarf (L/ha):", value=st.session_state.global_verbrauch_saat)
        st.session_state.global_verbrauch_herbi = st.number_input("Herbizid Bedarf (L/ha):", value=st.session_state.global_verbrauch_herbi)
    with col2:
        st.subheader("Anbau- & Ernte-Info (LS25 Referenz)")
        ref_frucht = st.selectbox("Frucht-Steckbrief abrufen:", st.session_state._global_fruchtarten, key="ref_f")
        if ref_frucht in LS25_KALENDER:
            k = LS25_KALENDER[ref_frucht]
            saat_monate = [LISTE_MONATE[m-1] for m in k["sa"]]
            ernte_monate = [LISTE_MONATE[m-1] for m in k["er"]]
            st.info(f"🌱 **Erlaubte Aussaat:** {', '.join(saat_monate) if saat_monate else 'Keine (Spezial)'}  \n🌾 **Erntezeit:** {', '.join(ernte_monate) if ernte_monate else 'Keine (Spezial)'}")
        else:
            st.warning("Für diese Fruchtart wurden manuell erweiterte Daten eingetragen.")

# ---------------------------------------------------------
# SEITE 2: MEINE FELDER & ANBAU (ERWEITERT UM LS25 TIMING)
# ---------------------------------------------------------
elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung mit automatisiertem LS25 Reife-Tracker")
    
    col_feld_ein, col_feld_stats = st.columns([1, 1])
    with col_feld_ein:
        st.subheader("📝 Neues Feld registrieren")
        f_nummer = st.text_input("Feld-ID / Nummer:", placeholder="z.B. Feld 4")
        f_groesse = st.number_input("Feldgröße in Hektar (ha):", min_value=0.01, value=2.0, step=0.1, format="%.2f")
        f_frucht = st.selectbox("Geplante / Aktuelle Frucht:", st.session_state._global_fruchtarten)
        
        if st.button("💾 Feld in Datenbank eintragen", type="primary", use_container_width=True):
            if f_nummer.strip():
                st.session_state._global_felder_store.append({
                    "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                    "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0,
                    "rate_kalk": st.session_state.global_verbrauch_kalk, 
                    "rate_saat": st.session_state.global_verbrauch_saat, 
                    "rate_dueng": st.session_state.global_verbrauch_dueng,
                    "saat_monat": "Nicht gesät"
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
        st.subheader("📋 Wirtschaftskonsole der Felder")
        
        for idx, f in enumerate(st.session_state._global_felder_store):
            aktuelle_frucht = f.get('frucht', 'Weizen')
            s_monat = f.get('saat_monat', 'Nicht gesät')
            
            # Statusberechnung auf Basis des In-Game Datums aus der Sidebar
            status_text, farbe = berechne_erntestatus(aktuelle_frucht, s_monat, st.session_state._global_ingame_monat)
            
            with st.expander(f"🗺️ {f['nummer']} — ({fmt_float(f['groesse'])} ha) — Frucht: {aktuelle_frucht} — [{status_text}]"):
                c_inf, c_change, c_time, c_act1, c_act2, c_del = st.columns([1.5, 1.2, 1.2, 1, 1, 0.8])
                
                bedarf_kalk = f["groesse"] * f.get("rate_kalk", 2000)
                bedarf_saat = f["groesse"] * f.get("rate_saat", 150)
                bedarf_dueng = f["groesse"] * f.get("rate_dueng", 160)
                
                with c_inf:
                    st.markdown(f"**Verbraucht auf Fläche:**  \n⚪ Kalk: {fmt_int(f['kalk_verbraucht'])}L  \n🌱 Saat: {fmt_int(f['saat_verbraucht'])}L  \n🧪 Dünger: {fmt_int(f['dueng_verbraucht'])}L")
                    if farbe == "green": st.success(status_text)
                    elif farbe == "red": st.error(status_text)
                    elif farbe == "blue": st.info(status_text)
                
                with c_change:
                    try: f_index = st.session_state._global_fruchtarten.index(aktuelle_frucht)
                    except: f_index = 0
                    neue_gewaehlte_frucht = st.selectbox("Frucht wechseln:", st.session_state._global_fruchtarten, index=f_index, key=f"ch_f_{idx}")
                    if neue_gewaehlte_frucht != aktuelle_frucht:
                        st.session_state._global_felder_store[idx]["frucht"] = neue_gewaehlte_frucht
                        speichere_gesamte_daten()
                        st.rerun()
                        
                with c_time:
                    liste_saat_optionen = ["Nicht gesät"] + LISTE_MONATE
                    try: s_index = liste_saat_optionen.index(s_monat)
                    except: s_index = 0
                    neuer_saat_monat = st.selectbox("Gesät im Monat:", liste_saat_optionen, index=s_index, key=f"ch_s_{idx}")
                    if neuer_saat_monat != s_monat:
                        st.session_state._global_felder_store[idx]["saat_monat"] = neuer_saat_monat
                        speichere_gesamte_daten()
                        st.rerun()

                if c_act1.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}", use_container_width=True):
                    if st.session_state._global_lager_store.get("saat", 0) >= bedarf_saat:
                        # Überprüfung ob In-Game Monat zur Aussaat passt
                        akt_m_int = extrahiere_monat_int(st.session_state._global_ingame_monat)
                        if aktuelle_frucht in LS25_KALENDER and akt_m_int not in LS25_KALENDER[aktuelle_frucht]["sa"]:
                            st.warning("Laut LS25 Kalender ist jetzt eigentlich keine Aussaatzeit für diese Frucht!")
                        
                        st.session_state._global_lager_store["saat"] -= bedarf_saat
                        st.session_state._global_felder_store[idx]["saat_verbraucht"] += bedarf_saat
                        st.session_state._global_felder_store[idx]["saat_monat"] = st.session_state._global_ingame_monat
                        speichere_gesamte_daten()
                        st.rerun()
                    else: st.error("Zu wenig Saatgut!")
                    
                if c_act2.button(f"🚜 Ernten / Reset", key=f"ernte_{idx}", use_container_width=True):
                    st.session_state._global_felder_store[idx]["saat_monat"] = "Nicht gesät"
                    speichere_gesamte_daten()
                    st.success("Feld erfolgreich geerntet und zurückgesetzt!")
                    st.rerun()
                    
                if c_del.button(f"🗑️ Löschen", key=f"del_f_{idx}", use_container_width=True):
                    st.session_state._global_felder_store.pop(idx)
                    speichere_gesamte_daten()
                    st.rerun()

# Die restlichen Menüpunkte (Rechnungen, Material, LU-Auftragsbuch, Fuhrpark, Kassenbuch) bleiben absolut identisch zum vorherigen fehlerfreien Stand...
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
        full_ingame_date = f"J{st.session_state._global_ingame_jahr}-{st.session_state._global_ingame_monat}"
        if st.session_state.rechnungs_posten:
            for idx, p in enumerate(st.session_state.rechnungs_posten):
                c_p_info, c_p_del = st.columns([5, 1])
                c_p_info.write(f"🔹 **{p['name']}**: {p['menge']} {p['einheit']} x {fmt_float(p['preis'])} € = **{fmt_float(p['gesamt'])} €**")
                if c_p_del.button("🗑️", key=f"del_posten_{idx}"):
                    st.session_state.rechnungs_posten.pop(idx); st.rerun()
    if st.session_state.rechnungs_posten:
        st.write("---")
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        st.markdown(f"### 💵 Endbetrag: {fmt_float(total)} €")
        c_b1, c_b2 = st.columns(2)
        pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st.session_state._global_finanzen.get("naechste_rechnung_id", 1), full_ingame_date)
        c_b1.download_button("📥 PDF generieren", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        if c_b2.button("💾 Als Einnahme buchen", type="primary", use_container_width=True):
            st.session_state._global_finanzen["einnahmen"] += total
            st.session_state._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": int(st.session_state._global_ingame_jahr), "Sort_Monat": st.session_state._global_ingame_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}", "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st.session_state._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            speichere_gesamte_daten(); st.rerun()

elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material-Lagerbestand")
    c_l1, c_l2, c_l3, c_l4, c_l5 = st.columns(5)
    materialien = ["saat", "kalk", "dueng", "herbi", "diesel"]
    werte = {}
    for c, mat in zip([c_l1, c_l2, c_l3, c_l4, c_l5], materialien):
        with c:
            st.markdown(f"### {mat.upper()}")
            werte[f"v_{mat}"] = st.number_input("Bestand (L):", min_value=0, value=int(st.session_state._global_lager_store.get(mat, 0)), key=f"i_v_{mat}")
            werte[f"g_{mat}"] = st.number_input("Grenzwert (L):", min_value=0, value=int(st.session_state._global_lager_grenzwerte.get(mat, 1000)), key=f"i_g_{mat}")
    if st.button("💾 Lagerkonfiguration speichern", use_container_width=True, type="primary"):
        for mat in materialien:
            st.session_state._global_lager_store[mat] = werte[f"v_{mat}"]
            st.session_state._global_lager_grenzwerte[mat] = werte[f"g_{mat}"]
        speichere_gesamte_daten(); st.rerun()

elif menu == "📝 LU-Auftragsbuch":
    st.title("📝 LU-Auftragsbuch")
    col_a, col_b = st.columns([1.1, 1.4])
    with col_a:
        st.subheader("➕ Auftrag erstellen")
        a_kunde = st.selectbox("Kunde:", aktuelle_kunden)
        a_einheit = st.selectbox("Abrechnung:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Stk (Fixpreis)"])
        v_einheit = {"Nach Arbeitsstunden (h)": "h", "Nach Feldfläche (ha)": "ha", "Stk (Fixpreis)": "Stk"}[a_einheit]
        a_feld = st.text_input("Zweck / Ort:")
        if v_einheit == "h":
            masch_auswahl = st.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["Standard"])
            geholter_preis = float(preis_dict.get(masch_auswahl, 50.0))
            if st.button("➕ Maschine hinzufügen"):
                st.session_state.temp_lu_maschinen.append({"name": masch_auswahl, "preis_h": geholter_preis, "anfangs_h": 0.0, "end_h": 0.0})
                st.rerun()
            for t_idx, m in enumerate(st.session_state.temp_lu_maschinen):
                st.write(f"• {m['name']} ({m['preis_h']} €/h)")
        else:
            a_arbeit = st.text_input("Arbeitsschritt:")
            a_menge = st.number_input("Menge:", min_value=0.1, value=1.0)
            a_preis = st.number_input("Preis/Einheit (€):", value=100.0)
        if st.button("💾 Auftrag speichern", type="primary", use_container_width=True):
            if v_einheit == "h" and st.session_state.temp_lu_maschinen:
                st.session_state._global_auftrags_store.append({"kunde": a_kunde, "ort": a_feld, "einheit": "h", "status": "⏳ Ausstehend", "monat": st.session_state._global_ingame_monat, "jahr": st.session_state._global_ingame_jahr, "maschinen": st.session_state.temp_lu_maschinen.copy(), "arbeit": "Maschinenverleih"})
                st.session_state.temp_lu_maschinen = []; speichere_gesamte_daten(); st.rerun()
            elif v_einheit != "h":
                st.session_state._global_auftrags_store.append({"kunde": a_kunde, "ort": a_feld, "arbeit": a_arbeit, "status": "⏳ Ausstehend", "menge": a_menge, "einheit": v_einheit, "preis_einheit": a_preis, "monat": st.session_state._global_ingame_monat, "jahr": st.session_state._global_ingame_jahr, "maschinen": []})
                speichere_gesamte_daten(); st.rerun()
    with col_b:
        st.subheader("📋 Aktive Aufträge")
        for idx, aut in enumerate(st.session_state._global_auftrags_store):
            with st.container(border=True):
                st.write(f"**Kunde:** {aut['kunde']} | **Ort:** {aut['ort']} ({aut['monat']})")
                total_wert = 0.0
                if aut.get('einheit') == "h":
                    for m_idx, m in enumerate(aut['maschinen']):
                        anf = st.number_input(f"Start h ({m['name']})", value=m['anfangs_h'], key=f"anf_{idx}_{m_idx}")
                        end = st.number_input(f"Ende h ({m['name']})", value=max(anf, m['end_h']), key=f"end_{idx}_{m_idx}")
                        if anf != m['anfangs_h'] or end != m['end_h']:
                            st.session_state._global_auftrags_store[idx]['maschinen'][m_idx]['anfangs_h'] = anf
                            st.session_state._global_auftrags_store[idx]['maschinen'][m_idx]['end_h'] = end
                            speichere_gesamte_daten(); st.rerun()
                        total_wert += (end - anf) * m['preis_h']
                else:
                    total_wert = aut['menge'] * aut['preis_einheit']
                st.write(f" Wert: **{fmt_float(total_wert)} €**")
                if st.button("💾 Erledigt & Buchen", key=f"f_j_{idx}", type="primary"):
                    st.session_state._global_finanzen["einnahmen"] += total_wert
                    st.session_state._global_finanzen["historie"].append({"In-Game Datum": f"{aut['monat']}", "Sort_Jahr": aut['jahr'], "Sort_Monat": aut['monat'], "Typ": "Einnahme", "Nummer": f"#LU-{st.session_state._global_finanzen.get('naechste_rechnung_id', 1):04d}", "Details": f"LU Job: {aut['kunde']}", "Betrag (EUR)": total_wert})
                    st.session_state._global_auftrags_store.pop(idx); speichere_gesamte_daten(); st.rerun()

elif menu == "🚛 Fuhrpark-Manager":
    st.title("🚛 Fuhrpark-Manager")
    col_f1, col_f2 = st.columns([1, 1.5])
    with col_f1:
        if preis_dict:
            m_waehlen = st.selectbox("Maschine aktivieren:", options=list(preis_dict.keys()))
            m_h = st.number_input("Betriebsstunden (h):", min_value=0.0, step=0.1)
            if st.button("💾 Hinzufügen", use_container_width=True, type="primary"):
                st.session_state._global_fuhrpark_store[m_waehlen] = m_h
                speichere_gesamte_daten(); st.rerun()
    with col_f2:
        for f_name, f_stunden in list(st.session_state._global_fuhrpark_store.items()):
            with st.container(border=True):
                c_fn, c_fh, c_fdel = st.columns([2.5, 1.5, 0.5])
                c_fn.write(f"**{f_name}**")
                neue_stunden = c_fh.number_input("h", min_value=0.0, value=float(f_stunden), key=f"f_h_{f_name}")
                if neue_stunden != f_stunden:
                    st.session_state._global_fuhrpark_store[f_name] = neue_stunden
                    speichere_gesamte_daten(); st.rerun()
                if c_fdel.button("🗑️", key=f"del_m_{f_name}"):
                    del st.session_state._global_fuhrpark_store[f_name]
                    speichere_gesamte_daten(); st.rerun()

elif menu == "📖 Detailliertes Kassenbuch":
    st.title("📖 Kassenbuch")
    historie_liste = st.session_state._global_finanzen.get("historie", [])
    if historie_liste:
        df_anzeige = pd.DataFrame(historie_liste).iloc[::-1]
        st.dataframe(df_anzeige[["In-Game Datum", "Nummer", "Typ", "Details", "Betrag (EUR)"]], use_container_width=True, hide_index=True)
    else:
        st.info("Keine Buchungen vorhanden.")

speichere_gesamte_daten()
