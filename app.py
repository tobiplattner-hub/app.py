import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import urllib.request
from fpdf import FPDF

# ---------------------------------------------------------
# STYLING & SEITEN-KONFIGURATION
# ---------------------------------------------------------
st.set_page_config(page_title="LS25 LU- & Hof-Manager", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container { background: #f4f6f0; }
    .sidebar .sidebar-content { background: #2e4a23; color: white; }
    h1, h2, h3 { color: #2e4a23; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    div.stButton > button:first-child {
        background-color: #4a7c36; color: white; border-radius: 8px;
        border: none; font-weight: bold; transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover { background-color: #3b632b; transform: scale(1.02); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# GLOBALE KONSTANTEN & HILFSFUNKTIONEN
# ---------------------------------------------------------
LISTE_MONATE = ["März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember", "Januar", "Februar"]

def fmt_float(val): return f"{float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_int(val): return f"{int(val):,}".replace(",", ".")

def extrahiere_monat_int(m_name):
    try: return LISTE_MONATE.index(m_name) + 1
    except: return 1

KALENDER_STANDARD = {
    "Weizen": {"sa": [1, 2], "er": [5, 6]},
    "Gerste": {"sa": [1, 2], "er": [5]},
    "Hafer": {"sa": [1, 2], "er": [5, 6]},
    "Raps": {"sa": [6, 7], "er": [5]},
    "Sojabohnen": {"sa": [2, 3], "er": [7, 8]},
    "Mais": {"sa": [2, 3], "er": [7, 8, 9]},
    "Kartoffeln": {"sa": [2, 3], "er": [6, 7, 8]},
    "Zuckerrüben": {"sa": [1, 2], "er": [7, 8, 9]},
    "Gras": {"sa": [1, 2, 3, 4, 5, 6, 7, 8], "er": [2, 3, 4, 5, 6, 7, 8, 9]}
}

def berechne_erntestatus(frucht, saat_monat, aktueller_monat_name, manueller_status):
    if manueller_status != "Automatisch (Kalender)":
        farbe = "🟢" if "REIF" in manueller_status else ("🌱" if "Wachstum" in manueller_status else "⏳")
        return manueller_status, farbe
    if saat_monat == "Nicht gesät":
        return "⏳ Brachland / Bereit", "⏳"
        
    cust_k = st.session_state.get("_global_custom_kalender", {})
    if frucht in cust_k: k_daten = cust_k[frucht]
    else: k_daten = KALENDER_STANDARD.get(frucht, {"sa": [], "er": []})
    
    idx_saat = LISTE_MONATE.index(saat_monat) + 1
    idx_jetzt = LISTE_MONATE.index(aktueller_monat_name) + 1
    
    if idx_jetzt in k_daten["er"]: return "🟢 REIF ZUR ERNTE!", "🟢"
    if idx_jetzt in k_daten["sa"]: return "🌱 Frisch gesät / Keimung", "🌱"
    
    if idx_jetzt > idx_saat:
        moegliche_ernte = [e for e in k_daten["er"] if e >= idx_saat]
        if moegliche_ernte and idx_jetzt > max(moegliche_ernte): return "🚨 ERNTEZEIT VERPASST!", "🚨"
        return "🌱 Im Wachstum", "🌱"
    elif idx_jetzt < idx_saat:
        return "🌱 Im Wachstum (Überwinterung)", "🌱"
    return "🌱 Im Wachstum", "🌱"

def generate_invoice_pdf(kunde, posten, rabatt, rechnungs_id, ingame_date, herkunft_hof):
    def clean_str(s):
        if not s: return ""
        s = str(s).replace("—", "-").replace("–", "-").replace("€", "EUR")
        return s.encode("latin-1", errors="ignore").decode("latin-1")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    clean_hof = clean_str(herkunft_hof).upper()
    clean_kunde = clean_str(kunde)
    clean_date = clean_str(ingame_date)
    
    pdf.cell(190, 10, f"RECHNUNG - {clean_hof}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 5, f"In-Game Datum: {clean_date} | ID: #RE-{rechnungs_id:04d}", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 10, f"Empfaenger / Kunde: {clean_kunde}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(80, 8, "Posten / Dienstleistung", border=1)
    pdf.cell(30, 8, "Menge", border=1, align="C")
    pdf.cell(40, 8, "Einzelpreis", border=1, align="R")
    pdf.cell(40, 8, "Gesamt", border=1, align="R")
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    summe = 0
    for p in posten:
        name_clean = clean_str(p["name"])
        pdf.cell(80, 8, name_clean, border=1)
        pdf.cell(30, 8, f"{p['menge']} {clean_str(p['einheit'])}", border=1, align="C")
        pdf.cell(40, 8, f"{fmt_float(p['preis'])} EUR", border=1, align="R")
        pdf.cell(40, 8, f"{fmt_float(p['gesamt'])} EUR", border=1, align="R")
        pdf.ln()
        summe += p["gesamt"]
        
    total = summe - (summe * (rabatt / 100))
    pdf.ln(5)
    if rabatt > 0:
        pdf.cell(150, 8, "Zwischensumme:", align="R")
        pdf.cell(40, 8, f"{fmt_float(summe)} EUR", align="R", ln=True)
        pdf.cell(150, 8, f"Rabatt ({rabatt}%):", align="R")
        pdf.cell(40, 8, f"-{fmt_float(summe*(rabatt/100))} EUR", align="R", ln=True)
        
    pdf.set_font("Arial", "B", 12)
    pdf.cell(150, 10, "ENDSUMME:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    
    try: pdf_out = pdf.output(dest="S")
    except: pdf_out = pdf.output()
        
    if isinstance(pdf_out, str): return pdf_out.encode("latin-1", errors="ignore")
    return bytes(pdf_out)

# ---------------------------------------------------------
# DATA-LOADING (LIVE AUS DEINER GOOGLE SHEET)
# ---------------------------------------------------------
@st.cache_data(ttl=5)
def load_data(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            df = pd.read_csv(response)
        return df
    except Exception as e:
        st.sidebar.error(f"Sheets-Verbindung fehlgeschlagen: {e}")
        return pd.DataFrame()

TABELLEN_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"

# Import-Links für die jeweiligen Datenblätter generieren
sheet_url_preise = f"https://docs.google.com/spreadsheets/d/{TABELLEN_ID}/export?format=csv&gid=0"
sheet_url_kunden = f"https://docs.google.com/spreadsheets/d/{TABELLEN_ID}/export?format=csv&gid=568043650"

df_preise = load_data(sheet_url_preise)
df_kunden = load_data(sheet_url_kunden)

# Verarbeiten der Preisliste
preis_dict = {}
if not df_preise.empty and "geraet" in df_preise.columns and "preis" in df_preise.columns:
    for _, row in df_preise.dropna(subset=["geraet"]).iterrows():
        preis_dict[str(row["geraet"]).strip()] = float(row["preis"])

# Verarbeiten der Kundenliste
aktuelle_kunden = ["Hof 1", "Hof 2", "Hof 3 Extern", "Landi AG", "Zuckerfabrik"]
if not df_kunden.empty and "name" in df_kunden.columns:
    aktuelle_kunden = df_kunden["name"].dropna().astype(str).tolist()

# ---------------------------------------------------------
# INITIALISIERUNG DES SESSION STATES
# ---------------------------------------------------------
if "_global_custom_kalender" not in st.session_state: st.session_state._global_custom_kalender = {}
if "_global_fruchtarten" not in st.session_state: st.session_state._global_fruchtarten = sorted(list(KALENDER_STANDARD.keys()))
if "_global_ingame_monat" not in st.session_state: st.session_state._global_ingame_monat = "März"
if "_global_ingame_jahr" not in st.session_state: st.session_state._global_ingame_jahr = 1
if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []
if "temp_lu_maschinen" not in st.session_state: st.session_state.temp_lu_maschinen = []

if "hof1_name_custom" not in st.session_state: st.session_state.hof1_name_custom = "Hof 1 - Hauptbetrieb"
if "hof2_name_custom" not in st.session_state: st.session_state.hof2_name_custom = "Hof 2 - Bio-Betrieb"
if "hof3_name_custom" not in st.session_state: st.session_state.hof3_name_custom = "Hof 3 - Freier Verbund"

if "_global_hoefe" not in st.session_state:
    st.session_state._global_hoefe = {
        st.session_state.hof1_name_custom: {
            "finanzen": {"einnahmen": 500000.0, "ausgaben": 0.0, "historie": [], "naechste_rechnung_id": 1},
            "lager_store": {"saat": 5000, "kalk": 10000, "dueng": 4000, "herbi": 2000, "diesel": 5000, "frischgut": 0, "silage": 0},
            "lager_grenzwerte": {"saat": 1000, "kalk": 2000, "dueng": 1000, "herbi": 500, "diesel": 1000, "frischgut": 2000, "silage": 2000},
            "felder_store": [], "auftrags_store": [], "fuhrpark_store": {}, "silos": []
        },
        st.session_state.hof2_name_custom: {
            "finanzen": {"einnahmen": 350000.0, "ausgaben": 0.0, "historie": [], "naechste_rechnung_id": 1},
            "lager_store": {"saat": 3000, "kalk": 6000, "dueng": 2000, "herbi": 0, "diesel": 3000, "frischgut": 0, "silage": 0},
            "lager_grenzwerte": {"saat": 800, "kalk": 1500, "dueng": 500, "herbi": 0, "diesel": 800, "frischgut": 2000, "silage": 2000},
            "felder_store": [], "auftrags_store": [], "fuhrpark_store": {}, "silos": []
        },
        st.session_state.hof3_name_custom: {
            "finanzen": {"einnahmen": 200000.0, "ausgaben": 0.0, "historie": [], "naechste_rechnung_id": 1},
            "lager_store": {"saat": 2000, "kalk": 4000, "dueng": 1500, "herbi": 1000, "diesel": 2000, "frischgut": 0, "silage": 0},
            "lager_grenzwerte": {"saat": 500, "kalk": 1000, "dueng": 500, "herbi": 200, "diesel": 500, "frischgut": 2000, "silage": 2000},
            "felder_store": [], "auftrags_store": [], "fuhrpark_store": {}, "silos": []
        }
    }

# ---------------------------------------------------------
# SIDEBAR: MANAGEMENT & SWITCHER
# ---------------------------------------------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2760/2760010.png", width=70)
st.sidebar.title("🚜 LS25 Control Center")

st.sidebar.subheader("📝 Hofnamen anpassen")

alter_hof1 = st.session_state.hof1_name_custom
neuer_hof1 = st.sidebar.text_input("Name Hof 1:", value=alter_hof1)
if neuer_hof1.strip() and neuer_hof1 != alter_hof1:
    st.session_state._global_hoefe[neuer_hof1] = st.session_state._global_hoefe.pop(alter_hof1)
    st.session_state.hof1_name_custom = neuer_hof1
    st.rerun()

alter_hof2 = st.session_state.hof2_name_custom
neuer_hof2 = st.sidebar.text_input("Name Hof 2:", value=alter_hof2)
if neuer_hof2.strip() and neuer_hof2 != alter_hof2:
    st.session_state._global_hoefe[neuer_hof2] = st.session_state._global_hoefe.pop(alter_hof2)
    st.session_state.hof2_name_custom = neuer_hof2
    st.rerun()

alter_hof3 = st.session_state.hof3_name_custom
neuer_hof3 = st.sidebar.text_input("Name Hof 3:", value=alter_hof3)
if neuer_hof3.strip() and neuer_hof3 != alter_hof3:
    st.session_state._global_hoefe[neuer_hof3] = st.session_state._global_hoefe.pop(alter_hof3)
    st.session_state.hof3_name_custom = neuer_hof3
    st.rerun()

st.sidebar.write("---")

liste_hoefe = list(st.session_state._global_hoefe.keys())
if akt_hof_name := st.sidebar.selectbox("🎯 Aktiven Hof verwalten:", liste_hoefe):
    hof_daten = st.session_state._global_hoefe[akt_hof_name]
else:
    st.stop()

st.sidebar.write("---")

st.sidebar.subheader("📅 Globale Betriebszeit")
c_t1, c_t2 = st.sidebar.columns(2)
j_alt = st.session_state._global_ingame_jahr
m_alt = st.session_state._global_ingame_monat

neues_jahr = c_t1.number_input("Jahr:", min_value=1, value=int(j_alt))
neuer_monat = c_t2.selectbox("Monat:", LISTE_MONATE, index=LISTE_MONATE.index(m_alt))

if neues_jahr != j_alt or neuer_monat != m_alt:
    st.session_state._global_ingame_jahr = neues_jahr
    st.session_state._global_ingame_monat = neuer_monat
    st.rerun()

st.sidebar.write("---")

kontostand = hof_daten["finanzen"]["einnahmen"] - hof_daten["finanzen"]["ausgaben"]
st.sidebar.metric("💰 Kontostand (Aktuell)", f"{fmt_float(kontostand)} €")

st.sidebar.subheader("📦 Lager-Warnungen")
for mat, menge in hof_daten["lager_store"].items():
    grenze = hof_daten["lager_grenzwerte"].get(mat, 1000)
    if menge <= grenze:
        st.sidebar.warning(f"⚠️ {mat.upper()}: {fmt_int(menge)}L (Limit: {fmt_int(grenze)}L)")

st.sidebar.write("---")

menu = st.sidebar.radio("Navigation", [
    "💰 Ernte & Verbrauchsraten",
    "🚜 Meine Felder & Anbau",
    "📋 Rechnungen",
    "🛒 Material & Aufträge",
    "🏗️ Silo-Manager",
    "📝 LU-Auftragsbuch",
    "🛒 Fuhrpark-Manager",
    "📖 Detailliertes Kassenbuch"
])

if "global_verbrauch_kalk" not in st.session_state: st.session_state.global_verbrauch_kalk = 2000
if "global_verbrauch_saat" not in st.session_state: st.session_state.global_verbrauch_saat = 150
if "global_verbrauch_dueng" not in st.session_state: st.session_state.global_verbrauch_dueng = 180
if "global_verbrauch_herbi" not in st.session_state: st.session_state.global_verbrauch_herbi = 100

# ---------------------------------------------------------
# SEITE 1: ERNTE & VERBRAUCHSRATEN
# ---------------------------------------------------------
if menu == "💰 Ernte & Verbrauchsraten":
    st.title(f"💰 Ernteverkauf & Verbrauchs-Mittelung - {akt_hof_name}")
    
    with st.expander("⚙️ Globale Standard-Verbrauchsraten anpassen (pro Hektar)"):
        cl1, cl2, cl3, cl4 = st.columns(4)
        st.session_state.global_verbrauch_kalk = cl1.number_input("Kalk (L/ha):", value=st.session_state.global_verbrauch_kalk, step=50)
        st.session_state.global_verbrauch_saat = cl2.number_input("Saatgut (L/ha):", value=st.session_state.global_verbrauch_saat, step=10)
        st.session_state.global_verbrauch_dueng = cl3.number_input("Dünger (L/ha):", value=st.session_state.global_verbrauch_dueng, step=10)
        st.session_state.global_verbrauch_herbi = cl4.number_input("Herbizid (L/ha):", value=st.session_state.global_verbrauch_herbi, step=10)

    col_links, col_rechts = st.columns([1.1, 0.9])
    
    with col_links:
        st.subheader("🌾 Fruchtart-Steckbrief & Kalenderdaten")
        f_auswahl = st.selectbox("Fruchtart wählen:", st.session_state._global_fruchtarten)
        cust_k = st.session_state._global_custom_kalender
        
        if f_auswahl in cust_k:
            saat_monate = [LISTE_MONATE[i-1] for i in cust_k[f_auswahl]["sa"]]
            ernte_monate = [LISTE_MONATE[i-1] for i in cust_k[f_auswahl]["er"]]
            st.info(f"Mod-Fruchtart '{f_auswahl}' aktiv.")
        else:
            s_idx = KALENDER_STANDARD.get(f_auswahl, {"sa":[]})["sa"]
            e_idx = KALENDER_STANDARD.get(f_auswahl, {"er":[]})["er"]
            saat_monate = [LISTE_MONATE[i-1] for i in s_idx]
            ernte_monate = [LISTE_MONATE[i-1] for i in e_idx]
            
        st.markdown(f"**Optimaler Aussaatzeitraum:** {', '.join(saat_monate) if saat_monate else 'Keine Angabe'}")
        st.markdown(f"**Optimaler Erntezeitraum:** {', '.join(ernte_monate) if ernte_monate else 'Keine Angabe'}")
        
    with col_rechts:
        st.subheader("💵 Waren-Verkaufsrechner & Kassenbuchung")
        v_menge = st.number_input("Verkaufte Menge (Liter):", min_value=0, value=10000, step=1000)
        v_preis = st.number_input("Erlös pro 1.000 Liter (€):", min_value=0.0, value=850.0, step=50.0)
        v_details = st.text_input("Abnehmer / Station:", placeholder="z.B. Getreidemühle West")
        
        erloes = (v_menge / 1000.0) * v_preis
        st.markdown(f"### Berechneter Erlös: **{fmt_float(erloes)} €**")
        
        if st.button("💾 Erlös direkt ins Kassenbuch einbuchen", type="primary", use_container_width=True):
            f_date = f"J{st.session_state._global_ingame_jahr}-{st.session_state._global_ingame_monat}"
            hof_daten["finanzen"]["einnahmen"] += erloes
            hof_daten["finanzen"]["historie"].append({
                "In-Game Datum": f_date, "Sort_Jahr": int(st.session_state._global_ingame_jahr), "Sort_Monat": st.session_state._global_ingame_monat,
                "Typ": "Einnahme", "Nummer": f"#VK-{os.urandom(2).hex().upper()}", "Details": f"Verkauf {v_menge}L {f_auswahl} ({v_details})", "Betrag (EUR)": erloes
            })
            st.success(f"Erfolgreich gebucht! + {fmt_float(erloes)} €")
            st.rerun()

# ---------------------------------------------------------
# SEITE 2: MEINE FELDER & ANBAU
# ---------------------------------------------------------
elif menu == "🚜 Meine Felder & Anbau":
    st.title(f"🚜 Feld-Verwaltung & Kalender - {akt_hof_name}")
    
    with st.expander("✨ Neue Mod-Fruchtart definieren"):
        c_nf1, c_nf2, c_nf3 = st.columns([1.5, 2, 2])
        neue_frucht_name = c_nf1.text_input("Name der Mod-Frucht:", placeholder="z.B. Senf")
        saat_monate_auswahl = c_nf2.multiselect("Sämonate:", LISTE_MONATE, key="cust_saat")
        ernte_monate_auswahl = c_nf3.multiselect("Erntemonate:", LISTE_MONATE, key="cust_ernte")
        
        if st.button("💾 Fruchtart im System registrieren", use_container_width=True):
            if neue_frucht_name.strip():
                f_name = neue_frucht_name.strip()
                st.session_state._global_custom_kalender[f_name] = {
                    "sa": [extrahiere_monat_int(m) for m in saat_monate_auswahl], 
                    "er": [extrahiere_monat_int(m) for m in ernte_monate_auswahl]
                }
                if f_name not in st.session_state._global_fruchtarten:
                    st.session_state._global_fruchtarten.append(f_name)
                    st.session_state._global_fruchtarten.sort()
                st.success(f"Frucht '{f_name}' registriert!"); st.rerun()

    st.write("---")
    col_feld_ein, col_feld_stats = st.columns([1.2, 0.8])
    with col_feld_ein:
        st.subheader("📝 Neues Feld registrieren")
        cx1, cx2 = st.columns(2)
        f_nummer = cx1.text_input("Feld-ID / Nummer:")
        f_groesse = cx2.number_input("Größe (ha):", min_value=0.01, value=2.0, step=0.1, format="%.2f")
        f_frucht = st.selectbox("Aktuelle Frucht:", st.session_state._global_fruchtarten)
            
        if st.button("💾 Feld eintragen", type="primary", use_container_width=True):
            if f_nummer.strip():
                hof_daten["felder_store"].append({
                    "nummer": f_nummer.strip(), "groesse": f_groesse, "frucht": f_frucht,
                    "saat_verbraucht": 0.0, "dueng_verbraucht": 0.0, "kalk_verbraucht": 0.0, "herbi_verbraucht": 0.0,
                    "rate_kalk": st.session_state.global_verbrauch_kalk, "rate_saat": st.session_state.global_verbrauch_saat, "rate_dueng": st.session_state.global_verbrauch_dueng,
                    "saat_monat": "Nicht gesät", "manueller_status": "Automatisch (Kalender)"
                })
                st.rerun()

    with col_feld_stats:
        st.subheader("📊 Betriebszusammenfassung")
        if hof_daten["felder_store"]:
            st.metric("Gesamtfläche unter Bewirtschaftung", f"{fmt_float(sum(f['groesse'] for f in hof_daten['felder_store']))} ha")
        else: st.info("Keine Felder für diesen Hof.")

    if hof_daten["felder_store"]:
        st.write("---")
        for idx, f in enumerate(hof_daten["felder_store"]):
            aktuelle_frucht = f.get('frucht', 'Weizen')
            s_monat = f.get('saat_monat', 'Nicht gesät')
            m_status = f.get('manueller_status', 'Automatisch (Kalender)')
            status_text, farbe = berechne_erntestatus(aktuelle_frucht, s_monat, st.session_state._global_ingame_monat, m_status)
            
            with st.expander(f"🗺️ {f['nummer']} - ({fmt_float(f['groesse'])} ha) - [{status_text}]"):
                c_inf, c_change, c_time, c_manual_state, c_act1, c_act2, c_del = st.columns([1.5, 1.3, 1.2, 1.3, 0.9, 0.9, 0.6])
                bedarf_saat = f["groesse"] * f.get("rate_saat", 150)
                
                with c_inf:
                    st.markdown(f"**Verbrauch:**  \n⚪ Kalk: {fmt_int(f['kalk_verbraucht'])}L  \n🌱 Saat: {fmt_int(f['saat_verbraucht'])}L")
                with c_change:
                    ch_opt = st.selectbox("Frucht wechseln:", st.session_state._global_fruchtarten, index=st.session_state._global_fruchtarten.index(aktuelle_frucht) if aktuelle_frucht in st.session_state._global_fruchtarten else 0, key=f"ch_{idx}")
                    if ch_opt != aktuelle_frucht: hof_daten["felder_store"][idx]["frucht"] = ch_opt; st.rerun()
                with c_time:
                    neuer_saat_monat = st.selectbox("Gesät im:", ["Nicht gesät"] + LISTE_MONATE, index=(["Nicht gesät"] + LISTE_MONATE).index(s_monat) if s_monat in (["Nicht gesät"] + LISTE_MONATE) else 0, key=f"chs_{idx}")
                    if neuer_saat_monat != s_monat: hof_daten["felder_store"][idx]["saat_monat"] = neuer_saat_monat; st.rerun()
                with c_manual_state:
                    neuer_m_status = st.selectbox("Status-Override:", ["Automatisch (Kalender)", "🌱 Im Wachstum", "🟢 REIF ZUR ERNTE!", "⏳ Brachland / Bereit", "🚨 ERNTEZEIT VERPASST!"], index=["Automatisch (Kalender)", "🌱 Im Wachstum", "🟢 REIF ZUR ERNTE!", "⏳ Brachland / Bereit", "🚨 ERNTEZEIT VERPASST!"].index(m_status) if m_status in ["Automatisch (Kalender)", "🌱 Im Wachstum", "🟢 REIF ZUR ERNTE!", "⏳ Brachland / Bereit", "🚨 ERNTEZEIT VERPASST!"] else 0, key=f"chm_{idx}")
                    if neuer_m_status != m_status: hof_daten["felder_store"][idx]["manueller_status"] = neuer_m_status; st.rerun()

                if c_act1.button(f"🌱 Säen ({fmt_int(bedarf_saat)}L)", key=f"saat_{idx}", use_container_width=True):
                    if hof_daten["lager_store"].get("saat", 0) >= bedarf_saat:
                        hof_daten["lager_store"]["saat"] -= bedarf_saat
                        hof_daten["felder_store"][idx]["saat_verbraucht"] += bedarf_saat
                        hof_daten["felder_store"][idx]["saat_monat"] = st.session_state._global_ingame_monat
                        st.rerun()
                    else: st.error("Zu wenig Saatgut!")
                if c_act2.button(f"🚜 Ernte", key=f"ernte_{idx}", use_container_width=True):
                    hof_daten["felder_store"][idx]["saat_monat"] = "Nicht gesät"
                    hof_daten["felder_store"][idx]["manueller_status"] = "Automatisch (Kalender)"
                    st.success("Feld zurückgesetzt!"); st.rerun()
                if c_del.button("🗑️", key=f"d_{idx}", use_container_width=True): hof_daten["felder_store"].pop(idx); st.rerun()

# ---------------------------------------------------------
# SEITE 3: RECHNUNGEN
# ---------------------------------------------------------
elif menu == "📋 Rechnungen":
    st.title(f"📋 Rechnungs-Zentrale - Erstellt von: {akt_hof_name}")
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
            auswahl = st.selectbox("Maschine/Gerät:", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
            menge = st.number_input("Stunden (h):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Stunde (€/h):", value=float(preis_dict.get(auswahl, 75.0)) if preis_dict else 75.0)
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
        
        ziel_konto = st.selectbox("🎯 Geldeingang verbuchen auf Konto:", liste_hoefe, index=liste_hoefe.index(akt_hof_name))
        
        if st.session_state.rechnungs_posten:
            for idx, p in enumerate(st.session_state.rechnungs_posten):
                c_p_info, c_p_del = st.columns([5, 1])
                c_p_info.write(f"🔹 **{p['name']}**: {p['menge']} {p['einheit']} = **{fmt_float(p['gesamt'])} €**")
                if c_p_del.button("🗑️", key=f"del_posten_{idx}"): st.session_state.rechnungs_posten.pop(idx); st.rerun()
                
    if st.session_state.rechnungs_posten:
        st.write("---")
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe - (summe * (rabatt / 100))
        st.markdown(f"### 💵 Endbetrag: {fmt_float(total)} €")
        c_b1, c_b2 = st.columns(2)
        
        pdf_bytes = generate_invoice_pdf(k_name, st.session_state.rechnungs_posten, rabatt, hof_daten["finanzen"].get("naechste_rechnung_id", 1), full_ingame_date, herkunft_hof=akt_hof_name)
        c_b1.download_button("📥 PDF generieren", data=pdf_bytes, file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        
        if c_b2.button("💾 Auf gewähltes Konto buchen", type="primary", use_container_width=True):
            tgt_hof = st.session_state._global_hoefe[ziel_konto]
            tgt_hof["finanzen"]["einnahmen"] += total
            tgt_hof["finanzen"]["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": int(st.session_state._global_ingame_jahr), "Sort_Monat": st.session_state._global_ingame_monat, 
                "Typ": "Einnahme", "Nummer": f"#RE-{hof_daten['finanzen'].get('naechste_rechnung_id', 1):04d}", 
                "Details": f"Kunde: {k_name} (Erstellt durch {akt_hof_name})", "Betrag (EUR)": total
            })
            hof_daten["finanzen"]["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.rerun()

# ---------------------------------------------------------
# SEITE 4: MATERIAL & AUFTRÄGE
# ---------------------------------------------------------
elif menu == "🛒 Material & Aufträge":
    st.title(f"🛒 Material-Lagerbestand - {akt_hof_name}")
    
    if "frischgut" not in hof_daten["lager_store"]: hof_daten["lager_store"]["frischgut"] = 0
    if "silage" not in hof_daten["lager_store"]: hof_daten["lager_store"]["silage"] = 0

    materialien = ["saat", "kalk", "dueng", "herbi", "diesel", "frischgut", "silage"]
    
    st.subheader("📦 Aktuelle Lagerbestände")
    rows = [materialien[i:i + 4] for i in range(0, len(materialien), 4)]
    werte = {}
    
    for row in rows:
        cols = st.columns(len(row))
        for c, mat in zip(cols, row):
            with c:
                st.markdown(f"**{mat.upper()}**")
                werte[f"v_{mat}"] = st.number_input("Bestand (L):", min_value=0, value=int(hof_daten["lager_store"].get(mat, 0)), key=f"i_v_{mat}")
                werte[f"g_{mat}"] = st.number_input("Grenzwert (L):", min_value=0, value=int(hof_daten["lager_grenzwerte"].get(mat, 1000)), key=f"i_g_{mat}")
    
    if st.button("💾 Lagerkonfiguration保存", use_container_width=True, type="primary"):
        for mat in materialien:
            hof_daten["lager_store"][mat] = werte[f"v_{mat}"]
            hof_daten["lager_grenzwerte"][mat] = werte[f"g_{mat}"]
        st.success("Lagerbestände erfolgreich aktualisiert!")
        st.rerun()

# ---------------------------------------------------------
# SEITE 5: SILO-MANAGER
# ---------------------------------------------------------
elif menu == "🏗️ Silo-Manager":
    st.title(f"🏗️ Fahrsilo-Zentrale (Gärprozess) - {akt_hof_name}")
    
    if "silage" not in hof_daten["lager_store"]: hof_daten["lager_store"]["silage"] = 0
    if "frischgut" not in hof_daten["lager_store"]: hof_daten["lager_store"]["frischgut"] = 0
    if "silos" not in hof_daten: hof_daten["silos"] = []

    col_s1, col_s2 = st.columns([1, 1.5])
    
    with col_s1:
        st.markdown("### ➕ Neues Silo befüllen")
        silo_menge = st.number_input("Menge an Frischgut (L):", min_value=100, step=500, value=5000)
        silo_typ = st.selectbox("Typ:", ["Maissilage", "Grassilage"])
        gaer_dauer = st.slider("Benötigte Gärmonate:", 1, 4, 2)
        
        if st.button("🚀 Silo schließen & gären lassen", use_container_width=True):
            if hof_daten["lager_store"]["frischgut"] >= silo_menge:
                hof_daten["lager_store"]["frischgut"] -= silo_menge
                hof_daten["silos"].append({
                    "id": f"SILO-{os.urandom(1).hex().upper()}",
                    "menge": silo_menge,
                    "typ": silo_typ,
                    "start_monat": st.session_state._global_ingame_monat,
                    "start_jahr": int(st.session_state._global_ingame_jahr),
                    "dauer_monate": gaer_dauer,
                    "geoeffnet": False
                })
                st.success("Silo erfolgreich verdichtet!")
                st.rerun()
            else: st.error("Nicht genug Frischgut im Lager!")

    with col_s2:
        st.markdown("### 📐 Laufende Gärprozesse")
        if not hof_daten["silos"]: st.info("Aktuell keine aktiven Silos vorhanden.")
        else:
            current_month_idx = LISTE_MONATE.index(st.session_state._global_ingame_monat)
            current_year = int(st.session_state._global_ingame_jahr)
            
            for idx, silo in enumerate(hof_daten["silos"]):
                start_month_idx = LISTE_MONATE.index(silo["start_monat"])
                start_year = silo["start_jahr"]
                vergangene_monate = (current_year - start_year) * 12 + (current_month_idx - start_month_idx)
                
                progress = min(1.0, max(0.0, vergangene_monate / silo["dauer_monate"]))
                fertig = vergangene_monate >= silo["dauer_monate"]
                
                with st.container(border=True):
                    st.markdown(f"**Silo ID: {silo['id']}** ({silo['typ']})")
                    st.write(f"Menge: {fmt_int(silo['menge'])} Liter")
                    
                    if fertig:
                        st.success("🟢 REIF! Die Silage ist fertig gegoren.")
                        if st.button("📥 Silo öffnen & ins Lager umbuchen", key=f"open_silo_{idx}", use_container_width=True):
                            hof_daten["lager_store"]["silage"] += silo["menge"]
                            hof_daten["silos"].pop(idx)
                            st.rerun()
                    else:
                        st.warning(f"⏳ Gärt noch... ({int(progress * 100)}%)")
                        st.progress(progress)
                        if st.button("🗑️ Silo verwerfen", key=f"del_silo_{idx}"):
                            hof_daten["silos"].pop(idx)
                            st.rerun()

# ---------------------------------------------------------
# SEITE 6: LU-AUFTRAGSBUCH
# ---------------------------------------------------------
elif menu == "📝 LU-Auftragsbuch":
    st.title(f"📝 LU-Auftragsbuch - {akt_hof_name}")
    col_a, col_b = st.columns([1.1, 1.4])
    with col_a:
        st.subheader("➕ Auftrag erstellen")
        a_kunde = st.selectbox("Kunde:", aktuelle_kunden)
        a_einheit = st.selectbox("Abrechnung:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Stk (Fixpreis)"])
        v_einheit = {"Nach Arbeitsstunden (h)": "h", "Nach Feldfläche (ha)": "ha", "Stk (Fixpreis)": "Stk"}[a_einheit]
        a_feld = st.text_input("Zweck / Ort:")
        if v_einheit == "h":
            masch_auswahl = st.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["Standard"])
            if st.button("➕ Maschine hinzufügen"):
                st.session_state.temp_lu_maschinen.append({"name": masch_auswahl, "preis_h": float(preis_dict.get(masch_auswahl, 50.0)), "anfangs_h": 0.0, "end_h": 0.0})
                st.rerun()
            for m in st.session_state.temp_lu_maschinen: st.write(f"• {m['name']} ({m['preis_h']} €/h)")
        else:
            a_arbeit = st.text_input("Arbeitsschritt:")
            a_menge = st.number_input("Menge:", min_value=0.1, value=1.0)
            a_preis = st.number_input("Preis/Einheit (€):", value=100.0)
            
        if st.button("💾 Auftrag speichern", type="primary", use_container_width=True):
            if v_einheit == "h" and st.session_state.temp_lu_maschinen:
                hof_daten["auftrags_store"].append({"kunde": a_kunde, "ort": a_feld, "einheit": "h", "status": "⏳ Ausstehend", "monat": st.session_state._global_ingame_monat, "jahr": st.session_state._global_ingame_jahr, "maschinen": st.session_state.temp_lu_maschinen.copy(), "arbeit": "Maschinenverleih"})
                st.session_state.temp_lu_maschinen = []; st.rerun()
            elif v_einheit != "h":
                hof_daten["auftrags_store"].append({"kunde": a_kunde, "ort": a_feld, "arbeit": a_arbeit, "status": "⏳ Ausstehend", "menge": a_menge, "einheit": v_einheit, "preis_einheit": a_preis, "monat": st.session_state._global_ingame_monat, "jahr": st.session_state._global_ingame_jahr, "maschinen": []})
                st.rerun()
                
    with col_b:
        st.subheader("📋 Aktive Aufträge")
        for idx, aut in enumerate(hof_daten["auftrags_store"]):
            with st.container(border=True):
                st.write(f"**Kunde:** {aut['kunde']} | **Ort:** {aut['ort']}")
                total_wert = 0.0
                if aut.get('einheit') == "h":
                    for m_idx, m in enumerate(aut['maschinen']):
                        anf = st.number_input(f"Start h ({m['name']})", value=m['anfangs_h'], key=f"anf_{idx}_{m_idx}")
                        end = st.number_input(f"Ende h ({m['name']})", value=max(anf, m['end_h']), key=f"end_{idx}_{m_idx}")
                        if anf != m['anfangs_h'] or end != m['end_h']:
                            hof_daten["auftrags_store"][idx]['maschinen'][m_idx]['anfangs_h'] = anf
                            hof_daten["auftrags_store"][idx]['maschinen'][m_idx]['end_h'] = end
                            st.rerun()
                        total_wert += (end - anf) * m['preis_h']
                else: total_wert = aut['menge'] * aut['preis_einheit']
                st.write(f"Wert: **{fmt_float(total_wert)} €**")
                
                lu_ziel = st.selectbox("Einnahme buchen auf:", liste_hoefe, index=liste_hoefe.index(akt_hof_name), key=f"lu_tgt_{idx}")
                
                if st.button("💾 Erledigt & Buchen", key=f"f_j_{idx}", type="primary"):
                    st.session_state._global_hoefe[lu_ziel]["finanzen"]["einnahmen"] += total_wert
                    st.session_state._global_hoefe[lu_ziel]["finanzen"]["historie"].append({"In-Game Datum": f"{aut['monat']}", "Sort_Jahr": aut['jahr'], "Sort_Monat": aut['monat'], "Typ": "Einnahme", "Nummer": f"#LU-{os.urandom(2).hex().upper()}", "Details": f"LU Job abgeschlossen ({akt_hof_name})", "Betrag (EUR)": total_wert})
                    hof_daten["auftrags_store"].pop(idx); st.rerun()

# ---------------------------------------------------------
# SEITE 7: FUHRPARK-MANAGER
# ---------------------------------------------------------
elif menu == "🛒 Fuhrpark-Manager":
    st.title(f"🚛 Fuhrpark-Manager - {akt_hof_name}")
    col_f1, col_f2 = st.columns([1, 1.5])
    with col_f1:
        if preis_dict:
            m_waehlen = st.selectbox("Maschine aktivieren:", options=list(preis_dict.keys()))
            m_h = st.number_input("Betriebsstunden (h):", min_value=0.0, step=0.1)
            if st.button("💾 Hinzufügen", use_container_width=True, type="primary"):
                hof_daten["fuhrpark_store"][m_waehlen] = m_h
                st.rerun()
        else: st.info("Keine Maschinen im Google-Sheet gefunden. Bitte Spaltenüberschriften prüfen.")
        
    with col_f2:
        for f_name, f_stunden in list(hof_daten["fuhrpark_store"].items()):
            with st.container(border=True):
                c_fn, c_fh, c_fdel = st.columns([2.5, 1.5, 0.5])
                c_fn.write(f"**{f_name}**")
                neue_stunden = c_fh.number_input("h", min_value=0.0, value=float(f_stunden), key=f"f_h_{f_name}")
                if neue_stunden != f_stunden: hof_daten["fuhrpark_store"][f_name] = neue_stunden; st.rerun()
                if c_fdel.button("🗑️", key=f"del_m_{f_name}"): del hof_daten["fuhrpark_store"][f_name]; st.rerun()

# ---------------------------------------------------------
# SEITE 8: KASSENBUCH
# ---------------------------------------------------------
elif menu == "📖 Detailliertes Kassenbuch":
    st.title(f"📖 Kassenbuch & Finanzzentrale - {akt_hof_name}")
    with st.expander("➕ Manuelle Buchung durchführen"):
        c_kb1, c_kb2, c_kb3 = st.columns([1, 2, 1.2])
        b_typ = c_kb1.selectbox("Buchungs-Typ:", ["Ausgabe", "Einnahme"])
        b_text = c_kb2.text_input("Verwendungszweck:")
        b_betrag = c_kb3.number_input("Betrag in €:", min_value=0.01, value=100.0, format="%.2f")
        
        if st.button("💾 Transaktion verbindlich buchen", type="primary", use_container_width=True):
            if b_text.strip():
                full_ingame_date = f"J{st.session_state._global_ingame_jahr}-{st.session_state._global_ingame_monat}"
                if b_typ == "Einnahme":
                    hof_daten["finanzen"]["einnahmen"] += b_betrag
                    prefix = "#MAN-EIN"
                else:
                    hof_daten["finanzen"]["ausgaben"] += b_betrag
                    prefix = "#MAN-AUS"
                
                hof_daten["finanzen"]["historie"].append({
                    "In-Game Datum": full_ingame_date, "Sort_Jahr": int(st.session_state._global_ingame_jahr), "Sort_Monat": st.session_state._global_ingame_monat,
                    "Typ": b_typ, "Nummer": f"{prefix}-{os.urandom(2).hex().upper()}", "Details": b_text.strip(), "Betrag (EUR)": b_betrag
                })
                st.success("Gebucht!"); st.rerun()

    st.write("---")
    st.subheader("📊 Transaktionsverlauf")
    historie_liste = hof_daten["finanzen"].get("historie", [])
    if historie_liste:
        df_anzeige = pd.DataFrame(historie_liste).iloc[::-1]
        st.dataframe(df_anzeige[["In-Game Datum", "Nummer", "Typ", "Details", "Betrag (EUR)"]], use_container_width=True, hide_index=True)
    else: st.info(f"Noch keine Einträge im Kassenbuch von {akt_hof_name} vorhanden.")
