import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- GLOBALER SERVER-SPEICHER (FÜR ALLE SPIELER SYNCHRONISIERT) ---
if not hasattr(st, "_global_hof_store"):
    st._global_hof_store = []

if not hasattr(st, "_global_lager_store"):
    st._global_lager_store = {"saat": 3000, "kalk": 10000, "dueng": 2000, "herbi": 2000}

if not hasattr(st, "_global_bestell_store"):
    st._global_bestell_store = []

# Globaler Finanzen- & Nummern-Speicher
if not hasattr(st, "_global_finanzen"):
    st._global_finanzen = {
        "start_saldo": 0.0,  # Neues Feld für das manuelle Start-Saldo
        "einnahmen": 0.0,
        "ausgaben": 0.0,
        "naechste_rechnung_id": 1,
        "naechste_bestellung_id": 1,
        "historie": [] # Liste aller Buchungen für die Übersicht
    }

# --- STATISCHE LISTE FÜR IN-GAME MONATE ---
LISTE_MONATE = [
    "01 - Januar", "02 - Februar", "03 - März", "04 - April", 
    "05 - Mai", "06 - Juni", "07 - Juli", "08 - August", 
    "09 - September", "10 - Oktober", "11 - November", "12 - Dezember"
]

# --- HILFSFUNKTIONEN FÜR FORMATIERUNG UND UMLAUTE ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items():
        txt = txt.replace(r, v)
    return txt

def fmt_int(wert):
    return f"{wert:,.0f}".replace(",", ".")

def fmt_float(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- PDF KLASSEN ---
class InvoicePDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 15, 15, 40)
        else:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "LU-BETRIEB", ln=True)
        self.ln(20)

def generate_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum):
    pdf = InvoicePDF()
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
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 10, "Leistung / Maschine", border=0)
    pdf.cell(30, 10, "Menge", border=0, align="C")
    pdf.cell(40, 10, "Einzelpreis", border=0, align="R")
    pdf.cell(40, 10, "Gesamt", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    summe = 0
    for p in posten:
        pdf.cell(80, 10, safe_str(p['name']), border=0)
        einheit = p.get('einheit', 'h')
        pdf.cell(30, 10, f"{p['menge']} {einheit}", border=0, align="C")
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
    if rabatt_prozent > 0:
        pdf.cell(150, 6, f"Rabatt ({rabatt_prozent}%):", align="R")
        pdf.cell(40, 6, f"-{fmt_float(rabatt_betrag)} EUR", align="R", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Vielen Dank fuer die gute Zusammenarbeit! Der Betrag ist sofort faellig.", align="C")
    return pdf.output()

def generate_order_pdf(bestell_liste, bestell_id, ingame_datum):
    pdf = InvoicePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.cell(65, 6, f"In-Game Datum: {ingame_datum}\nAuftrags-Nr: #BS-{bestell_id:04d}", align="R", ln=True)
    
    pdf.ln(35)
    pdf.set_x(50)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "BESTELLUNG / ARBEITSAUFTRAG", ln=True)
    
    pdf.ln(15)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 10, "Artikel oder Dienstleistung", border=0)
    pdf.cell(60, 10, "Menge / Einheit", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    for b in bestell_liste:
        pdf.cell(120, 10, safe_str(b["artikel"]), border=0)
        einheit = b.get("einheit", "L")
        if einheit in ["ha", "h"]:
            pdf.cell(60, 10, f"{fmt_float(b['menge'])} {einheit}", border=0, align="R")
        else:
            pdf.cell(60, 10, f"{fmt_int(b['menge'])} {einheit}", border=0, align="R")
        pdf.ln(10)
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Generiert ueber LS25 Hof-Manager. Bitte an Partnerhof/Lohnunternehmer uebermitteln.", align="C")
    return pdf.output()


# 2. Daten-Verbindung zu Google Sheets
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

PROD_DATA = {
    "Getreidemühle: Weizen zu Mehl": (36000, 27000, "Weizen", "Mehl"),
    "Getreidemühle: Gerste zu Mehl": (36000, 27000, "Gerste", "Mehl"),
    "Bäckerei: Brot": (21600, 10800, "Mehl", "Brot"),
    "Bäckerei: Kuchen": (4320, 4320, "Mehl/Zucker/Milch/Eier/Erdbeeren (Mix)", "Kuchen"),
    "Ölmühle: Sonnenblumenöl": (14400, 7200, "Sonnenblumen", "Sonnenblumenöl"),
    "Ölmühle: Rapsöl": (14400, 7200, "Raps", "Rapsöl"),
    "Molkerei: Butter": (36000, 21600, "Milch", "Butter"),
    "Molkerei: Käse": (21600, 16200, "Milch", "Käse"),
    "Zuckerfabrik: Zuckerrohr": (28800, 28800, "Zuckerrohr", "Zucker"),
    "Zuckerfabrik: Zuckerrüben": (14400, 7200, "Zuckerrüben", "Zucker"),
    "➕ Eigenes / Mod-Rezept hinzufügen": (0, 0, "", "")
}

# --- SIDEBAR FINANZ-METRIKEN ---
st.sidebar.markdown("## 💰 Hof-Kasse (Live)")

# NEU: Start-Saldo konfigurieren
st.sidebar.markdown("### 🏁 Startkapital einrichten")
st._global_finanzen["start_saldo"] = st.sidebar.number_input(
    "Start-Saldo (EUR):", 
    min_value=0.0, 
    value=float(st._global_finanzen.get("start_saldo", 0.0)), 
    step=10000.0,
    key="config_start_saldo"
)

einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
# Aktueller Hof-Gewinn berechnet sich nun inklusive Start-Saldo
aktuelle_hof_kasse = st._global_finanzen["start_saldo"] + einn - ausg

st.sidebar.metric("Einnahmen (Saison)", f"+{fmt_float(einn)} EUR")
st.sidebar.metric("Ausgaben (Saison)", f"-{fmt_float(ausg)} EUR")
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} EUR")

# Manuelle Buchungsfunktion in der Seitenleiste
with st.sidebar.expander("➕ Manuelle Buchung eintragen"):
    m_typ = st.radio("Buchungsart:", ["Einnahme", "Ausgabe"], key="m_typ")
    m_betrag = st.number_input("Betrag (EUR):", min_value=0.0, value=1000.0, step=100.0, key="m_betrag")
    m_details = st.text_input("Zweck (z.B. Getreideverkauf):", value="", key="m_details")
    
    st.markdown("**In-Game Zeit:**")
    col_m_m, col_m_j = st.columns(2)
    m_monat = col_m_m.selectbox("Monat:", LISTE_MONATE, key="m_monat")
    m_jahr = col_m_j.number_input("Jahr:", min_value=1, value=1, step=1, key="m_jahr")
    
    if st.button("💾 Buchung speichern", key="sidebar_save_btn"):
        if m_details.strip() == "":
            st.error("Bitte einen Verwendungszweck eingeben!")
        else:
            in_game_datum_str = f"Jahr {m_jahr} - {m_monat}"
            if m_typ == "Einnahme":
                st._global_finanzen["einnahmen"] += m_betrag
                st._global_finanzen["historie"].append({
                    "In-Game Datum": in_game_datum_str, "Sort_Jahr": m_jahr, "Sort_Monat": m_monat,
                    "Typ": "Manuelle Einnahme", "Nummer": "M-IN", "Details": m_details, "Betrag (EUR)": m_betrag
                })
            else:
                st._global_finanzen["ausgaben"] += m_betrag
                st._global_finanzen["historie"].append({
                    "In-Game Datum": in_game_datum_str, "Sort_Jahr": m_jahr, "Sort_Monat": m_monat,
                    "Typ": "Manuelle Ausgabe", "Nummer": "M-OUT", "Details": m_details, "Betrag (EUR)": m_betrag
                })
            st.success("Erfolgreich gebucht!")
            st.rerun()

if st.sidebar.button("🗑️ Kassenbuch zurücksetzen"):
    st._global_finanzen = {"start_saldo": 0.0, "einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}
    st.rerun()

st.sidebar.write("---")
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "🛒 Material- & Auftragsverwaltung", "🏭 Produktions-Planer"])

# --- SEITE 1 ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    with st.expander("⚙️ Verbrauchs-Raten anpassen (pro Hektar)"):
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        r_kalk = col_r1.number_input("Kalk (L/ha):", value=2000)
        r_duenger = col_r2.number_input("Dünger (L/ha):", value=160)
        r_saat = col_r3.number_input("Saatgut (L/ha):", value=150)
        r_herbi = col_r4.number_input("Herbizid (L/ha):", value=100)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧪 Bedarfskalkulation")
        ha = st.number_input("Hektar (ha):", min_value=0.1, value=1.0, step=0.1)
        st.info(f"""
        **Benötigte Mengen für {ha} ha:**
        * Kalk: **{fmt_int(ha * r_kalk)} L**
        * Dünger: **{fmt_int(ha * r_duenger)} L**
        * Saatgut: **{fmt_int(ha * r_saat)} L**
        * Herbizid: **{fmt_int(ha * r_herbi)} L**
        """)
    with col2:
        st.subheader("Erloesrechner")
        menge = st.number_input("Liter im Silo:", value=10000)
        preis_pro_1000 = st.number_input("EUR pro 1000L:", value=1200)
        erloes = (menge / 1000) * preis_pro_1000
        st.success(f"**Voraussichtlicher Erloes:**\n### {fmt_float(erloes)} EUR")

# --- SEITE 2: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📋 Rechnungs-Ersteller")
    
    aktuelle_id = st._global_finanzen["naechste_rechnung_id"]
    st.caption(f"Nächste Rechnungsnummer: **#RE-{aktuelle_id:04d}**")

    with st.container(border=True):
        abrechnungs_art = st.radio("Abrechnungsmethode:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Freitext / Sonderposten"], horizontal=True)
        c1, c2, c3 = st.columns([2, 1, 1])
        
        if abrechnungs_art == "Freitext / Sonderposten":
            auswahl = c1.text_input("Bezeichnung / Leistung:", value="", placeholder="z.B. Forstarbeiten, Ballentransport")
            menge = c2.number_input("Menge:", min_value=0.1, value=1.0, step=0.1)
            e_p = c3.number_input("Preis (EUR / Einheit):", value=0.0, step=10.0)
            einheit_str = "Stk"
        elif abrechnungs_art == "Nach Feldfläche (ha)":
            auswahl = c1.text_input("Arbeitsleistung (Fläche):", value="Maehen", placeholder="z.B. Mähen, Grubbern, Dreschen")
            menge = c2.number_input("Fläche (ha):", min_value=0.1, value=1.0, step=0.1)
            e_p = c3.number_input("Preis (EUR / ha):", value=50.0, step=5.0)
            einheit_str = "ha"
        else: 
            auswahl = c1.selectbox("Maschine / Dienstleistung:", options=list(preis_dict.keys()) if preis_dict else ["Traktorenarbeit"])
            menge = c2.number_input("Arbeitszeit (h):", min_value=0.1, value=1.0, step=0.1)
            e_p = c3.number_input("Preis (EUR / h):", value=float(preis_dict.get(auswahl, 0.0)))
            einheit_str = "h"
            
        if st.button("➕ Zum Beleg hinzufügen"):
            if auswahl.strip() == "":
                st.error("Die Bezeichnung darf nicht leer sein!")
            else:
                st.session_state.rechnungs_posten.append({
                    "name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p
                })
                st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden) if aktuelle_kunden else ck1.text_input("Hofname:")
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)
    
    st.markdown("#### 📆 Wann findet die Leistung statt? (In-Game Zeit)")
    col_re_m, col_re_j = st.columns(2)
    re_monat = col_re_m.selectbox("In-Game Monat für Rechnung:", LISTE_MONATE)
    re_jahr = col_re_j.number_input("In-Game Jahr für Rechnung:", min_value=1, value=1, step=1)

    if st.session_state.rechnungs_posten:
        st.write("---")
        st.subheader("📋 Aktuelle Posten")
        
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        df_preview["Menge / Einheit"] = df_preview.apply(lambda r: f"{r['menge']} {r['einheit']}", axis=1)
        df_display = df_preview[["name", "Menge / Einheit", "preis", "gesamt"]].copy()
        df_display.columns = ["Leistung / Maschine", "Menge & Einheit", "Einzelpreis (EUR)", "Gesamt (EUR)"]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Zwischensumme", f"{fmt_float(summe)} EUR")
        col_m2.metric("Endbetrag", f"{fmt_float(total)} EUR")

        st.write("")
        
        # --- DYNAMISCHER DATEINAME FÜR RECHNUNGEN ---
        vorgeschlagener_name = f"Rechnung_RE-{aktuelle_id:04d}_{safe_str(k_name)}"
        pdf_dateiname = st.text_input("📄 PDF-Dateiname (ohne .pdf):", value=vorgeschlagener_name)
        # ---------------------------------------------
        
        col_b1, col_b2, col_b3 = st.columns(3)
        
        full_ingame_date = f"Jahr {re_jahr} - {re_monat}"
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt, aktuelle_id, full_ingame_date)
        
        col_b1.download_button(
            label="📥 PDF herunterladen",
            data=bytes(pdf_data),
            file_name=f"{pdf_dateiname}.pdf",
            mime="application/pdf"
        )
        
        if col_b2.button("💾 Rechnung auf Server verbuchen", type="primary"):
            st._global_finanzen["einnahmen"] += total
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": re_jahr, "Sort_Monat": re_monat,
                "Typ": "Einnahme (Rechnung)", "Nummer": f"#RE-{aktuelle_id:04d}",
                "Details": f"Kunde: {k_name} ({len(st.session_state.rechnungs_posten)} Positionen)", "Betrag (EUR)": total
            })
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.success("Erfolgreich verbucht!")
            st.rerun()
            
        if col_b3.button("🗑️ Posten löschen"):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3: AUFTRÄGE & BESTELLUNGEN ---
elif menu == "🛒 Material- & Auftragsverwaltung":
    st.title("🛒 Materialbestellungen & Fremdaufträge")
    
    st.subheader("📦 Aktueller Hof-Bestand (Server)")
    col_s, col_k, col_d, col_h = st.columns(4)
    
    with col_s:
        st.markdown("### 🌱 Saatgut")
        v_saat = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["saat"]), step=500, key="nb_saat")
        g_saat = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_saat")
        b_saat = v_saat - g_saat
        st._global_lager_store["saat"] = b_saat
        if b_saat < 1500: st.error(f"🚨 Kritisch: {fmt_int(b_saat)} L")
        else: st.success(f"✅ Stabil: {fmt_int(b_saat)} L")
            
    with col_k:
        st.markdown("### ⚪ Kalk")
        v_kalk = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["kalk"]), step=1000, key="nb_kalk")
        g_kalk = st.number_input("Verbraucht (L):", min_value=0, value=0, step=500, key="g_kalk")
        b_kalk = v_kalk - g_kalk
        st._global_lager_store["kalk"] = b_kalk
        if b_kalk < 5000: st.error(f"🚨 Kritisch: {fmt_int(b_kalk)} L")
        else: st.success(f"✅ Stabil: {fmt_int(b_kalk)} L")
            
    with col_d:
        st.markdown("### 🧪 Flüssigdünger")
        v_dueng = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["dueng"]), step=500, key="nb_dueng")
        g_dueng = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_dueng")
        b_dueng = v_dueng - g_dueng
        st._global_lager_store["dueng"] = b_dueng
        if b_dueng < 1000: st.error(f"🚨 Kritisch: {fmt_int(b_dueng)} L")
        else: st.success(f"✅ Stabil: {fmt_int(b_dueng)} L")

    with col_h:
        st.markdown("### 🌿 Herbizid")
        v_herbi = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store.get("herbi", 2000)), step=500, key="nb_herbi")
        g_herbi = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_herbi")
        b_herbi = v_herbi - g_herbi
        st._global_lager_store["herbi"] = b_herbi
        if b_herbi < 1000: st.error(f"🚨 Kritisch: {fmt_int(b_herbi)} L")
        else: st.success(f"✅ Stabil: {fmt_int(b_herbi)} L")
            
    st.write("---")
    st.subheader("📝 Einkäufe & Lohnarbeiten auf Server-Liste setzen")
    
    art_der_bestellung = st.radio("Was möchtest du in Auftrag geben / einkaufen?", ["🌾 Eigenes Lager auffüllen (Material)", "🚜 Externe Dienstleistung beauftragen (Mähen, Dreschen etc.)"], horizontal=True)

    if art_der_bestellung == "🚜 Externe Dienstleistung beauftragen (Mähen, Dreschen etc.)":
        with st.container(border=True):
            st.markdown("**Arbeitsauftrag für Lohnunternehmer / Nachbarhof**")
            col_o1, col_o2, col_o3 = st.columns([2, 1, 1])
            
            lu_arbeit = col_o1.text_input("Welche Arbeit gibst du in Auftrag?", placeholder="z.B. Maehen Feld 12, Haeckseln", key="lu_arbeit")
            lu_einheit = col_o2.selectbox("Einheit:", ["ha", "h"], key="lu_einheit")
            lu_menge = col_o3.number_input(f"Menge ({lu_einheit}):", min_value=0.1, value=1.0, step=0.5, key="lu_menge")
            
            if st.button("📝 Dienstleistung auf die Liste setzen", type="secondary"):
                if lu_arbeit.strip() == "":
                    st.error("Bitte trage ein, welche Arbeit erledigt werden soll!")
                else:
                    st._global_bestell_store.append({
                        "artikel": f"Auftrag LU: {lu_arbeit}",
                        "menge": lu_menge,
                        "einheit": lu_einheit
                    })
                    st.success(f"✅ '{lu_arbeit}' wurde der Liste hinzugefügt!")
                    st.rerun()
    else:
        with st.expander("📉 Automatische Nachfüllung (Lager-Vorschlag)"):
            col_p1, col_p2, col_p3, col_p4 = st.columns(4)
            p_saat = col_p1.number_input("Saatgut (EUR/1000L):", value=900)
            p_kalk = col_p2.number_input("Kalk (EUR/1000L):", value=150)
            p_dueng = col_p3.number_input("Dünger (EUR/1000L):", value=1200)
            p_herbi = col_p4.number_input("Herbizid (EUR/1000L):", value=1000)

            col_b1, col_b2 = st.columns(2)
            init_saat = 2000 if b_saat < 1500 else 0
            order_saat = col_b1.number_input("Saatgut Menge (Liter):", min_value=0, value=init_saat, step=500)
            b_typ = col_b2.text_input("Fruchtsorte (z.B. Weizen, Raps):", value="")
            
            col_b3, col_b4, col_b5 = st.columns(3)
            init_kalk = 5000 if b_kalk < 5000 else 0
            order_kalk = col_b3.number_input("Kalk Menge (Liter):", min_value=0, value=init_kalk, step=1000)
            init_dueng = 1000 if b_dueng < 1000 else 0
            order_dueng = col_b4.number_input("Flüssigdünger Menge (Liter):", min_value=0, value=init_dueng, step=500)
            init_herbi = 1000 if b_herbi < 1000 else 0
            order_herbi = col_b5.number_input("Herbizid Menge (Liter):", min_value=0, value=init_herbi, step=500)
            
            if st.button("📝 Standard-Lagergüter hinzufügen"):
                if order_saat > 0:
                    art = f"Saatgut ({b_typ})" if b_typ else "Saatgut"
                    st._global_bestell_store.append({"artikel": art, "menge": order_saat, "einheit": "L"})
                if order_kalk > 0:
                    st._global_bestell_store.append({"artikel": "Kalk", "menge": order_kalk, "einheit": "L"})
                if order_dueng > 0:
                    st._global_bestell_store.append({"artikel": "Fluessigduenger", "menge": order_dueng, "einheit": "L"})
                if order_herbi > 0:
                    st._global_bestell_store.append({"artikel": "Herbizid", "menge": order_herbi, "einheit": "L"})
                st.success(f"Standardgüter hinzugefügt!")
                st.rerun()

        with st.expander("➕ Freitext / Andere Waren hinzufügen (Diesel, Futter, etc.)"):
            col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
            m_artikel_name = col_m1.text_input("Artikelname:", placeholder="z.B. Diesel, Mischration", key="order_m_name")
            m_artikel_menge = col_m2.number_input("Menge:", min_value=1, value=1000, step=50, key="order_m_menge")
            m_artikel_einheit = col_m3.selectbox("Einheit:", ["L", "Stk", "kg"], key="order_m_einheit")
            
            if st.button("📝 Sonderposten zur Einkaufsliste packen"):
                if m_artikel_name.strip() == "":
                    st.error("Bitte gib einen Namen für das Produkt ein!")
                else:
                    st._global_bestell_store.append({"artikel": m_artikel_name, "menge": m_artikel_menge, "einheit": m_artikel_einheit})
                    st.success(f"✅ '{m_artikel_name}' wurde hinzugefügt!")
                    st.rerun()

    if st._global_bestell_store:
        st.write("---")
        bestell_id = st._global_finanzen["naechste_bestellung_id"]
        st.subheader(f"📋 Offene Posten & Aufträge auf dem Server (#BS-{bestell_id:04d})")
        
        df_bestellungen = pd.DataFrame(st._global_bestell_store)
        df_bestellungen["Menge & Einheit"] = df_bestellungen.apply(lambda r: f"{r['menge']} {r['einheit']}", axis=1)
        df_anzeige_b = df_bestellungen[["artikel", "Menge & Einheit"]].copy()
        df_anzeige_b.columns = ["Artikel / Dienstleistung", "Menge & Einheit"]
        
        st.dataframe(df_anzeige_b, use_container_width=True, hide_index=True)
        
        # --- MANUELLE EINZEL-LÖSCHFUNKTION ---
        with st.container(border=True):
            st.markdown("🗑️ **Einzelnen Posten von der Liste löschen**")
            loesch_optionen = [f"{i+1}: {p['artikel']} ({p['menge']} {p['einheit']})" for i, p in enumerate(st._global_bestell_store)]
            posten_zu_loeschen = st.selectbox("Wähle den Posten aus, den du entfernen willst:", options=loesch_optionen)
            
            if st.button("❌ Ausgewählten Posten löschen", type="secondary"):
                idx_zu_loeschen = int(posten_zu_loeschen.split(":")[0]) - 1
                entfernter_posten = st._global_bestell_store.pop(idx_zu_loeschen)
                st.success(f" Posten '{entfernter_posten['artikel']}' wurde gelöscht!")
                st.rerun()
        # ------------------------------------------

        st.markdown("#### 📆 In-Game Buchungsmonat für diesen Beleg")
        col_bs_m, col_bs_j = st.columns(2)
        bs_monat = col_bs_m.selectbox("In-Game Monat für Beleg:", LISTE_MONATE)
        bs_jahr = col_bs_j.number_input("In-Game Jahr für Beleg:", min_value=1, value=1, step=1)
        
        # --- DYNAMISCHER DATEINAME FÜR AUFTRÄGE ---
        vorgeschlagener_auftrag_name = f"Hof_Auftrag_BS-{bestell_id:04d}"
        auftrag_dateiname = st.text_input("📄 PDF-Dateiname (ohne .pdf):", value=vorgeschlagener_auftrag_name, key="pdf_order_name")
        # -------------------------------------------
        
        tatsaechliche_kosten = st.number_input("Tatsächliche Gesamtkosten (EUR):", min_value=0.0, value=0.0, step=50.0)
        col_btn1, col_btn2 = st.columns(2)
        
        full_bs_date = f"Jahr {bs_jahr} - {bs_monat}"
        order_pdf_data = generate_order_pdf(st._global_bestell_store, bestell_id, full_bs_date)
        
        col_btn1.download_button(
            label="📥 Bestell-/Auftragszettel als PDF", 
            data=bytes(order_pdf_data), 
            file_name=f"{auftrag_dateiname}.pdf", 
            mime="application/pdf"
        )
        
        if col_btn2.button("✅ Posten erledigt & Geld abziehen", type="primary"):
            st._global_finanzen["ausgaben"] += tatsaechliche_kosten
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_bs_date, "Sort_Jahr": bs_jahr, "Sort_Monat": bs_monat,
                "Typ": "Ausgabe (Auftrag/Einkauf)", "Nummer": f"#BS-{bestell_id:04d}",
                "Details": f"{len(st._global_bestell_store)} Positionen abgerechnet", "Betrag (EUR)": tatsaechliche_kosten
            })
            st._global_finanzen["naechste_bestellung_id"] += 1
            st._global_bestell_store = []
            st.success("Erfolgreich im Kassenbuch als Ausgabe verbucht!")
            st.rerun()

# --- SEITE 4: PRODUKTIONS-PLANER ---
elif menu == "🏭 Produktions-Planer":
    st.title("🏭 LS-Produktionsketten Rechner")
    st.write("Diese Liste wird **live mit allen Spielern auf dem Hof synchronisiert**!")
    
    with st.container(border=True):
        st.subheader("🏭 Neue Produktion hinzufügen")
        rezept = st.selectbox("Wähle eine Produktion/Rezept aus:", options=list(PROD_DATA.keys()))
        
        if rezept == "➕ Eigenes / Mod-Rezept hinzufügen":
            st.write("---")
            col_custom1, col_custom2 = st.columns(2)
            in_name = col_custom1.text_input("Name des Rohstoffs (Input):", value="Dinkel")
            out_name = col_custom2.text_input("Name des Produkts (Output):", value="Altes Mehl")
            col_custom3, col_custom4, col_custom5 = st.columns(3)
            custom_in_menge = col_custom3.number_input(f"Menge pro Zyklus:", min_value=1, value=5)
            custom_out_menge = col_custom4.number_input(f"Menge pro Zyklus:", min_value=1, value=4)
            zyklen_pro_std = col_custom5.number_input("Zyklen pro Stunde:", min_value=1, value=30)
            base_in = custom_in_menge * zyklen_pro_std * 24 * 30
            base_out = custom_out_menge * zyklen_pro_std * 24 * 30
            name_anzeige = f"Mod-Rezept: {in_name} -> {out_name}"
        else:
            base_in, base_out, in_name, out_name = PROD_DATA[rezept]
            name_anzeige = rezept
            
        col_time1, col_time2 = st.columns(2)
        monate = col_time1.slider("Betriebsdauer im Jahr (Monate):", min_value=1, max_value=12, value=12, key="prod_monate")
        anzahl_fabriken = col_time2.number_input("Anzahl Linien / Fabriken:", min_value=1, value=1, step=1, key="prod_anzahl")
        
        if st.button("💾 Für ALLE speichern & synchronisieren", type="primary"):
            gesamt_input = base_in * monate * anzahl_fabriken
            gesamt_output = base_out * monate * anzahl_fabriken
            st._global_hof_store.append({
                "name": name_anzeige, "monate": monate, "linien": anzahl_fabriken,
                "in_typ": in_name, "in_menge": gesamt_input, "out_typ": out_name, "out_menge": gesamt_output
            })
            st.success(f"✅ Gespeichert!")
            st.rerun()

    if st._global_hof_store:
        st.write("---")
        st.header("🏡 Aktive Produktionen auf dem Server")
        table_data = []
        for idx, item in enumerate(st._global_hof_store):
            table_data.append({
                "ID": idx + 1, "Produktion / Fabrik": item["name"], "Linien": item["linien"], "Laufzeit": f"{item['monate']} Monate",
                "Rohstoff Bedarf (Jahr)": f"{fmt_int(item['in_menge'])} L ({item['in_typ']})", "Produkt Ertrag (Jahr)": f"{fmt_int(item['out_menge'])} L ({item['out_typ']})"
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        col_action1, col_action2 = st.columns(2)
        if col_action2.button("🗑️ Alle Produktionen vom Server löschen"):
            st._global_hof_store = []
            st.rerun()


# --- ANZEIGE DER HISTORIE & JAHRESABSCHLUSS BILANZ ---
if st._global_finanzen["historie"]:
    st.write("---")
    st.header("📊 In-Game Jahresabschluss-Bilanz & Berichte")
    
    df_raw = pd.DataFrame(st._global_finanzen["historie"])
    
    df_raw["Einnahme_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if "Einnahme" in r["Typ"] else 0.0, axis=1)
    df_raw["Ausgabe_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if "Ausgabe" in r["Typ"] else 0.0, axis=1)
    
    # Chronologisch sortieren, um das Saldo sauber aufzubauen
    df_raw_sorted = df_raw.sort_values(by=["Sort_Jahr", "Sort_Monat"]).reset_index(drop=True)
    
    # --- ANGEPASST: Fortlaufendes Saldo inkl. Start-Saldo berechnen ---
    kontostand = st._global_finanzen["start_saldo"]
    saldo_liste = []
    for idx, row in df_raw_sorted.iterrows():
        if "Einnahme" in row["Typ"]:
            kontostand += row["Betrag (EUR)"]
        else:
            kontostand -= row["Betrag (EUR)"]
        saldo_liste.append(kontostand)
    
    df_raw_sorted["Saldo (EUR)"] = saldo_liste
    # ------------------------------------------
    
    df_monat = df_raw_sorted.groupby(["In-Game Datum", "Sort_Jahr", "Sort_Monat"]).agg(
        Einnahmen=("Einnahme_Wert", "sum"),
        Ausgaben=("Ausgabe_Wert", "sum")
    ).reset_index()
    
    df_monat = df_monat.sort_values(by=["Sort_Jahr", "Sort_Monat"])
    df_monat["Gewinn / Verlust"] = df_monat["Einnahmen"] - df_monat["Ausgaben"]
    
    col_bil1, col_bil2 = st.columns([5, 4])
    
    with col_bil1:
        st.subheader("🗓️ Finanzergebnis nach In-Game Monaten")
        df_anzeige = df_monat.copy()
        df_anzeige["Einnahmen"] = df_anzeige["Einnahmen"].map(lambda x: f"+{fmt_float(x)} EUR")
        df_anzeige["Ausgaben"] = df_anzeige["Ausgaben"].map(lambda x: f"-{fmt_float(x)} EUR")
        df_anzeige["Gewinn / Verlust"] = df_anzeige["Gewinn / Verlust"].map(lambda x: f"{fmt_float(x)} EUR")
        st.dataframe(df_anzeige[["In-Game Datum", "Einnahmen", "Ausgaben", "Gewinn / Verlust"]], use_container_width=True, hide_index=True)
        
    with col_bil2:
        st.subheader("📈 Reingewinn-Trend")
        st.bar_chart(data=df_monat, x="In-Game Datum", y="Gewinn / Verlust", color="#2e7d32")

    with st.expander("📋 Komplettes Kassenbuch (Einzeltransaktionen mit Live-Saldo anzeigen)"):
        # Spalten für eine schönere UI-Anzeige formatieren
        df_kassenbuch_view = df_raw_sorted.copy()
        df_kassenbuch_view["Betrag (EUR)"] = df_kassenbuch_view.apply(
            lambda r: f"+{fmt_float(r['Betrag (EUR)'])}" if "Einnahme" in r["Typ"] else f"-{fmt_float(r['Betrag (EUR)'])}", axis=1
        )
        df_kassenbuch_view["Saldo"] = df_kassenbuch_view["Saldo (EUR)"].map(lambda x: f"{fmt_float(x)} EUR")
        
        # Hinweis-Zeile für das Startkapital über der Tabelle anzeigen
        st.info(f"🏁 Eingestelltes Startkapital: **{fmt_float(st._global_finanzen['start_saldo'])} EUR**")
        
        # DataFrame mit der neuen Saldo-Spalte ausgeben
        st.dataframe(
            df_kassenbuch_view[["In-Game Datum", "Typ", "Nummer", "Details", "Betrag (EUR)", "Saldo"]], 
            use_container_width=True, 
            hide_index=True
        )
