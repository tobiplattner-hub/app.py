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

# --- DATA FOR PRODUCTIONS (LS-Standardwerte pro Monat im 24h Betrieb) ---
# Format: { Rezeptname: (Input_Je_Monat, Output_Je_Monat, Input_Name, Output_Name) }
PROD_DATA = {
    "Getreidemühle: Weizen zu Mehl": (36000, 27000, "Weizen (L)", "Mehl (L)"),
    "Getreidemühle: Gerste zu Mehl": (36000, 27000, "Gerste (L)", "Mehl (L)"),
    "Bäckerei: Brot": (21600, 10800, "Mehl (L)", "Brot (L/Zyklen)"),
    "Bäckerei: Kuchen": (4320, 4320, "Mehl/Zucker/Milch/Eier/Erdbeeren (Mix)", "Kuchen (L/Zyklen)"),
    "Ölmühle: Sonnenblumenöl": (14400, 7200, "Sonnenblumen (L)", "Sonnenblumenöl (L)"),
    "Ölmühle: Rapsöl": (14400, 7200, "Raps (L)", "Rapsöl (L)"),
    "Molkerei: Butter": (36000, 21600, "Milch (L)", "Butter (L)"),
    "Molkerei: Käse": (21600, 16200, "Milch (L)", "Käse (L)"),
    "Zuckerfabrik: Zuckerrohr": (28800, 28800, "Zuckerrohr (L)", "Zucker (L)"),
    "Zuckerfabrik: Zuckerrüben": (14400, 7200, "Zuckerrüben (L)", "Zucker (L)")
}

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "🛒 Saatgut-Bestellung", "🏭 Produktions-Planer"])

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

# --- SEITE 3 ---
elif menu == "🛒 Saatgut-Bestellung":
    st.title("🛒 Material- & Lagerverwaltung")
    st.subheader("📦 Aktueller Hof-Bestand")
    col_s, col_k, col_d = st.columns(3)
    
    with col_s:
        st.markdown("### 🌱 Saatgut")
        v_saat = st.number_input("Vorhanden (L):", min_value=0, value=3000, step=500, key="v_saat")
        g_saat = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_saat")
        b_saat = v_saat - g_saat
        if b_saat < 1500: st.error(f"🚨 Kritisch: {b_saat:,} L\n(Unter 1.500 L)")
        else: st.success(f"✅ Stabil: {b_saat:,} L")
            
    with col_k:
        st.markdown("### ⚪ Kalk")
        v_kalk = st.number_input("Vorhanden (L):", min_value=0, value=10000, step=1000, key="v_kalk")
        g_kalk = st.number_input("Verbraucht (L):", min_value=0, value=0, step=500, key="g_kalk")
        b_kalk = v_kalk - g_kalk
        if b_kalk < 5000: st.error(f"🚨 Kritisch: {b_kalk:,} L\n(Unter 5.000 L)")
        else: st.success(f"✅ Stabil: {b_kalk:,} L")
            
    with col_d:
        st.markdown("### 🧪 Flüssigdünger")
        v_dueng = st.number_input("Vorhanden (L):", min_value=0, value=2000, step=500, key="v_dueng")
        g_dueng = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_dueng")
        b_dueng = v_dueng - g_dueng
        if b_dueng < 1000: st.error(f"🚨 Kritisch: {b_dueng:,} L\n(Unter 1.000 L)")
        else: st.success(f"✅ Stabil: {b_dueng:,} L")
            
    st.write("---")
    if b_saat < 1500 or b_kalk < 5000 or b_dueng < 1000:
        st.subheader("🛒 Nachbestellung aufgeben")
        col_b1, col_b2 = st.columns(2)
        init_saat = 2000 if b_saat < 1500 else 0
        order_saat = col_b1.number_input("Saatgut nachbestellen (Liter):", min_value=0, value=init_saat, step=500)
        b_typ = col_b2.text_input("Fruchtsorte (z.B. Weizen, Raps):", value="")
        
        col_b3, col_b4 = st.columns(2)
        init_kalk = 5000 if b_kalk < 5000 else 0
        order_kalk = col_b3.number_input("Kalk nachbestellen (Liter):", min_value=0, value=init_kalk, step=1000)
        init_dueng = 1000 if b_dueng < 1000 else 0
        order_dueng = col_b4.number_input("Flüssigdünger nachbestellen (Liter):", min_value=0, value=init_dueng, step=500)
        
        if order_saat > 0 or order_kalk > 0 or order_dueng > 0:
            order_pdf_data = generate_order_pdf(order_kalk, order_dueng, order_saat, b_typ)
            st.write("")
            st.download_button(label="📥 Bestellzettel als PDF herunterladen", data=bytes(order_pdf_data), file_name=f"Bestellung_{date.today().strftime('%Y%m%d')}.pdf", mime="application/pdf")
    else:
        st.info("ℹ️ Die Bestellfunktion schaltet sich automatisch frei, sobald einer deiner Bestände ins Minus bzw. unter das Limit rutscht.")

# --- NEUER BEREICH 4: PRODUKTIONS-PLANER ---
elif menu == "🏭 Produktions-Planer":
    st.title("🏭 LS-Produktionsketten Rechner")
    st.write("Planst du deine Ernte? Berechne hier, wie viel Rohstoff deine Fabriken im Jahr fressen und wie viel Paletten am Ende herauskommen.")
    
    with st.container(border=True):
        # Rezept-Auswahl
        rezept = st.selectbox("Wähle deine Produktion/Rezept aus:", options=list(PROD_DATA.keys()))
        
        # Laufzeit in Monaten (Viele Fabriken laufen ja nicht ganzjährig)
        monate = st.slider("Betriebsdauer der Fabrik im Jahr (Monate):", min_value=1, max_value=12, value=12)
        
        # Anzahl der parallel laufenden Linien/Fabriken
        anzahl_fabriken = st.number_input("Anzahl dieser Fabriken/Produktionslinien auf deinem Hof:", min_value=1, value=1, step=1)
    
    # Werte aus der Datenbank holen
    base_in, base_out, in_name, out_name = PROD_DATA[rezept]
    
    # Berechnung hochrechnen
    gesamt_input = base_in * monate * anzahl_fabriken
    gesamt_output = base_out * monate * anzahl_fabriken
    
    st.write("---")
    st.subheader("📊 Berechneter Jahresumsatz")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.info(f"""
        **Benötigter Rohstoff (INPUT):**
        ### {gesamt_input:,} Liter
        Das musst du im Jahr anliefern, um die Fabrik für {monate} Monate auszulasten.
        """)
        
    with col_p2:
        st.success(f"""
        **Erzeugte Produkte (OUTPUT):**
        ### {gesamt_output:,} Liter / Einheiten
        Das ist die Menge, die am Ende als Paletten am Trigger spawnt.
        """)
        
    # Kleiner Profi-Tipp für den Spieler
    st.write("")
    st.caption(f"💡 *Hinweis basierend auf den LS-Standard-XML-Daten: Dieses Rezept verarbeitet im Dauerbetrieb exakt {int(base_in/24):,} L pro Tag.*")
