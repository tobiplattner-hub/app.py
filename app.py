import streamlit as st
from datetime import date
import os

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

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
    # --- SESSION STATE FÜR RECHNUNG, PREISLISTE & ERNTE ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []
    
    if "preisliste" not in st.session_state:
        st.session_state.preisliste = {
            "Traktor (Mittel)": 120.0,
            "Traktor (Groß)": 160.0,
            "Mähdrescher": 280.0,
            "Häckseln": 320.0,
            "Grubbern": 85.0,
            "Säen": 95.0,
            "Düngen": 60.0,
            "Transportfahrt": 70.0,
            "Eigenes Gerät (Manuell)": 0.0
        }

    # Navigation in der Seitenleiste
    menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "⚙️ Preisliste bearbeiten"])

    # --- BEREICH 1: ERNTE & FELDER (DEIN ALTER CODE) ---
    if menu == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        
        # Frucht-Datenbank für den Ernte-Rechner
        frucht_daten = {"Weizen": 1100, "Gerste": 1000, "Raps": 2100, "Mais": 1050, "Sojabohnen": 3200, "Hafer": 1250}
        
        col1, col2 = st.columns(2)
        with col1:
            st.header("💰 Erlös-Rechner")
            frucht = st.selectbox("Fruchtart:", list(frucht_daten.keys()))
            menge = st.number_input("Liter im Silo:", value=20000, step=1000)
            standard_preis = frucht_daten[frucht]
            aktueller_preis = st.number_input("Preis pro 1000L (€):", value=standard_preis)
            
            erloes = (menge / 1000) * aktueller_preis
            st.metric("Voraussichtlicher Erlös", f"{erloes:,.2f} €")
            
        with col2:
            st.header("🧪 Verbrauchs-Rechner")
            hektar = st.number_input("Feldgröße (Hektar):", value=1.0, step=0.1, min_value=0.1)
            
            st.subheader("Bedarf:")
            st.write(f"💧 Dünger: **{int(hektar * 160)} L**")
            st.write(f"🌾 Saatgut: **{int(hektar * 150)} L**")
            st.write(f"⚪ Kalk: **{int(hektar * 2000)} L**")
            st.info("Werte basieren auf Standard-Verbrauch im LS25.")

    # --- BEREICH 2: PREISLISTE BEARBEITEN ---
    elif menu == "⚙️ Preisliste bearbeiten":
        st.title("⚙️ Maschinen-Preisliste")
        st.write("Ändere hier die Standard-Stundensätze für deine Rechnungen.")
        
        for geraet, preis in st.session_state.preisliste.items():
            new_price = st.number_input(f"Preis für {geraet} (€/h):", value=float(preis), key=f"edit_{geraet}")
            st.session_state.preisliste[geraet] = new_price
        st.success("Die Preise wurden für diese Sitzung übernommen.")

    # --- BEREICH 3: RECHNUNGS-ERSTELLER ---
    elif menu == "📋 Rechnungs-Ersteller":
        st.title("📄 Rechnungs-Erstellung")
        
        # Eingabe neuer Posten
        with st.container(border=True):
            st.subheader("➕ Neuen Posten hinzufügen")
            col_a, col_b, col_c = st.columns([2, 1, 1])
            
            with col_a:
                auswahl = st.selectbox("Gerät wählen:", options=list(st.session_state.preisliste.keys()))
                if auswahl == "Eigenes Gerät (Manuell)":
                    name_final = st.text_input("Bezeichnung:")
                else:
                    name_final = auswahl
            
            with col_b:
                std = st.number_input("Stunden:", min_value=0.0, value=1.0, step=0.5)
            
            with col_c:
                preis_vorschlag = st.session_state.preisliste[auswahl]
                e_preis = st.number_input("Preis (€/h):", value=float(preis_vorschlag))
            
            if st.button("Hinzufügen"):
                if name_final:
                    st.session_state.rechnungs_posten.append({
                        "name": name_final, "std": std, "preis": e_preis, "gesamt": std * e_preis
                    })
                    st.rerun()

        # Kundendaten & Rabatt
        st.subheader("👤 Empfänger & Rabatt")
        ck1, ck2 = st.columns(2)
        kunde = ck1.text_input("Kunde / Mitspieler:", value="Hof Bergmann")
        rabatt = ck2.slider("Rabatt auf Gesamtsumme (%)", 0, 50, 0)

        # DIE RECHNUNGSVORSCHAU (Layout-Box)
        if st.session_state.rechnungs_posten:
            st.write("---")
            with st.container(border=True):
                # Header mit Logo Check
                c_logo, c_info = st.columns([1, 1])
                with c_logo:
                    if os.path.exists("logo.png"):
                        st.image("logo.png", width=180)
                    else:
                        st.markdown("### 🚜 **LU-BETRIEB**")
                
                with c_info:
                    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                    st.write(f"**Empfänger:** {kunde}")

                st.write("## RECHNUNG")
                st.write("---")
                
                # Rechnungs-Tabelle
                tabelle = "| Beschreibung | Menge | Preis/h | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
                summe_netto = 0
                for p in st.session_state.rechnungs_posten:
                    tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                    summe_netto += p['gesamt']
                
                st.markdown(tabelle)
                
                # Berechnungen
                abzug = summe_netto * (rabatt / 100)
                total = summe_netto - abzug
                
                st.write("---")
                e1, e2 = st.columns([2, 1])
                with e2:
                    st.write(f"Zwischensumme: {summe_netto:.2f} €")
                    if rabatt > 0:
                        st.write(f"Rabatt ({rabatt}%): -{abzug:.2f} €")
                    st.write(f"### Gesamt: {total:.2f} €")
                
                st.caption("Erstellt mit dem LS25 Hof-Manager. Gut Schüttel!")

            if st.button("❌ Rechnung leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()

    # Logout in der Sidebar
    if st.sidebar.button("Abmelden"):
        st.session_state["user_correct"] = False
        st.rerun()
