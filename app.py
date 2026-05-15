import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- CSS für sauberen Druck (Blendet Sidebar und Buttons beim Drucken aus) ---
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer, .no-print { 
            display: none !important; 
        }
        .main .block-container { 
            padding-top: 0rem !important; 
        }
        .print-container {
            border: 1px solid #ccc !important;
            padding: 20px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Verbindung
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
PREISLISTE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"

@st.cache_data(ttl=10)
def load_preisliste():
    try:
        df = pd.read_csv(PREISLISTE_URL)
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
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
    st.stop()

# --- DATEN LADEN ---
df_preise = load_preisliste()
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}

# Beispiel Kundenliste (Kannst du hier erweitern)
kunden_liste = ["Hof Bergmann", "Gut Höhne", "Lohnbetrieb Müller", "Bio-Hof Maier", "Manuelle Eingabe"]

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller"])

# --- BEREICH: ERNTE & FELDER ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("🧪 Verbrauchs-Rechner")
        ha = st.number_input("Feldgröße (Hektar):", value=1.0, min_value=0.1, step=0.1)
        st.write(f"⚪ **Kalkbedarf:** {int(ha * 2000)} L")
        st.write(f"💧 **Düngerbedarf:** {int(ha * 160)} L")
        st.write(f"🌾 **Saatgutbedarf:** {int(ha * 150)} L")
        st.info("Werte basieren auf Standard-Verbrauchswerten.")

    with col2:
        st.header("🌾 Erlös-Rechner")
        liter = st.number_input("Liter im Silo:", value=10000, step=1000)
        p_1000 = st.number_input("Preis pro 1000L (€):", value=1200)
        st.metric("Dein Erlös", f"{(liter/1000)*p_1000:,.2f} €")

# --- BEREICH: RECHNUNGS-ERSTELLER ---
with st.container(border=True):
    st.subheader("➕ Posten hinzufügen")
    c1, c2, c3 = st.columns([2, 1, 1])
    
    auswahl = c1.selectbox("Gerät/Leistung:", options=list(preis_dict.keys()) if preis_dict else ["Keine Daten"])
    
    # NEU: min_value=0.0 und step=0.1 für feinere Zeiterfassung
    stunden = c2.number_input("Dauer (h):", min_value=0.0, value=1.0, step=0.1)
    
    # Preislogik
    standard_preis = float(preis_dict.get(auswahl, 0.0))
    einzelpreis = c3.number_input("€/h:", value=standard_preis)
    
    if st.button("Posten hinzufügen"):
        # Sicherstellen, dass auch wirklich etwas gearbeitet wurde
        if stunden > 0:
            st.session_state.rechnungs_posten.append({
                "name": auswahl, 
                "std": stunden, 
                "preis": einzelpreis, 
                "gesamt": stunden * einzelpreis
            })
            st.rerun()
        else:
            st.warning("Bitte gib eine Dauer größer als 0 an.")

    # Kunden-Auswahl
    col_k1, col_k2 = st.columns(2)
    kunden_wahl = col_k1.selectbox("Kunde auswählen:", options=kunden_liste)
    if kunden_wahl == "Manuelle Eingabe":
        kunde_final = col_k1.text_input("Name eingeben:")
    else:
        kunde_final = kunden_wahl
        
    rabatt = col_k2.slider("Rabatt auf Alles (%)", 0, 50, 0)

    # RECHNUNGS-VORSCHAU
    if st.session_state.rechnungs_posten:
        st.write("---")
        
        # Dieser Bereich wird gedruckt
        with st.container(border=True):
            st.markdown('<div class="print-container">', unsafe_allow_html=True)
            
            # Header
            cl, cr = st.columns([1,1])
            with cl:
                if os.path.exists("logo.png"):
                    st.image("logo.png", width=150)
                else:
                    st.write("### 🚜 LU-BETRIEB")
            with cr:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                st.write(f"**Empfänger:** {kunde_final}")
            
            st.write("---")
            st.markdown("### RECHNUNG")
            
            # Tabelle
            tabelle = "| Beschreibung | Menge | Preis/h | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
            summe_n = 0
            for p in st.session_state.rechnungs_posten:
                tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                summe_n += p['gesamt']
            st.markdown(tabelle)
            
            # Fußzeile
            abzug = summe_n * (rabatt / 100)
            st.write("---")
            e1, e2 = st.columns([2, 1])
            with e2:
                st.write(f"Zwischensumme: {summe_n:.2f} €")
                if rabatt > 0: st.write(f"Rabatt: -{abzug:.2f} €")
                st.subheader(f"Gesamt: {summe_n - abzug:.2f} €")
            
            st.markdown('</div>', unsafe_allow_html=True)

        # BUTTONS (Diese werden nicht mitgedruckt)
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("🖨️ Drucken / Als PDF"):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
                st.info("Falls der Druckdialog nicht öffnet, drücke Strg + P (oder Cmd + P am Mac).")
        with col_btn2:
            if st.button("🗑️ Liste leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
