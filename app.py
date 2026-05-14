import streamlit as st
from streamlit_gsheets import GSheetsConnection
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
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Verbindung zum Google Sheet
# Kopiere deinen Google Sheet Link hier rein:
url = "https://docs.google.com/spreadsheets/d/1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

# Funktion zum Laden der Preisliste
@st.cache_data(ttl=60) # Aktualisiert sich alle 60 Sekunden
def load_prices(url):
    return conn.read(spreadsheet=url, worksheet="Preisliste")

# 3. Login
def check_user():
    if "user_correct" not in st.session_state:
        st.session_state["user_correct"] = False
    if not st.session_state["user_correct"]:
        st.title("🔐 LS25 Hof-Login")
        username = st.text_input("Benutzername:", key="login_name")
        if st.button("Einloggen"):
            if username == "LS25-Team": 
                st.session_state["user_correct"] = True
                st.rerun()
        return False
    return True

if check_user():
    # Preisliste laden
    try:
        df_preise = load_prices(url)
        # Umwandeln in ein Dictionary für die App
        preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis']))
    except:
        st.error("Fehler: Konnte Google Sheet nicht laden. Prüfe den Link!")
        preis_dict = {"Fehler": 0.0}

    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []

    menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

    # --- ERNTE & KALK ---
    if menu == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        col1, col2 = st.columns(2)
        with col1:
            st.header("💰 Erlös-Rechner")
            menge = st.number_input("Liter im Silo:", value=10000, step=1000)
            preis_l = st.number_input("Preis pro 1000L (€):", value=1200)
            st.metric("Erlös", f"{(menge/1000)*preis_l:,.2f} €")
        with col2:
            st.header("🧪 Verbrauchs-Rechner")
            hektar = st.number_input("Hektar:", value=1.0, step=0.1)
            st.write(f"⚪ Kalk: **{int(hektar * 2000)} L**")
            st.write(f"💧 Dünger: **{int(hektar * 160)} L**")

    # --- RECHNUNG ---
    elif menu == "📋 Rechnungs-Ersteller":
        st.title("📄 Gemeinsame Abrechnung")
        
        with st.container(border=True):
            c_a, c_b, c_c = st.columns([2, 1, 1])
            with c_a:
                auswahl = st.selectbox("Maschine (aus Google Sheet):", options=list(preis_dict.keys()))
            with c_b:
                std = st.number_input("Stunden:", value=1.0, step=0.5)
            with c_c:
                e_preis = st.number_input("Preis (€):", value=float(preis_dict.get(auswahl, 0)))
            
            if st.button("Hinzufügen"):
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_preis, "gesamt": std * e_preis})
                st.rerun()

        kunde = st.text_input("Kunde:", value="Hof Bergmann")
        rabatt = st.slider("Rabatt (%)", 0, 50, 0)

        if st.session_state.rechnungs_posten:
            with st.container(border=True):
                # Rechnungskopf
                cl, cr = st.columns([1, 1])
                with cl:
                    if os.path.exists("logo.png"): st.image("logo.png", width=150)
                    else: st.write("### 🚜 LU-BETRIEB")
                with cr:
                    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}\n\n**Kunde:** {kunde}")
                
                st.write("---")
                # Tabelle
                summe = 0
                st.write("**Posten:**")
                for p in st.session_state.rechnungs_posten:
                    st.write(f"{p['name']} | {p['std']}h x {p['preis']}€ = **{p['gesamt']:.2f}€**")
                    summe += p['gesamt']
                
                # Summe & Rabatt
                st.write("---")
                abzug = summe * (rabatt / 100)
                st.write(f"### Gesamtbetrag: {summe - abzug:.2f} €")

            if st.button("🗑️ Rechnung leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()
