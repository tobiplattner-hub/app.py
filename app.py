import streamlit as st
import pandas as pd
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- RADIKALES CSS FÜR PROFI-DRUCK (VERSTECKT ALLES AUSSER DIE RECHNUNG) ---
st.markdown("""
    <style>
    @media print {
        /* Alles auf der Hauptseite, Sidebar, Header und Buttons unsichtbar machen */
        html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"], 
        header, footer, .no-print, .stButton, [data-testid="stHeader"] {
            visibility: hidden !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Nur das Element mit unserer Rechnung absolut oben einblenden */
        iframe, .element-container {
            visibility: visible !important;
            position: absolute !important;
            left: 0 !important;
            top: 0 !important;
            width: 100% !important;
        }
        
        @page {
            size: A4;
            margin: 15mm;
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
    with st.expander("⚙️ Verbrauchs-Raten anpassen (pro Hektar)"):
        r_kalk = st.number_input("Kalk (L/ha):", value=2000)
        r_duenger = st.number_input("Dünger (L/ha):", value=160)
        r_saat = st.number_input("Saatgut (L/ha):", value=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.header("🧪 Bedarf")
        ha = st.number_input("Hektar:", value=1.0, step=0.1)
        st.write(f"⚪ Kalk: **{int(ha * r_kalk)} L**")
        st.write(f"💧 Dünger: **{int(ha * r_duenger)} L**")
        st.write(f"🌾 Saatgut: **{int(ha * r_saat)} L**")
    with col2:
        st.header("🌾 Erlös")
        m = st.number_input("Liter im Silo:", value=10000)
        p = st.number_input("€/1000L:", value=1200)
        st.metric("Erlös", f"{(m/1000)*p:,.2f} €")

# --- BEREICH: RECHNUNGS-ERSTELLER ---
elif menu == "📋 Rechnungs-Ersteller":
    st.markdown('<h1 class="no-print">📋 Rechnungs-Ersteller</h1>', unsafe_allow_html=True)
    
    # EINGABE-BEREICH (wird beim Drucken über CSS versteckt)
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

    # RECHNUNGS-BEREICH (DAS WIRD GERENDERED UND GEDRUCKT)
    if st.session_state.rechnungs_posten:
        st.write("---")
        
        # 1. Werte zuerst sauber in Python berechnen
        summe = 0
        tabellen_zeilen = ""
        for p in st.session_state.rechnungs_posten:
            tabellen_zeilen += f"""
            <tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; text-align: left;">{p['name']}</td>
                <td style="padding: 10px; text-align: left;">{p['std']} h</td>
                <td style="padding: 10px; text-align: left;">{p['preis']:.2f} €</td>
                <td style="padding: 10px; text-align: right;">{p['gesamt']:.2f} €</td>
            </tr>
            """
            summe += p['gesamt']
        
        total = summe * (1 - rabatt/100)
        
        rabatt_html = ""
        if rabatt > 0:
            rabatt_html = f"""
            <tr>
                <td colspan="3" style="text-align: right; padding: 5px; color: #555; font-family: sans-serif;">Rabatt ({rabatt}%):</td>
                <td style="text-align: right; padding: 5px; color: #555; font-family: sans-serif;">-{summe*(rabatt/100):.2f} €</td>
            </tr>
            """

        # 2. Die gesamte Rechnung als ein festes HTML-Paket schnüren
        komplette_rechnung_html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; background-color: white; }}
                .invoice-box {{ padding: 20px; border: 1px solid #333; border-radius: 6px; }}
                @media print {{
                    .invoice-box {{ border: none; padding: 0; }}
                    * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                }}
            </style>
        </head>
        <body>
            <div class="invoice-box">
                <!-- Header mit Logo/Name und Meta-Daten -->
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr>
                        <td style="text-align: left; vertical-align: middle;">
                            <h2 style="margin: 0; color: #222; font-size: 24px;">🚜 LU-BETRIEB</h2>
                        </td>
                        <td style="text-align: right; vertical-align: middle; font-size: 14px; color: #444; line-height: 1.5;">
                            <strong>Datum:</strong> {date.today().strftime('%d.%m.%Y')}<br>
                            <strong>Kunde:</strong> {k_name}
                        </td>
                    </tr>
                </table>
                
                <hr style="border: 0; border-top: 3px solid #111; margin: 10px 0;">
                <h1 style="margin: 10px 0; font-size: 32px; font-weight: bold; letter-spacing: 0.5px;">RECHNUNG</h1>
                <hr style="border: 0; border-top: 3px solid #111; margin: 10px 0;">
                
                <!-- Artikelliste -->
                <table style="width:100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px;">
                    <thead>
                        <tr style="border-bottom: 2px solid #111; background-color: #f2f2f2; font-weight: bold;">
                            <th style="padding: 12px 10px; text-align: left;">Leistung / Maschine</th>
                            <th style="padding: 12px 10px; text-align: left;">Menge</th>
                            <th style="padding: 12px 10px; text-align: left;">Einzelpreis</th>
                            <th style="padding: 12px 10px; text-align: right;">Gesamt</th>
                        </tr>
                    </thead>
                    <tbody>
                        {tabellen_zeilen}
                    </tbody>
                </table>
                
                <!-- Finanzieller Abschluss -->
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <tr>
                        <td style="width: 40%;"></td>
                        <td style="width: 60%;">
                            <table style="width: 100%; border-collapse: collapse;">
                                <tr>
                                    <td style="text-align: right; padding: 6px; font-size: 15px;">Zwischensumme:</td>
                                    <td style="text-align: right; padding: 6px; font-size: 15px; width: 120px;">{summe:.2f} €</td>
                                </tr>
                                {rabatt_html}
                                <tr style="font-size: 20px; font-weight: bold;">
                                    <td style="text-align: right; padding: 12px 6px; border-top: 2px solid #111;">Gesamtbetrag:</td>
                                    <td style="text-align: right; padding: 12px 6px; border-top: 2px solid #111; color: #000;">{total:.2f} €</td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        # 3. SICHERE GENERIERUNG ALS ECHTE WEB-KOMPONENTE
        # Verhindert, dass roher Text oder Code ausgegeben wird
        st.components.v1.html(komplette_rechnung_html, height=480, scrolling=True)

        # Aktionsbuttons unter der Rechnung (beim Drucken unsichtbar)
        st.markdown('<div class="no-print">', unsafe_allow_html=True)
        btn1, btn2 = st.columns(2)
        if btn1.button("🖨️ RECHNUNG DRUCKEN / PDF"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        if btn2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- BEREICH: KUNDEN-VERWALTUNG ---
elif menu == "👥 Kunden-Verwaltung":
    st.title("👥 Hof-Namen dauerhaft speichern")
    neuer_hof = st.text_input("Name des neuen Hofes:")
    if st.button("Hof im Google Sheet speichern"):
        if neuer_hof:
            try:
                from streamlit_gsheets import GSheetsConnection
                conn = st.connection("gsheets", type=GSheetsConnection)
                new_row = pd.DataFrame([{"Name": neuer_hof}])
                updated_df = pd.concat([df_kunden, new_row], ignore_index=True)
                conn.update(spreadsheet=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}", 
                            worksheet="Kunden", data=updated_df)
                st.success(f"Hof '{neuer_hof}' erfolgreich gespeichert!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Fehler beim Speichern: {e}")

if st.sidebar.button("Abmelden"):
    st.session_state["user_correct"] = False
    st.rerun()
