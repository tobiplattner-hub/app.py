import streamlit as st
import pandas as pd
from datetime import date
import os
import base64

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- LOGO HELPER ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- DER ULTIMATIVE DRUCK-FIX PER CSS ---
st.markdown("""
<style>
    /* Das Druck-Element ist im Browser standardmäßig KOMPLETT UNSICHTBAR */
    #print-section {
        display: none !important;
    }
    
    /* Erst beim Drucken greift diese radikale Umstellung */
    @media print {
        /* Verstecke die gesamte Streamlit-Oberfläche inklusive aller Container */
        .stApp, [data-testid="stSidebar"], header, footer, .stButton, [data-testid="stHeader"] {
            display: none !important;
            visibility: hidden !important;
        }
        
        /* Mache NUR das reine HTML-Druck-Element sichtbar */
        #print-section {
            display: block !important;
            visibility: visible !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 210mm !important; /* Exakt A4 Breite */
            font-family: Arial, sans-serif !important;
            color: black !important;
            background: white !important;
        }
        
        @page {
            size: A4;
            margin: 15mm;
        }
    }
</style>
""", unsafe_allow_html=True)

# 2. Daten-Verbindung
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

# Daten laden
df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state: 
    st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

# --- BEREICH 1: ERNTE & KALKULATION ---
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
        * ⚪ Kalk: **{int(ha * r_kalk):,} L**
        * 💧 Dünger: **{int(ha * r_duenger):,} L**
        * 🌾 Saatgut: **{int(ha * r_saat):,} L**
        """)
    
    with col2:
        st.subheader("🌾 Erlösrechner")
        menge = st.number_input("Liter im Silo:", value=10000)
        preis_pro_1000 = st.number_input("€ pro 1000L:", value=1200)
        erloes = (menge / 1000) * preis_pro_1000
        st.success(f"**Voraussichtlicher Erlös:**\n### {erloes:,.2f} €")

# --- BEREICH 2: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📋 Rechnungs-Ersteller")
    
    # Eingabe-Maske
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["-"])
        std = c2.number_input("Stunden:", min_value=0.1, value=1.0, step=0.1)
        e_p = c3.number_input("Preis (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("➕ Hinzufügen"):
            st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
            st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden) if aktuelle_kunden else ck1.text_input("Hofname:")
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)

    # RECHNUNGSDESIGN
    if st.session_state.rechnungs_posten:
        st.write("---")
        
        # 1. Schicke, native Streamlit-Vorschau (KEIN Textfehler möglich, da Pandas-Tabelle!)
        st.subheader("📋 Rechnungsvorschau")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        df_preview.columns = ["Leistung / Maschine", "Menge (h)", "Einzelpreis (€/h)", "Gesamtpreis (€)"]
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        
        st.metric(label="Zwischensumme", value=f"{summe:.2f} €")
        if rabatt > 0:
            st.metric(label=f"Rabatt ({rabatt}%)", value=f"-{summe*(rabatt/100):.2f} €")
        st.metric(label="RECHNUNGSENDBETRAG", value=f"{total:.2f} €")

        # 2. Das unsichtbare HTML-Druck-Element (Wird erst beim Klick auf Drucken aktiv)
        logo_data = get_base64_image("logo.png")
        items_html = "".join([f"<tr style='border-bottom: 1px solid #ddd;'><td style='padding: 10px;'>{p['name']}</td><td style='padding: 10px;'>{p['std']} h</td><td style='padding: 10px;'>{p['preis']:.2f} €</td><td style='padding: 10px; text-align: right;'>{p['gesamt']:.2f} €</td></tr>" for p in st.session_state.rechnungs_posten])
        rabatt_html = f"<tr><td colspan='3' style='text-align: right; padding: 5px;'>Rabatt ({rabatt}%):</td><td style='text-align: right; padding: 5px;'>-{summe*(rabatt/100):.2f} €</td></tr>" if rabatt > 0 else ""

        # WICHTIG: Das div hat die ID "print-section". Das CSS steuert dieses Element unabhängig von Streamlit.
        druck_html = f"""
        <div id="print-section">
            <table style="width: 100%; border: none; margin-bottom: 30px;">
                <tr>
                    <td style="text-align: left; vertical-align: middle;">
                        {f'<img src="data:image/png;base64,{logo_data}" width="180">' if logo_data else '<h2>🚜 LU-BETRIEB</h2>'}
                    </td>
                    <td style="text-align: right; vertical-align: middle; font-size: 14px; line-height: 1.6;">
                        <strong>Datum:</strong> {date.today().strftime('%d.%m.%Y')}<br>
                        <strong>Kunde:</strong> {k_name}
                    </td>
                </tr>
            </table>
            <hr style="border: none; border-top: 3px solid black; margin: 10px 0;">
            <h1 style="margin: 15px 0; font-size: 32px; letter-spacing: 1px;">RECHNUNG</h1>
            <hr style="border: none; border-top: 3px solid black; margin: 10px 0;">
            <table style="width:100%; border-collapse:collapse; margin: 25px 0;">
                <thead>
                    <tr style="border-bottom: 2px solid black; background-color: #f2f2f2; text-align: left; font-weight: bold;">
                        <th style="padding: 12px 10px;">Leistung / Maschine</th>
                        <th style="padding: 12px 10px;">Menge</th>
                        <th style="padding: 12px 10px;">Einzelpreis</th>
                        <th style="padding: 12px 10px; text-align: right;">Gesamt</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>
            <table style="width: 100%; margin-top: 30px;">
                <tr>
                    <td style="width: 50%;"></td>
                    <td style="width: 50%;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr><td style="text-align: right; padding: 5px;">Zwischensumme:</td><td style="text-align: right; padding: 5px; width: 120px;">{summe:.2f} €</td></tr>
                            {rabatt_html}
                            <tr style="font-size: 20px; font-weight: bold;">
                                <td style="text-align: right; padding: 15px 5px 5px 5px; border-top: 2px solid black;">GESAMT:</td>
                                <td style="text-align: right; padding: 15px 5px 5px 5px; border-top: 2px solid black;">{total:.2f} €</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        """
        # Wir injizieren das HTML direkt in die Seite. Im Browser unsichtbar, im Druck sichtbar!
        st.markdown(druck_html, unsafe_allow_html=True)

        # Buttons unter der Vorschau
        st.write("")
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🖨️ Rechnung drucken (A4)"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
        if col_b2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()
