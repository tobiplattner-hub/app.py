import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- DER ULTIMATIVE DRUCK-FIX (RADIKAL) ---
st.markdown("""
    <style>
    /* NORMALE ANSICHT IM BROWSER */
    .only-print { display: none; }

    @media print {
        /* 1. ALLES auf der Seite komplett ausblenden */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], 
        header, footer, .no-print, .stButton, [data-testid="stHeader"] {
            visibility: hidden !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* 2. NUR den Rechnungs-Container wieder einblenden */
        .print-content {
            visibility: visible !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
            display: block !important;
            background-color: white !important;
        }

        /* 3. Text-Korrekturen für den Druck */
        .print-content h3, .print-content p, .print-content span, .print-content td, .print-content th {
            color: black !important;
            visibility: visible !important;
        }

        /* 4. A4 Einstellungen */
        @page {
            size: A4;
            margin: 20mm;
        }
        
        /* Grafiken erzwingen */
        * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Daten (ID & GID)
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

# --- BEREICH: ERNTE ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    with st.expander("⚙️ Raten anpassen"):
        r_kalk = st.number_input("Kalk (L/ha):", value=2000)
        r_duenger = st.number_input("Dünger (L/ha):", value=160)
        r_saat = st.number_input("Saatgut (L/ha):", value=150)
    ha = st.number_input("Hektar:", value=1.0, step=0.1)
    st.write(f"⚪ Kalk: **{int(ha * r_kalk)} L** | 💧 Dünger: **{int(ha * r_duenger)} L** | 🌾 Saat: **{int(ha * r_saat)} L**")

# --- BEREICH: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    # Diese Überschrift ist NUR im Browser sichtbar, verschwindet beim Drucken
    st.markdown('<h1 class="no-print">📋 Rechnungs-Ersteller</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()))
        std = c2.number_input("Stunden:", min_value=0.0, value=1.0, step=0.1)
        e_p = c3.number_input("€/h:", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("➕ Posten hinzufügen"):
            if std > 0:
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
                st.rerun()

    ck1, ck2 = st.columns(2)
    k_wahl = ck1.selectbox("Hof auswählen:", options=["-- Bitte wählen --"] + aktuelle_kunden + ["Manuelle Eingabe"])
    k_name = ck1.text_input("Name:") if k_wahl == "Manuelle Eingabe" else k_wahl
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)
    st.markdown('</div>', unsafe_allow_html=True)

    # DER RECHNUNGS-BLOCK (DRUCK-RELEVANT)
    if st.session_state.rechnungs_posten:
        st.markdown('<div class="print-content">', unsafe_allow_html=True)
        
        # Innerer Rahmen der Rechnung
        with st.container(border=True):
            col_logo_l, col_logo_r = st.columns([1,1])
            with col_logo_l:
                if os.path.exists("logo.png"):
                    st.image("logo.png", width=180)
                else:
                    st.write("## 🚜 LU-BETRIEB")
            with col_logo_r:
                st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                st.write(f"**Kunde:** {k_name}")
            
            st.write("---")
            st.write("# RECHNUNG")
            st.write("---")
            
            # Tabelle manuell in HTML für maximale Druckkontrolle
            html_table = """
            <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                <thead>
                    <tr style="border-bottom: 2px solid black; text-align: left;">
                        <th style="padding: 8px;">Posten</th>
                        <th style="padding: 8px;">Menge</th>
                        <th style="padding: 8px;">Einzelpreis</th>
                        <th style="padding: 8px; text-align: right;">Gesamt</th>
                    </tr>
                </thead>
                <tbody>
            """
            summe = 0
            for p in st.session_state.rechnungs_posten:
                html_table += f"""
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 8px;">{p['name']}</td>
                    <td style="padding: 8px;">{p['std']} h</td>
                    <td style="padding: 8px;">{p['preis']:.2f} €</td>
                    <td style="padding: 8px; text-align: right;">{p['gesamt']:.2f} €</td>
                </tr>
                """
                summe += p['gesamt']
            
            total = summe * (1 - rabatt/100)
            html_table += "</tbody></table>"
            st.markdown(html_table, unsafe_allow_html=True)
            
            st.write("---")
            col_f1, col_f2 = st.columns([2, 1])
            with col_f2:
                st.write(f"Zwischensumme: {summe:.2f} €")
                if rabatt > 0:
                    st.write(f"Rabatt ({rabatt}%): -{summe*(rabatt/100):.2f} €")
                st.write(f"## **Gesamt: {total:.2f} €**")
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Buttons (no-print)
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("🖨️ RECHNUNG DRUCKEN (PDF)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        if btn_c2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- BEREICH: KUNDEN ---
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
