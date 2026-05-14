import streamlit as st
from datetime import date
import os

# 1. Seiteneinstellungen & Druck-Design
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# CSS für den "Nur-Rechnung-Drucken" Effekt
st.markdown("""
    <style>
    @media print {
        /* Blendet alles aus außer den Bereich mit der ID 'print-area' */
        header, [data-testid="stSidebar"], .stButton, .stExpander, footer, .stTabs {
            display: none !important;
        }
        .main .block-container {
            padding-top: 0rem !important;
        }
        .print-only {
            display: block !important;
        }
    }
    .print-only { display: none; }
    </style>
    """, unsafe_allow_value=True)

# 2. Login-Funktion
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
            else:
                st.error("Unbekannter Benutzername.")
        return False
    return True

if check_user():
    # --- INITIALISIERUNG ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []
    
    # Grund-Preisliste falls noch nicht vorhanden
    if "preisliste" not in st.session_state:
        st.session_state.preisliste = {
            "Traktor (Mittel)": 120.0,
            "Traktor (Groß)": 160.0,
            "Mähdrescher": 280.0
        }

    menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "⚙️ Preisliste bearbeiten"])

    # --- BEREICH 1: ERNTE & FELDER (KALK ETC.) ---
    if menu == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        col1, col2 = st.columns(2)
        with col1:
            st.header("💰 Erlös-Rechner")
            frucht_daten = {"Weizen": 1100, "Gerste": 1000, "Raps": 2100, "Mais": 1050, "Sojabohnen": 3200}
            frucht = st.selectbox("Fruchtart:", list(frucht_daten.keys()))
            menge = st.number_input("Liter im Silo:", value=20000, step=1000)
            erloes = (menge / 1000) * frucht_daten[frucht]
            st.metric("Voraussichtlicher Erlös", f"{erloes:,.2f} €")
            
        with col2:
            st.header("🧪 Verbrauchs-Rechner")
            hektar = st.number_input("Feldgröße (Hektar):", value=1.0, step=0.1, min_value=0.1)
            st.write(f"💧 Dünger: **{int(hektar * 160)} L**")
            st.write(f"🌾 Saatgut: **{int(hektar * 150)} L**")
            st.warning(f"⚪ Kalk: **{int(hektar * 2000)} L**")

    # --- BEREICH 2: PREISLISTE BEARBEITEN (MANUELL HINZUFÜGEN) ---
    elif menu == "⚙️ Preisliste bearbeiten":
        st.title("⚙️ Maschinen-Verleih Preisliste")
        
        # Neue Maschine hinzufügen
        with st.expander("🆕 Neue Maschine zur Liste hinzufügen"):
            neuer_name = st.text_input("Name der Maschine:")
            neuer_preis = st.number_input("Stundensatz (€):", min_value=0.0, value=50.0)
            if st.button("Maschine speichern"):
                if neuer_name:
                    st.session_state.preisliste[neuer_name] = neuer_preis
                    st.success(f"{neuer_name} wurde zur Auswahl hinzugefügt!")
                    st.rerun()

        st.write("---")
        st.subheader("Bestehende Preise ändern")
        for geraet in list(st.session_state.preisliste.keys()):
            col_g, col_p, col_d = st.columns([3, 2, 1])
            with col_g: st.write(f"**{geraet}**")
            with col_p: 
                new_p = st.number_input("€/h", value=float(st.session_state.preisliste[geraet]), key=f"p_{geraet}")
                st.session_state.preisliste[geraet] = new_p
            with col_d:
                if st.button("🗑️", key=f"del_{geraet}"):
                    del st.session_state.preisliste[geraet]
                    st.rerun()

    # --- BEREICH 3: RECHNUNGS-ERSTELLER ---
    elif menu == "📋 Rechnungs-Ersteller":
        st.title("📄 Rechnungs-Erstellung")
        
        with st.container(border=True):
            st.subheader("➕ Posten hinzufügen")
            c_a, c_b, c_c = st.columns([2, 1, 1])
            with c_a:
                auswahl = st.selectbox("Gerät wählen:", options=list(st.session_state.preisliste.keys()))
            with c_b:
                std = st.number_input("Stunden:", min_value=0.0, value=1.0, step=0.5)
            with c_c:
                p_vorschlag = st.session_state.preisliste[auswahl]
                e_preis = st.number_input("Einzelpreis (€):", value=float(p_vorschlag))
            
            if st.button("Hinzufügen"):
                st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_preis, "gesamt": std * e_preis})
                st.rerun()

        kunde = st.text_input("Empfänger / Hof:", value="Hof Bergmann")
        rabatt = st.slider("Rabatt (%)", 0, 50, 0)

        if st.session_state.rechnungs_posten:
            st.info("💡 Klicke unten auf 'Rechnung drucken' und wähle 'Als PDF speichern'.")
            
            # --- DER RECHNUNGS-BLOCK (Was gedruckt wird) ---
            st.markdown('<div id="print-area">', unsafe_allow_html=True)
            with st.container(border=True):
                col_l, col_r = st.columns([1, 1])
                with col_l:
                    if os.path.exists("logo.png"):
                        st.image("logo.png", width=160)
                    else:
                        st.write("### 🚜 LU-BETRIEB")
                with col_r:
                    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                    st.write(f"**Kunde:** {kunde}")

                st.write("## RECHNUNG")
                st.write("---")
                
                tabelle = "| Beschreibung | Menge | Preis/h | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
                summe_n = 0
                for p in st.session_state.rechnungs_posten:
                    tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                    summe_n += p['gesamt']
                st.markdown(tabelle)
                
                abzug = summe_n * (rabatt / 100)
                total = summe_n - abzug
                
                st.write("---")
                e1, e2 = st.columns([2, 1])
                with e2:
                    st.write(f"Netto: {summe_n:.2f} €")
                    if rabatt > 0: st.write(f"Rabatt: -{abzug:.2f} €")
                    st.write(f"### Gesamt: {total:.2f} €")
            st.markdown('</div>', unsafe_allow_html=True)

            # --- AKTIONEN ---
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                # Dieser Button nutzt JavaScript, um den Druckdialog zu öffnen
                st.button("🖨️ Rechnung drucken / PDF", on_click=lambda: st.write('<script>window.print();</script>', unsafe_allow_html=True))
                st.caption("Alternativ: Strg + P drücken")
            with col_btn2:
                if st.button("🗑️ Rechnung leeren"):
                    st.session_state.rechnungs_posten = []
                    st.rerun()

    if st.sidebar.button("Abmelden"):
        st.session_state["user_correct"] = False
        st.rerun()
