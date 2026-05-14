import streamlit as st
from streamlit_gsheets import GSheetsConnection
from datetime import date
import pandas as pd
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- CSS für sauberen Druck ---
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer { display: none !important; }
        .main .block-container { padding-top: 0rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Verbindung zum Google Sheet
# ERSETZE DIESEN LINK DURCH DEINEN KOPIERTEN LINK:
URL = "https://docs.google.com/spreadsheets/d/1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# Preisliste laden
@st.cache_data(ttl=10) # Schaut alle 10 Sekunden nach Updates
def load_data():
    prices = conn.read(spreadsheet=URL, worksheet="Preisliste")
    archive = conn.read(spreadsheet=URL, worksheet="Archiv")
    return prices, archive

# 3. Login
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
            st.error("Falscher Name")
    st.stop()

# --- DATEN LADEN ---
try:
    df_preise, df_archiv = load_data()
    preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis']))
except Exception as e:
    st.error(f"Verbindung zum Google Sheet fehlgeschlagen. Link prüfen! Fehler: {e}")
    st.stop()

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungen", "📂 Archiv (Team)"])

# --- BEREICH: RECHNUNGEN ---
if menu == "📋 Rechnungen":
    st.title("📄 Team-Abrechnung")
    
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []

    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()))
        std = c2.number_input("Stunden:", min_value=0.5, value=1.0, step=0.5)
        e_preis = c3.number_input("Preis (€):", value=float(preis_dict.get(auswahl, 0)))
        
        if st.button("Hinzufügen"):
            st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_preis, "gesamt": std * e_preis})
            st.rerun()

    kunde = st.text_input("Kunde:", value="Hof Bergmann")
    rabatt = st.slider("Rabatt (%)", 0, 50, 0)

    if st.session_state.rechnungs_posten:
        # Rechnungs-Vorschau
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        endbetrag = summe * (1 - rabatt/100)

        with st.container(border=True):
            col_l, col_r = st.columns([1,1])
            with col_l:
                if os.path.exists("logo.png"): st.image("logo.png", width=150)
                else: st.write("### 🚜 LU-BETRIEB")
            with col_r:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}\n\n**Kunde:** {kunde}")
            
            st.write("---")
            for p in st.session_state.rechnungs_posten:
                st.write(f"{p['name']} | {p['std']}h x {p['preis']}€ = **{p['gesamt']:.2f}€**")
            st.write("---")
            st.write(f"### Gesamtbetrag: {endbetrag:.2f} €")

        if st.button("✅ Rechnung abschließen & Speichern"):
            # Daten für Google Sheet Archiv vorbereiten
            neuer_eintrag = pd.DataFrame([{
                "Datum": str(date.today()),
                "Kunde": kunde,
                "Summe": f"{endbetrag:.2f}€",
                "Details": ", ".join([p['name'] for p in st.session_state.rechnungs_posten])
            }])
            
            # Im Archiv-Blatt speichern
            updated_df = pd.concat([df_archiv, neuer_eintrag], ignore_index=True)
            conn.update(spreadsheet=URL, worksheet="Archiv", data=updated_df)
            
            st.success("Rechnung wurde im Google Sheet archiviert!")
            st.session_state.rechnungs_posten = []
            st.cache_data.clear() # Cache leeren, damit andere es sofort sehen
            st.rerun()

# --- BEREICH: ARCHIV ---
elif menu == "📂 Archiv (Team)":
    st.title("📂 Alle Rechnungen")
    st.write("Hier sehen alle Teammitglieder die letzten Buchungen:")
    st.table(df_archiv.tail(10)) # Zeigt die letzten 10 Rechnungen

# --- BEREICH: ERNTE ---
elif menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte & Kalk")
    hektar = st.number_input("Hektar:", value=1.0)
    st.write(f"⚪ Kalkbedarf: **{int(hektar * 2000)} L**")
    st.info("Diese Daten sind aktuell nur für dich lokal berechnet.")
