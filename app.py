import streamlit as st
import pandas as pd
from datetime import date
import os
import base64

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- FUNKTION: LOGO FÜR HTML VORBEREITEN ---
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- RADIKALES CSS FÜR PROFI-DRUCK (A4 OPTIMIERT) ---
st.markdown("""
    <style>
    @media print {
        /* Verstecke alles von Streamlit */
        [data-testid="stAppViewContainer"], [data-testid="stSidebar"], 
        header, footer, .no-print, .stButton, [data-testid="stHeader"] {
            display: none !important;
        }

        /* Zeige nur den iframeinhalt (die Rechnung) */
        iframe {
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
            width: 100% !important;
            height: 100vh !important;
            border: none !important;
        }
        
        @page {
            size: A4;
            margin: 0; /* Wir steuern das Padding im HTML */
        }
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Google Sheet Daten Verbindung
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
    except:
        return pd.DataFrame()

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
    st.stop()

# --- DATEN LADEN ---
df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state:
    st.session_state.rechnungs_posten = []

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "👥 Kunden-Verwaltung"])

# --- BEREICH: ERNTE ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    # ... (Ernte Bereich bleibt gleich) ...
    ha = st.number_input("Hektar:", value=1.0, step=0.1)
    st.write(f"Bedarf berechnet für {ha} ha.")

# --- BEREICH: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    st.markdown('<h1 class="no-print">📋 Rechnungs-Ersteller</h1>', unsafe_allow_html=True)
    
    st.markdown('<div class="no-print">', unsafe_allow_html=True)
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine auswählen:", options=list(preis_dict.keys()) if preis_dict else ["Keine Daten"])
        std = c2.number_input("Stunden (h):", min_value=0.0, value=1.0, step=0.1)
        e_p = c3.number_input("Preis (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
        
        if st.button("➕ Posten hinzufügen"):
            if std > 0:
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
                st.rerun()

    ck1, ck2 = st.columns(2)
    k_wahl = ck1.selectbox("Hof auswählen:", options=["-- Bitte wählen --"] + aktuelle_kunden + ["Manuelle Eingabe"])
    k_name = ck1.text_input("Hof-Name manuell:") if k_wahl == "Manuelle Eingabe" else k_wahl
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.rechnungs_posten:
        st.write("---")
        
        # Logo vorbereiten
        logo_base64 = get_base64_image("logo.png")
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="width:180px;">' if logo_base64 else '<h2 style="margin:0;">🚜 LU-BETRIEB</h2>'

        # Tabellen-Zeilen
        summe = 0
        tabellen_zeilen = ""
        for p in st.session_state.rechnungs_posten:
            tabellen_zeilen += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px 0;">{p['name']}</td>
                <td style="padding: 12px 0;">{p['std']} h</td>
                <td style="padding: 12px 0;">{p['preis']:.2f} €</td>
                <td style="padding: 12px 0; text-align: right;">{p['gesamt']:.2f} €</td>
            </tr>
            """
            summe += p['gesamt']
        
        total = summe * (1 - rabatt/100)
        
        # KOMPLETTES A4 RECHNUNGS-HTML
        komplette_rechnung_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Helvetica', sans-serif; color: #333; margin: 0; padding: 0; background-color: #fff; }}
                .page {{ width: 210mm; min-height: 297mm; padding: 20mm; margin: auto; box-sizing: border-box; }}
                .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 50px; }}
                .info-table {{ width: 100%; font-size: 14px; margin-bottom: 40px; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                .items-table th {{ border-bottom: 2px solid #000; text-align: left; padding: 10px 0; font-size: 14px; text-transform: uppercase; }}
                .totals {{ width: 100%; display: flex; justify-content: flex-end; }}
                .totals-table {{ width: 300px; border-collapse: collapse; }}
                .totals-table td {{ padding: 8px 0; }}
                .grand-total {{ font-size: 20px; font-weight: bold; border-top: 2px solid #000; }}
                @media print {{
                    body {{ padding: 0; }}
                    .page {{ padding: 15mm; border: none; width: 100%; min-height: auto; }}
                }}
            </style>
        </head>
        <body>
            <div class="page">
                <div class="header">
                    <div>{logo_html}</div>
                    <div style="text-align: right; line-height: 1.6;">
                        <strong>Rechnung Nr:</strong> #{date.today().strftime('%Y%m%d')}-01<br>
                        <strong>Datum:</strong> {date.today().strftime('%d.%m.%Y')}
                    </div>
                </div>

                <div style="margin-bottom: 50px;">
                    <span style="font-size: 12px; color: #777; text-transform: uppercase;">Empfänger</span><br>
                    <strong style="font-size: 18px;">{k_name}</strong>
                </div>

                <h1 style="font-size: 36px; margin-bottom: 30px; font-weight: 300;">RECHNUNG</h1>

                <table class="items-table">
                    <thead>
                        <tr>
                            <th>Leistung</th>
                            <th>Menge</th>
                            <th>Einzel</th>
                            <th style="text-align: right;">Gesamt</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tabellen_zeilen}
                    </tbody>
                </table>

                <div class="totals">
                    <table class="totals-table">
                        <tr>
                            <td>Zwischensumme</td>
                            <td style="text-align: right;">{summe:.2f} €</td>
                        </tr>
                        {f'<tr><td>Rabatt {rabatt}%</td><td style="text-align: right;">-{summe*(rabatt/100):.2f} €</td></tr>' if rabatt > 0 else ''}
                        <tr class="grand-total">
                            <td style="padding-top: 15px;">GESAMT</td>
                            <td style="text-align: right; padding-top: 15px;">{total:.2f} €</td>
                        </tr>
                    </table>
                </div>
                
                <div style="margin-top: 100px; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 20px;">
                    Vielen Dank für Ihren Auftrag! Der Betrag ist innerhalb von 14 Tagen zu begleichen.
                </div>
            </div>
        </body>
        </html>
        """
        
        # Anzeige im Browser (Höhe ist hier für die Vorschau)
        st.components.v1.html(komplette_rechnung_html, height=800, scrolling=True)

        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        if b1.button("🖨️ PDF DRUCKEN"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        if b2.button("🗑️ NEUE RECHNUNG"):
            st.session_state.rechnungs_posten = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- BEREICH: KUNDEN-VERWALTUNG ---
elif menu == "👥 Kunden-Verwaltung":
    # ... (Bleibt gleich) ...
    st.title("Kundenverwaltung")
