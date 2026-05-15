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
        "einnahmen": 0.0,
        "ausgaben": 0.0,
        "naechste_rechnung_id": 1,
        "naechste_bestellung_id": 1,
        "historie": [] # Liste aller Buchungen für die Übersicht
    }


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

def generate_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id):
    pdf = InvoicePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.multi_cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}\nRechnung-Nr: #RE-{rechnungs_id:04d}", align="R")
    
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
        pdf.cell(30, 10, f"{p['std']} h", border=0, align="C")
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

def generate_order_pdf(bestell_liste, bestell_id):
    pdf = InvoicePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}\nBestell-Nr: #BS-{bestell_id:04d}", align="R", ln=True)
    
    pdf.ln(35)
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "WARENBESTELLUNG", ln=True)
    
    pdf.ln(15)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 10, "Artikel / Ware", border=0)
    pdf.cell(60, 10, "Bestellmenge", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    for b in bestell_liste:
        pdf.cell(120, 10, safe_str(b["artikel"]), border=0)
        # Wenn eine Einheit mitgegeben wurde, nutzen wir diese, sonst Standard 'L'
        einheit = b.get("einheit", "L")
        pdf.cell(60, 10, f"{fmt_int(b['menge'])} {einheit}", border=0, align="R")
        pdf.ln(10)
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Generiert ueber LS25 Hof-Manager. Bitte an den Landhandel uebermitteln.", align="C")
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
einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
gewinn = einn - ausg
st.sidebar.metric("Einnahmen", f"+{fmt_float(einn)} EUR")
st.sidebar.metric("Ausgaben", f"-{fmt_float(ausg)} EUR")
st.sidebar.metric("Gewinn/Verlust", f"{fmt_float(gewinn)} EUR", delta=gewinn)

# Manuelle Buchungsfunktion in der Seitenleiste
with st.sidebar.expander("➕ Manuelle Buchung eintragen"):
    m_typ = st.radio("Buchungsart:", ["Einnahme", "Ausgabe"], key="m_typ")
    m_betrag = st.number_input("Betrag (EUR):", min_value=0.0, value=1000.0, step=100.0, key="m_betrag")
    m_details = st.text_input("Zweck (z.B. Getreideverkauf):", value="", key="m_details")
    
    if st.button("💾 Buchung speichern"):
        if m_details.strip() == "":
            st.error("Bitte einen Verwendungszweck eingeben!")
        else:
            if m_typ == "Einnahme":
                st._global_finanzen["einnahmen"] += m_betrag
                st._global_finanzen["historie"].append({
                    "Typ": "Manuelle Einnahme",
                    "Nummer": "M-IN",
                    "Details": m_details,
                    "Betrag (EUR)": m_betrag
                })
            else:
                st._global_finanzen["ausgaben"] += m_betrag
                st._global_finanzen["historie"].append({
                    "Typ": "Manuelle Ausgabe",
                    "Nummer": "M-OUT",
                    "Details": m_details,
                    "Betrag (EUR)": m_betrag
                })
            st.success("Erfolgreich gebucht!")
            st.rerun()

if st.sidebar.button("🗑️ Kassenbuch zurücksetzen"):
    st._global_finanzen = {"einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}
    st.rerun()

st.sidebar.write("---")
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "🛒 Saatgut-Bestellung", "🏭 Produktions-Planer"])

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

# --- SEITE 2: RECHNUNGS-ERSTELLER (MIT MANUELLEM POSTEN-BUTTON) ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📋 Rechnungs-Ersteller")
    
    aktuelle_id = st._global_finanzen["naechste_rechnung_id"]
    st.caption(f"Nächste Rechnungsnummer: **#RE-{aktuelle_id:04d}**")

    with st.container(border=True):
        # NEU: Checkbox um einen komplett freien Posten zu aktivieren
        manuell_aktiv = st.checkbox("⚙️ Sonderleistung / Manueller Posten (Nicht in Liste)")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        
        if manuell_aktiv:
            auswahl = c1.text_input("Bezeichnung / Leistung:", value="", placeholder="z.B. Forstarbeiten, Ballentransport")
            std = c2.number_input("Stunden / Menge:", min_value=0.1, value=1.0, step=0.1)
            e_p = c3.number_input("Preis (EUR / Einheit):", value=0.0, step=10.0)
        else:
            auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["-"])
            std = c2.number_input("Stunden:", min_value=0.1, value=1.0, step=0.1)
            e_p = c3.number_input("Preis (EUR/h):", value=float(preis_dict.get(auswahl, 0.0)))
            
        if st.button("➕ Hinzufuegen"):
            if manuell_aktiv and auswahl.strip() == "":
                st.error("Bitte gib einen Namen für die Sonderleistung ein!")
            else:
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
                st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden) if aktuelle_kunden else ck1.text_input("Hofname:")
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)

    if st.session_state.rechnungs_posten:
        st.write("---")
        st.subheader("📋 Aktuelle Posten")
        
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        df_preview.columns = ["Maschine / Leistung", "Menge/Stunden", "Einzelpreis (EUR)", "Gesamt (EUR)"]
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Zwischensumme", f"{fmt_float(summe)} EUR")
        col_m2.metric("Endbetrag", f"{fmt_float(total)} EUR")

        st.write("")
        col_b1, col_b2, col_b3 = st.columns(3)
        
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt, aktuelle_id)
        
        col_b1.download_button(
            label="📥 PDF herunterladen",
            data=bytes(pdf_data),
            file_name=f"Rechnung_RE-{aktuelle_id:04d}_{safe_str(k_name)}.pdf",
            mime="application/pdf"
        )
        
        if col_b2.button("💾 Rechnung auf Server verbuchen", type="primary"):
            st._global_finanzen["einnahmen"] += total
            st._global_finanzen["historie"].append({
                "Typ": "Einnahme (Rechnung)",
                "Nummer": f"#RE-{aktuelle_id:04d}",
                "Details": f"Kunde: {k_name}",
                "Betrag (EUR)": total
            })
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.success("Erfolgreich verbucht und Rechnungsnummer erhöht!")
            st.rerun()
            
        if col_b3.button("🗑️ Posten löschen"):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3: BESTELLUNGEN (MIT MANUELLEM FREITEXT-ARTIKEL-BUTTON) ---
elif menu == "🛒 Saatgut-Bestellung":
    st.title("🛒 Material- & Lagerverwaltung")
    
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
    
    st.subheader("🛒 Artikel auf Server-Einkaufsliste setzen")
    
    # 1. Option: Standard-Automatisierter Einkaufsrechner für Lagergrenzen
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
            kosten = ((order_saat/1000)*p_saat) + ((order_kalk/1000)*p_kalk) + ((order_dueng/1000)*p_dueng) + ((order_herbi/1000)*p_herbi)
            if order_saat > 0:
                art = f"Saatgut ({b_typ})" if b_typ else "Saatgut"
                st._global_bestell_store.append({"artikel": art, "menge": order_saat, "einheit": "L"})
            if order_kalk > 0:
                st._global_bestell_store.append({"artikel": "Kalk", "menge": order_kalk, "einheit": "L"})
            if order_dueng > 0:
                st._global_bestell_store.append({"artikel": "Fluessigduenger", "menge": order_dueng, "einheit": "L"})
            if order_herbi > 0:
                st._global_bestell_store.append({"artikel": "Herbizid", "menge": order_herbi, "einheit": "L"})
            st.success(f"Standardgüter hinzugefügt! Geschätzte Kosten: {fmt_float(kosten)} EUR")
            st.rerun()

    # NEU 2. Option: Manueller Freitext-Button für ALLES andere
    with st.expander("➕ Freitext / Sonderbestellung hinzufügen (Diesel, Futter, etc.)"):
        col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
        m_artikel_name = col_m1.text_input("Artikelname:", placeholder="z.B. Diesel, Mischration, Spanngurte", key="order_m_name")
        m_artikel_menge = col_m2.number_input("Menge:", min_value=1, value=1000, step=50, key="order_m_menge")
        m_artikel_einheit = col_m3.selectbox("Einheit:", ["L", "Stk", "Stück", "kg"], key="order_m_einheit")
        
        if st.button("📝 Sonderposten zur Einkaufsliste packen"):
            if m_artikel_name.strip() == "":
                st.error("Bitte gib einen Namen für das Produkt ein!")
            else:
                st._global_bestell_store.append({
                    "artikel": m_artikel_name,
                    "menge": m_artikel_menge,
                    "einheit": m_artikel_einheit
                })
                st.success(f"✅ '{m_artikel_name}' wurde auf die Einkaufsliste gesetzt!")
                st.rerun()

    if st._global_bestell_store:
        st.write("---")
        bestell_id = st._global_finanzen["naechste_bestellung_id"]
        st.subheader(f"📋 Offene Bestellungen auf dem Server (#BS-{bestell_id:04d})")
        
        df_bestellungen = pd.DataFrame(st._global_bestell_store)
        # Umbenennung & Schöner Formatieren im Dataframe
        df_bestellungen.columns = ["Artikel / Ware", "Bestellmenge", "Einheit"]
        st.dataframe(df_bestellungen, use_container_width=True, hide_index=True)
        
        tatsaechliche_kosten = st.number_input("Tatsächlicher Einkaufspreis beim Händler (EUR):", min_value=0.0, value=0.0, step=50.0)
        
        col_btn1, col_btn2 = st.columns(2)
        
        order_pdf_data = generate_order_pdf(st._global_bestell_store, bestell_id)
        col_btn1.download_button(
            label="📥 Bestellzettel als PDF laden", 
            data=bytes(order_pdf_data), 
            file_name=f"Hof_Bestellung_BS-{bestell_id:04d}.pdf", 
            mime="application/pdf"
        )
        
        if col_btn2.button("✅ Einkäufe erledigt & Geld abziehen", type="primary"):
            st._global_finanzen["ausgaben"] += tatsaechliche_kosten
            st._global_finanzen["historie"].append({
                "Typ": "Ausgabe (Einkauf)",
                "Nummer": f"#BS-{bestell_id:04d}",
                "Details": f"{len(st._global_bestell_store)} Artikel gekauft",
                "Betrag (EUR)": tatsaechliche_kosten
            })
            st._global_finanzen["naechste_bestellung_id"] += 1
            st._global_bestell_store = []
            st.success("Einkauf im Kassenbuch abgerechnet!")
            st.rerun()

# --- SEITE 4: PRODUKTIONS-PLANER ---
elif menu == "🏭 Produktions-Planer":
    st.title("🏭 LS-Produktionsketten Rechner")
    st.write("Füge hier deine Fabriken hinzu. Diese Liste wird **live mit allen Spielern auf dem Hof synchronisiert**!")
    
    if st.button("🔄 Server-Liste aktualisieren"):
        st.rerun()

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
                "name": name_anzeige,
                "monate": monate,
                "linien": anzahl_fabriken,
                "in_typ": in_name,
                "in_menge": gesamt_input,
                "out_typ": out_name,
                "out_menge": gesamt_output
            })
            st.success(f"✅ {name_anzeige} wurde für alle Spieler gespeichert!")
            st.rerun()

    if st._global_hof_store:
        st.write("---")
        st.header("🏡 Aktive Produktionen auf dem Server")
        
        table_data = []
        for idx, item in enumerate(st._global_hof_store):
            table_data.append({
                "ID": idx + 1,
                "Produktion / Fabrik": item["name"],
                "Linien": item["linien"],
                "Laufzeit": f"{item['monate']} Monate",
                "Rohstoff Bedarf (Jahr)": f"{fmt_int(item['in_menge'])} L ({item['in_typ']})",
                "Produkt Ertrag (Jahr)": f"{fmt_int(item['out_menge'])} L ({item['out_typ']})"
            })
            
        df_prods = pd.DataFrame(table_data)
        st.dataframe(df_prods, use_container_width=True, hide_index=True)
        
        col_action1, col_action2 = st.columns(2)
        
        json_data = json.dumps(st._global_hof_store, indent=4)
        col_action1.download_button(
            label="📥 Server-Planung als Datei sichern",
            data=json_data,
            file_name=f"LS25_Hofplan_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        if col_action2.button("🗑️ Alle Produktionen vom Server löschen"):
            st._global_hof_store = []
            st.warning("Die globale Liste wurde für alle Spieler geleert.")
            st.rerun()


# --- ANZEIGE DER HISTORIE AM SEITENENDE (URKUNDE/TRANSAKTIONEN) ---
if st._global_finanzen["historie"]:
    st.write("---")
    with st.expander("📊 Digitales Kassenbuch / Transaktionsverlauf anzeigen"):
        df_hist = pd.DataFrame(st._global_finanzen["historie"])
        st.dataframe(df_hist, use_container_width=True, hide_index=True)
