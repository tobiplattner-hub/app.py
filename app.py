import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- CSS für Druck & Design ---
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer { display: none !important; }
        .main .block-container { padding-top: 0rem !important; }
        .print-area { border: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Verbindung (Dein Link)
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
# Wir bauen den Export-Link für das erste Blatt (gid=0)
PREISLISTE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

# Funktion zum Laden der Daten
@st.cache_data(ttl=10)
def load_preisliste():
    try:
        df = pd.read_csv(PREISLISTE_URL)
        # Bereinigung: Leerzeichen aus Spaltennamen entfernen
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden der Preisliste: {e}")
        return pd.DataFrame(columns=["Geraet", "Preis"])

# 3. Login-Logik
if "user_correct" not in st.session_state:
    st.session_state["user_correct"] = False

if not st.session_state["user_correct"]:
    st.title("🔐 LS25 Hof-Login")
    username = st.text_input("Benutzername:")
    if st.button("Einloggen"):
        if username == "LS25-Team":
            st.session_state["user_correct"] = True
            st.rerun()
        else:
            st.error("Benutzername nicht erkannt.")
    st.stop()

# --- HAUPTPROGRAMM ---
df_preise = load_preisliste()
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis']))

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    col1, col2 = st.columns(2)
    with col1:
        st.header("💰 Kalkulation")
        hektar = st.number_input("Feldgröße (ha):", value=1.0, min_value=0.1)
        st.write(f"⚪ Kalk: **{int(hektar * 2000)} L**")
        st.write(f"💧 Dünger: **{int(hektar * 160)} L**")
    with col2:
        st.header("🌾 Erlös")
        liter = st.number_input("Liter im Silo:", value=10000)
        preis_1000 = st.number_input("Preis / 1000L:", value=1200)
        st.metric("Erlös", f"{(liter/1000)*preis_1000:,.2f} €")

elif menu == "📋 Rechnungs-Ersteller":
    st.title("📄 Rechnungs-Ersteller")
    
    # Eingabemaske
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Gerät wählen:", options=list(preis_dict.keys()))
        stunden = c2.number_input("h:", min_value=0.5, value=1.0, step=0.5)
        einzelpreis = c3.number_input("€/h:", value=float(preis_dict.get(auswahl, 0)))
        
        if st.button("Hinzufügen"):
            st.session_state.rechnungs_posten.append({
                "name": auswahl, "std": stunden, "preis": einzelpreis, "gesamt": stunden * einzelpreis
            })
            st.rerun()

    kunde = st.text_input("Kunde:", value="Hof Bergmann")
    rabatt = st.slider("Rabatt (%)", 0, 50, 0)

    # Rechnungsvorschau
    if st.session_state.rechnungs_posten:
        st.write("---")
        with st.container(border=True):
            # Header
            cl, cr = st.columns([1,1])
            with cl:
                if os.path.exists("logo.png"): st.image("logo.png", width=150)
                else: st.write("### 🚜 LU-BETRIEB")
            with cr:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                st.write(f"**Kunde:** {kunde}")
            
            st.write("---")
            st.write("### RECHNUNG")
            
            # Tabelle
            tabelle = "| Posten | Menge | Preis/h | Summe |\n| :--- | :--- | :--- | :--- |\n"
            summe_netto = 0
            for p in st.session_state.rechnungs_posten:
                tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                summe_netto += p['gesamt']
            st.markdown(tabelle)
            
            # Fußzeile
            abzug = summe_netto * (rabatt / 100)
            total = summe_netto - abzug
            
            st.write("---")
            e1, e2 = st.columns([2, 1])
            with e2:
                st.write(f"Zwischensumme: {summe_netto:.2f} €")
                if rabatt > 0: st.write(f"Rabatt: -{abzug:.2f} €")
                st.subheader(f"Gesamt: {total:.2f} €")

        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🗑️ Liste leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()
        with col_b2:
            st.write("Tipp: Strg + P zum Drucken")

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
