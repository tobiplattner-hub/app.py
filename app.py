import streamlit as st
import pandas as pd
from datetime import date
import os
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- HILFSFUNKTION FÜR UMLAUTE ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items():
        txt = txt.replace(r, v)
    return txt

# --- PDF KLASSEN ---
class InvoicePDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 15, 15, 40)
        else:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "LU-BETRIEB", ln=True)
        self.ln(20)

def generate_pdf(kunden_name, posten, rabatt_prozent):
    pdf = InvoicePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    pdf.set_x(130)
    pdf.multi_cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}\nRechnung-Nr: #{date.today().strftime('%Y%m%d')}-01", align="R")
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, "Empfaenger:", ln=True)
    pdf.set_font("Helvetica", size=11)
    pdf.cell(0, 6, safe_str(kunden_name), ln=True)
    
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "RECHNUNG", ln=True)
    
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
        pdf.cell(40, 10, f"{p['preis']:.2f} EUR", border=0, align="R")
        pdf.cell(40, 10, f"{p['gesamt']:.2f} EUR", border=0, align="R")
        pdf.ln(10)
        summe += p['gesamt']
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    rabatt_betrag = summe * (rabatt_prozent / 100)
    total = summe - rabatt_betrag
    
    pdf.cell(150, 6, "Zwischensumme:", align="R")
    pdf.cell(40, 6, f"{summe:.2f} EUR", align="R", ln=True)
    
    if rabatt_prozent > 0:
        pdf.cell(150, 6, f"Rabatt ({rabatt_prozent}%):", align="R")
        pdf.cell(40, 6, f"-{rabatt_betrag:.2f} EUR", align="R", ln=True)
        
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{total:.2f} EUR", align="R", ln=True)
    
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Vielen Dank fuer die gute Zusammenarbeit! Der Betrag ist sofort faellig.", align="C")
    return pdf.output()

def generate_order_pdf(kalk_l, duenger_l, saatgut_l, saaten_typ):
    pdf = InvoicePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    pdf.set_x(130)
    pdf.cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}", align="R", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "WARENBESTELLUNG", ln=True)
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 10, "Artikel / Ware", border=0)
    pdf.cell(60, 10, "Bestellmenge (Liter)", border=0, align="R")
    pdf.ln(10)
    
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    if kalk_l > 0:
        pdf.cell(120, 10, "Kalk", border=0)
        pdf.cell(60, 10, f"{kalk_l:,} L", border=0, align="R")
        pdf.ln(10)
    if duenger_l > 0:
        pdf.cell(120, 10, "Fluessigduenger", border=0)
        pdf.cell(60, 10, f"{duenger_l:,} L", border=0, align="R")
        pdf.ln(10)
    if saatgut_l > 0:
        art_name = f"Saatgut ({saaten_typ})" if saaten_typ else "Saatgut"
        pdf.cell(120, 10, safe_str(art_name), border=0)
        pdf.cell(60, 10, f"{saatgut_l:,} L", border=0, align="R")
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

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "🛒 Saatgut-Bestellung"])

# --- SEITE 1 ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    with st.expander("⚙️ Verbrauchs-Raten anpassen (pro Hektar)"):
        col_r1, col_r2, col_r3 = st.columns(3)
        r_kalk = col_r1.number_input("Kalk (L/ha):", value=2000)
        r_duenger = col_r2.number_input("Dünger (L/ha):", value=160)
        r_saat = col_r3.number_input("Saatgut (L/ha):", value=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧪 Bedarfskalkulation")
        ha = st.number_input("Hektar (ha):", min_value=0.1, value=1.0, step=0.1)
        st.info(f"""
        **Benötigte Mengen für {ha} ha:**
        * Kalk: **{int(ha * r_kalk):,} L**
        * Dünger: **{int(ha * r_duenger):,} L**
        * Saatgut: **{int(ha * r_saat):,} L**
        """)
    with col2:
        st.subheader("Erloesrechner")
        menge = st.number_input("Liter im Silo:", value=10000)
        preis_pro_1000 = st.number_input("EUR pro 1000L:", value=1200)
        erloes = (menge / 1000) * preis_pro_1000
        st.success(f"**Voraussichtlicher Erloes:**\n### {erloes:,.2f} EUR")

# --- SEITE 2 ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📋 Rechnungs-Ersteller")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["-"])
        std = c2.number_input("Stunden:", min_value=0.1, value=1.0, step=0.1)
        e_p = c3.number_input("Preis (EUR/h):", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("➕ Hinzufuegen"):
            st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
            st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden) if aktuelle_kunden else ck1.text_input("Hofname:")
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)

    if st.session_state.rechnungs_posten:
        st.write("---")
        st.subheader("📋 Aktuelle Posten")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        df_preview.columns = ["Maschine", "Stunden", "Einzelpreis", "Gesamt"]
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Zwischensumme", f"{summe:.2f} EUR")
        col_m2.metric("Endbetrag", f"{total:.2f} EUR")

        st.write("")
        col_b1, col_b2 = st.columns(2)
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt)
        
        col_b1.download_button(
            label="📥 Rechnung als PDF herunterladen",
            data=bytes(pdf_data),
            file_name=f"Rechnung_{safe_str(k_name)}_{date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        if col_b2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3 (UMSCHRIEBEN, DAMIT SIE NIE WIEDER LEER BLEIBT) ---
elif menu == "🛒 Saatgut-Bestellung":
    st.title("🛒 Saatgut- & Materialverwaltung")
    
    st.subheader("📦 Aktueller Hof-Bestand")
    col_s1, col_s2 = st.columns(2)
    vorhanden = col_s1.number_input("Vorhandenes Saatgut am Hof (Liter):", min_value=0, value=3000, step=500)
    verbraucht = col_s2.number_input("Auf den Feldern verbraucht (Liter):", min_value=0, value=0, step=100)
    
    aktueller_bestand = vorhanden - verbraucht
    
    if aktueller_bestand < 1500:
        st.error(f"🚨 Kritischer Bestand! Restmenge: {aktueller_bestand:,} L")
        st.write("---")
        st.subheader("🛒 Nachbestellung aufgeben")
        
        col_b1, col_b2 = st.columns(2)
        b_saat = col_b1.number_input("Saatgut nachbestellen (Liter):", min_value=0, value=2000, step=500)
        b_typ = col_b2.text_input("Fruchtsorte (z.B. Weizen, Raps):", value="")
        
        col_b3, col_b4 = st.columns(2)
        b_kalk = col_b3.number_input("Gleichzeitig Kalk mitbestellen (Liter):", min_value=0, value=0, step=500)
        b_duenger = col_b4.number_input("Gleichzeitig Flüssigdünger mitbestellen (Liter):", min_value=0, value=0, step=100)
        
        if b_saat > 0 or b_kalk > 0 or b_duenger > 0:
            order_pdf_data = generate_order_pdf(b_kalk, b_duenger, b_saat, b_typ)
            st.write("")
            st.download_button(
                label="📥 Bestellzettel als PDF herunterladen",
                data=bytes(order_pdf_data),
                file_name=f"Bestellung_{date.today().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    else:
        st.success(f"✅ Bestand stabil. Restmenge: {aktueller_bestand:,} L")
        st.write("---")
        st.info("ℹ️ Die Bestellfunktion schaltet sich automatisch frei, sobald der Bestand unter 1.500 Liter fällt.")
