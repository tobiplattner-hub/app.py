import streamlit as st
import pandas as pd
from datetime import date
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

# 2. Google Sheet Verbindung
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
PREISLISTE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def load_preisliste():
    try:
        # Sheet laden
        df = pd.read_csv(PREISLISTE_URL)
        # Spaltennamen säubern (Leerzeichen entfernen)
        df.columns = [c.strip() for c in df.columns]
        
        # Falls Spalten fehlen, leeres DF zurückgeben statt Absturz
        if 'Geraet' not in df.columns or 'Preis' not in df.columns:
            st.warning("Spalten 'Geraet' oder 'Preis' nicht im Sheet gefunden!")
            return pd.DataFrame(columns=["Geraet", "Preis"])
            
        return df
    except Exception as e:
        st.error(f"Verbindung zum Google Sheet fehlgeschlagen: {e}")
        return pd.DataFrame(columns=["Geraet", "Preis"])

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
            st.error("Benutzername falsch.")
    st.stop()

# --- DATEN VORBEREITEN ---
df_preise = load_preisliste()

# Falls das Sheet leer ist, Standardwerte nutzen
if df_preise.empty:
    preis_dict = {"Keine Daten im Sheet": 0.0}
else:
    # Dictionary erstellen
    preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis']))

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    col1, col2 = st.columns(2)
    with col1:
        st.header("⚪ Kalkulation")
        ha = st.number_input("Hektar:", value=1.0)
        st.write(f"Kalk: **{int(ha * 2000)} L**")
    with col2:
        st.header("🌾 Erlös")
        l = st.number_input("Liter:", value=10000)
        p = st.number_input("Preis/1000L:", value=1200)
        st.metric("Erlös", f"{(l/1000)*p:,.2f} €")

elif menu == "📋 Rechnungs-Ersteller":
    st.title("📄 Rechnungs-Ersteller")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        
        # Gerät auswählen
        geraete_liste = list(preis_dict.keys())
        auswahl = c1.selectbox("Gerät wählen:", options=geraete_liste)
        
        # Menge
        stunden = c2.number_input("h:", min_value=0.0, value=1.0, step=0.5)
        
        # PREIS-LOGIK (FEHLERSICHER)
        roher_preis = preis_dict.get(auswahl, 0.0)
        try:
            # Falls im Sheet Text steht oder das Feld leer ist
            start_preis = float(roher_preis) if pd.notnull(roher_preis) else 0.0
        except:
            start_preis = 0.0
            
        einzelpreis = c3.number_input("€/h:", value=start_preis)
        
        if st.button("Hinzufügen"):
            st.session_state.rechnungs_posten.append({
                "name": auswahl, "std": stunden, "preis": einzelpreis, "gesamt": stunden * einzelpreis
            })
            st.rerun()

    # Rechnungsvorschau
    if st.session_state.rechnungs_posten:
        st.write("---")
        with st.container(border=True):
            cl, cr = st.columns([1,1])
            with cl:
                if os.path.exists("logo.png"): st.image("logo.png", width=150)
                else: st.write("### 🚜 LU-BETRIEB")
            with cr:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
            
            st.write("---")
            summe = 0
            for p in st.session_state.rechnungs_posten:
                st.write(f"{p['name']} | {p['std']}h x {p['preis']}€ = **{p['gesamt']:.2f}€**")
                summe += p['gesamt']
            st.write("---")
            st.subheader(f"Gesamtbetrag: {summe:.2f} €")

        if st.button("🗑️ Liste leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
