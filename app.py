import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- CSS FÜR PROFI-DRUCK (DIN A4 Optimierung) ---
st.markdown("""
    <style>
    /* Verstecke alles Standardmäßige beim Drucken */
    @media print {
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer, .no-print, .stMarkdownContainer:not(.print-content) { 
            display: none !important; 
        }
        /* Nur den Bereich mit der Klasse 'print-content' anzeigen */
        .print-content {
            display: block !important;
            width: 100%;
            border: none !important;
        }
        .main .block-container { 
            padding: 0 !important; 
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Verbindung
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
KUNDEN_GID = "568043650"
PREIS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
KUNDEN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={KUNDEN_GID}"

@st.cache_data(ttl=5)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

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
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "👥 Kunden-Verwaltung"])

# --- BEREICH: ERNTE & FELDER (Mit anpassbaren Raten) ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    
    with st.expander("⚙️ Verbrauchs-Raten anpassen (pro Hektar)"):
        rate_kalk = st.number_input("Kalk Rate (L/ha):", value=2000)
        rate_duenger = st.number_input("Dünger Rate (L/ha):", value=160)
        rate_saat = st.number_input("Saatgut Rate (L/ha):", value=150)

    col1, col2 = st.columns(2)
    with col1:
        st.header("🧪 Bedarf")
        ha = st.number_input("Hektar:", value=1.0, step=0.1)
        st.write(f"⚪ Kalk: **{int(ha * rate_kalk)} L**")
        st.write(f"💧 Dünger: **{int(ha * rate_duenger)} L**")
        st.write(f"🌾 Saatgut: **{int(ha * rate_saat)} L**")
    with col2:
        st.header("🌾 Erlös")
        m = st.number_input("Liter im Silo:", value=10000)
        p = st.number_input("€/1000L:", value=1200)
        st.metric("Erlös", f"{(m/1000)*p:,.2f} €")

# --- BEREICH: RECHNUNGS-ERSTELLER (Optimierter Druck) ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📄 Rechnungs-Ersteller")
    
    # Arbeitsbereich (no-print)
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()))
        std = c2.number_input("Stunden:", min_value=0.0, value=1.0, step=0.1)
        e_p = c3.number_input("€/h:", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("Hinzufügen"):
            if std > 0:
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
                st.rerun()

    ck1, ck2 = st.columns(2)
    k_wahl = ck1.selectbox("Hof auswählen:", options=["-- Bitte wählen --"] + aktuelle_kunden + ["Manuelle Eingabe"])
    k_name = ck1.text_input("Falls manuell:") if k_wahl == "Manuelle Eingabe" else k_wahl
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)
    st.markdown('</div>', unsafe_allow_html=True)

    # RECHNUNGS-BEREICH (Das wird gedruckt)
    if st.session_state.rechnungs_posten:
        st.write("---")
        # Wir wickeln die Rechnung in eine spezielle CSS-Klasse ein
        rechnungs_container = st.container()
        with rechnungs_container:
            st.markdown('<div class="print-content">', unsafe_allow_html=True)
            with st.container(border=True):
                cl, cr = st.columns([1,1])
                with cl:
                    if os.path.exists("logo.png"): st.image("logo.png", width=150)
                    else: st.write("### 🚜 LU-BETRIEB")
                with cr:
                    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                    st.write(f"**Kunde:** {k_name}")
                
                st.write("---")
                st.write("### RECHNUNG")
                tabelle = "| Beschreibung | Menge | Einzel | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
                summe = 0
                for p in st.session_state.rechnungs_posten:
                    tabelle += f"| {p['name']} | {p['std']}h | {p['preis']:.2f}€ | {p['gesamt']:.2f}€ |\n"
                    summe += p['gesamt']
                st.markdown(tabelle)
                
                total = summe * (1 - rabatt/100)
                st.write("---")
                e1, e2 = st.columns([2, 1])
                with e2:
                    st.write(f"Zwischensumme: {summe:.2f} €")
                    if rabatt > 0: st.write(f"Rabatt: -{summe*(rabatt/100):.2f} €")
                    st.subheader(f"Gesamt: {total:.2f} €")
            st.markdown('</div>', unsafe_allow_html=True)

        # Druck-Buttons (no-print)
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        cp1, cp2 = st.columns(2)
        with cp1:
            if st.button("🖨️ Jetzt Drucken / PDF speichern"):
                st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        with cp2:
            if st.button("🗑️ Rechnung leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- BEREICH: KUNDEN-VERWALTUNG ---
elif menu == "👥 Kunden-Verwaltung":
    st.title("👥 Hof-Namen speichern")
    neuer_hof = st.text_input("Neuer Hof-Name:")
    if st.button("Dauerhaft speichern"):
        if neuer_hof:
            try:
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                new_row = pd.DataFrame([{"Name": neuer_hof}])
                updated_df = pd.concat([df_kunden, new_row], ignore_index=True)
                conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}", worksheet="Kunden", data=updated_df)
                st.success(f"'{neuer_hof}' gespeichert!")
                st.cache_data.clear()
            except Exception as e: st.error(f"Fehler: {e}")

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
