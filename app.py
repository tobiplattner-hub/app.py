import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- CSS für Druck-Layout ---
st.markdown("""
    <style>
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer, .no-print { 
            display: none !important; 
        }
        .main .block-container { 
            padding-top: 0rem !important; 
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Verbindung
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
KUNDEN_GID = "568043650"

# URLs für den Datenabruf
PREIS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
KUNDEN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={KUNDEN_GID}"

# Funktion zum Laden (mit Cache für Geschwindigkeit)
@st.cache_data(ttl=5)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

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
df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}

df_kunden = load_data(KUNDEN_URL)
# Wir filtern leere Zeilen aus der Kundenliste
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "👥 Kunden-Verwaltung"])

# --- BEREICH 1: ERNTE & VERBRAUCH ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    col1, col2 = st.columns(2)
    with col1:
        st.header("🧪 Feld-Bedarf")
        ha = st.number_input("Hektar:", value=1.0, step=0.1, min_value=0.0)
        st.write(f"⚪ Kalk: **{int(ha * 2000)} L**")
        st.write(f"💧 Dünger: **{int(ha * 160)} L**")
        st.write(f"🌾 Saatgut: **{int(ha * 150)} L**")
    with col2:
        st.header("🌾 Erlös-Rechner")
        menge = st.number_input("Liter im Silo:", value=10000, step=1000)
        p_pro_1000 = st.number_input("Preis/1000L (€):", value=1200)
        st.metric("Erlös", f"{(menge/1000)*p_pro_1000:,.2f} €")

# --- BEREICH 2: KUNDEN-VERWALTUNG (ZUM SPEICHERN) ---
elif menu == "👥 Kunden-Verwaltung":
    st.title("👥 Hof-Namen verwalten")
    st.write("Hier kannst du neue Höfe dauerhaft für das Team speichern.")
    
    neuer_hof = st.text_input("Neuer Hof-Name:")
    if st.button("Hof dauerhaft speichern"):
        if neuer_hof and neuer_hof not in aktuelle_kunden:
            # Hier nutzen wir die st-gsheets-connection Funktionalität zum Schreiben
            try:
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                
                # Neues DataFrame mit dem neuen Kunden erstellen
                new_row = pd.DataFrame([{"Name": neuer_hof}])
                updated_df = pd.concat([df_kunden, new_row], ignore_index=True)
                
                # Zurück ins Sheet schreiben
                conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}", 
                            worksheet="Kunden", data=updated_df)
                
                st.success(f"'{neuer_hof}' wurde gespeichert! Starte die App neu oder warte kurz.")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")
                st.info("Tipp: Du kannst den Namen auch direkt im Google Sheet in die Spalte 'Name' schreiben.")
        else:
            st.warning("Name leer oder bereits vorhanden.")
    
    st.write("### Aktuelle Höfe im System:")
    st.write(", ".join(aktuelle_kunden))

# --- BEREICH 3: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📄 Rechnungs-Ersteller")
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        geraet_wahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()))
        # Jetzt mit 0.1 Schritten und ab 0.0 möglich
        std_eingabe = c2.number_input("Stunden:", min_value=0.0, value=1.0, step=0.1)
        preis_eingabe = c3.number_input("€/h:", value=float(preis_dict.get(geraet_wahl, 0.0)))
        
        if st.button("Posten hinzufügen"):
            if std_eingabe > 0:
                st.session_state.rechnungs_posten.append({
                    "name": geraet_wahl, "std": std_eingabe, "preis": preis_eingabe, "gesamt": std_eingabe * preis_eingabe
                })
                st.rerun()

    # Kunden-Auswahl für die Rechnung
    st.subheader("👤 Rechnungsempfänger")
    ck1, ck2 = st.columns(2)
    kunde_rechnung = ck1.selectbox("Hof auswählen:", options=["-- Bitte wählen --"] + aktuelle_kunden + ["Manuelle Eingabe"])
    
    if kunde_rechnung == "Manuelle Eingabe":
        finaler_name = ck1.text_input("Name eingeben (nur für diese Rechnung):")
    else:
        finaler_name = kunde_rechnung
        
    rabatt_wert = ck2.slider("Rabatt (%)", 0, 50, 0)

    # RECHNUNGS-VORSCHAU
    if st.session_state.rechnungs_posten:
        st.write("---")
        with st.container(border=True):
            cl, cr = st.columns([1,1])
            with cl:
                if os.path.exists("logo.png"): st.image("logo.png", width=150)
                else: st.write("### 🚜 LU-BETRIEB")
            with cr:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                st.write(f"**Kunde:** {finaler_name}")
            
            st.write("---")
            # Tabelle
            line = "| Beschreibung | Menge | Einzel | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
            netto_summe = 0
            for p in st.session_state.rechnungs_posten:
                line += f"| {p['name']} | {p['std']}h | {p['preis']:.2f}€ | {p['gesamt']:.2f}€ |\n"
                netto_summe += p['gesamt']
            st.markdown(line)
            
            total_betrag = netto_summe * (1 - rabatt_wert/100)
            st.write("---")
            st.subheader(f"Gesamtbetrag: {total_betrag:.2f} €")

        c_btn1, c_btn2 = st.columns(2)
        with c_btn1:
            if st.button("🖨️ Drucken / PDF"):
                st.write('<script>window.print();</script>', unsafe_allow_html=True)
        with c_btn2:
            if st.button("🗑️ Rechnung leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
