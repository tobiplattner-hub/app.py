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

# --- CSS FÜR ANZEIGE UND DRUCK (KEIN WEISSES BLATT MEHR) ---
st.markdown("""
    <style>
    /* Verstecke die Streamlit-Elemente NUR beim Drucken */
    @media print {
        header, footer, .no-print, [data-testid="stSidebar"], [data-testid="stHeader"], .stButton {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] {
            background-color: white !important;
        }
        .main .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }
        .print-invoice {
            display: block !important;
            width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
    }
    /* Styling für die Rechnungsvorschau in der App */
    .print-invoice {
        background-color: white;
        padding: 40px;
        border: 1px solid #ddd;
        border-radius: 8px;
        color: black !important;
        font-family: Arial, sans-serif;
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
    except: return pd.DataFrame()

# 3. Login
if "user_correct" not in st.session_state: st.session_state["user_correct"] = False
if not st.session_state["user_correct"]:
    st.title("🔐 LS25 Hof-Login")
    if st.text_input("Benutzername:") == "LS25-Team":
        if st.button("Einloggen"):
            st.session_state["user_correct"] = True
            st.rerun()
    st.stop()

# Daten laden
df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

# --- BEREICH 1: ERNTE & KALKULATION (WIEDER DA!) ---
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
    st.markdown('<h1 class="no-print">📋 Rechnungs-Ersteller</h1>', unsafe_allow_html=True)
    
    # Eingabe-Maske
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["-"])
        std = c2.number_input("Stunden:", min_value=0.1, value=1.0, step=0.1)
        e_p = c3.number_input("Preis (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("➕ Hinzufügen"):
            st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
            st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden)
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)
    st.markdown('</div>', unsafe_allow_html=True)

    # RECHNUNGSDESIGN
    if st.session_state.rechnungs_posten:
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        logo_data = get_base64_image("logo.png")
        
        # Das HTML wird nun direkt in st.markdown ausgegeben (kein Iframe = kein weißes Blatt)
        items_html = "".join([f"<tr><td style='padding:8px 0; border-bottom:1px solid #eee;'>{p['name']}</td><td style='padding:8px 0; border-bottom:1px solid #eee;'>{p['std']} h</td><td style='padding:8px 0; border-bottom:1px solid #eee;'>{p['preis']:.2f} €</td><td style='padding:8px 0; border-bottom:1px solid #eee; text-align:right;'>{p['gesamt']:.2f} €</td></tr>" for p in st.session_state.rechnungs_posten])
        
        rechnung_html = f"""
        <div class="print-invoice">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>{f'<img src="data:image/png;base64,{logo_data}" width="150">' if logo_data else '<h2>🚜 LU-BETRIEB</h2>'}</div>
                <div style="text-align:right;"><strong>Datum:</strong> {date.today().strftime('%d.%m.%Y')}<br><strong>Kunde:</strong> {k_name}</div>
            </div>
            <hr style="border:2px solid black; margin:20px 0;">
            <h1 style="margin:0;">RECHNUNG</h1>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                <thead><tr style="border-bottom:2px solid black; text-align:left;"><th>Leistung</th><th>Menge</th><th>Einzel</th><th style="text-align:right;">Gesamt</th></tr></thead>
                <tbody>{items_html}</tbody>
            </table>
            <div style="text-align:right; margin-top:20px;">
                <p>Zwischensumme: {summe:.2f} €</p>
                {f'<p>Rabatt: -{summe*(rabatt/100):.2f} €</p>' if rabatt > 0 else ''}
                <h2 style="border-top:2px solid black; display:inline-block; padding-top:10px;">GESAMT: {total:.2f} €</h2>
            </div>
        </div>
        """
        st.markdown(rechnung_html, unsafe_allow_html=True)

        # Buttons
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🖨️ Jetzt Drucken"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        if col_b2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
