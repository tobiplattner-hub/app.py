import streamlit as st
from datetime import date

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# 2. Login-Funktion (NUR MIT BENUTZERNAME)
def check_user():
    if "user_correct" not in st.session_state:
        st.session_state["user_correct"] = False

    if not st.session_state["user_correct"]:
        st.title("🔐 LS25 Hof-Login")
        # Hier den Benutzernamen abfragen
        username = st.text_input("Bitte Benutzernamen eingeben:", key="login_name")
        
        if st.button("Einloggen"):
            # HIER kannst du den erlaubten Namen ändern
            if username == "LS25-Team": 
                st.session_state["user_correct"] = True
                st.rerun()
            else:
                st.error("Unbekannter Benutzername.")
        return False
    return True

# 3. Hauptprogramm
if check_user():
    # --- SESSION STATE FÜR DIE RECHNUNG ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []

    # Navigation in der Seitenleiste
    bereich = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Mehrfach-Rechnung"])
    
    # Logout-Button ganz unten in der Sidebar
    if st.sidebar.button("Abmelden"):
        st.session_state["user_correct"] = False
        st.rerun()

    # --- BEREICH: ERNTE & FELDER ---
    if bereich == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        
        col_ernte, col_feld = st.columns(2)
        
        with col_ernte:
            st.header("Erlös-Rechner")
            menge = st.number_input("Liter im Silo:", value=10000, step=1000)
            preis_pro_1000 = st.number_input("Preis pro 1.000L (€):", value=1200)
            erloes = (menge / 1000) * preis_pro_1000
            st.metric("Dein Erlös", f"{erloes:,.2f} €")

        with col_feld:
            st.header("Verbrauchs-Rechner")
            hektar = st.number_input("Feldgröße in Hektar:", value=1.0, step=0.1)
            st.write(f"🧪 Düngerbedarf: **{int(hektar * 160)} L**")
            st.write(f"🌾 Saatgutbedarf: **{int(hektar * 150)} L**")
            st.warning(f"⚪ Kalkbedarf: **{int(hektar * 2000)} L**")

    # --- BEREICH: MEHRFACH-RECHNUNG ---
    elif bereich == "📋 Mehrfach-Rechnung":
        st.title("📄 Rechnungs-Ersteller")
        
        # Eingabe neuer Posten
        with st.expander("➕ Maschine/Leistung hinzufügen", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                name = st.text_input("Was wurde gemacht?", placeholder="z.B. Grubbern Feld 12")
            with col2:
                std = st.number_input("Stunden", min_value=0.0, value=1.0, step=0.5)
            with col3:
                preis = st.number_input("Preis pro h (€)", min_value=0.0, value=100.0)
            
            if st.button("Hinzufügen"):
                if name:
                    st.session_state.rechnungs_posten.append({
                        "name": name, "std": std, "preis": preis, "gesamt": std * preis
                    })
                    st.rerun()

        # Kundendaten & Rabatt
        c1, c2 = st.columns(2)
        kunde = c1.text_input("Empfänger:", value="Hof Name")
        rabatt = c2.slider("Rabatt auf Gesamtsumme (%)", 0, 50, 0)

        # Die Rechnungsvorschau
        if st.session_state.rechnungs_posten:
            st.divider()
            with st.container(border=True):
                # Header mit Logo
                h1, h2 = st.columns([1, 1])
                try:
                    h1.image("logo.png", width=150)
                except:
                    h1.write("### [LOGO]")
                
                h2.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                h2.write(f"**Kunde:** {kunde}")
                
                st.write("---")
                
                # Tabelle manuell bauen
                tabelle = "| Beschreibung | Menge | Preis/h | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
                summe_netto = 0
                for p in st.session_state.rechnungs_posten:
                    tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                    summe_netto += p['gesamt']
                
                st.markdown(tabelle)
                
                # Berechnung Finale
                abzug = summe_netto * (rabatt / 100)
                total = summe_netto - abzug
                
                st.write("---")
                e1, e2 = st.columns([2, 1])
                with e2:
                    st.write(f"Zwischensumme: {summe_netto:.2f} €")
                    if rabatt > 0:
                        st.write(f"Rabatt ({rabatt}%): -{abzug:.2f} €")
                    st.subheader(f"Gesamt: {total:.2f} €")

            if st.button("❌ Liste leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()
