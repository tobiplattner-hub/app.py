import streamlit as st
from datetime import date

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# 2. Login-Funktion
def check_password():
    def password_entered():
        if st.session_state["username"] == "LS25-Team" and st.session_state["password"] == "unser-hof-2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.title("🔐 LS25 Hof-Login")
        st.text_input("Benutzername", on_change=password_entered, key="username")
        st.text_input("Passwort", type="password", on_change=password_entered, key="password")
        return False
    return st.session_state.get("password_correct", False)

if check_password():
    # --- SESSION STATE FÜR DIE RECHNUNG ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []

    # Navigation
    bereich = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Mehrfach-Rechnung"])

    if bereich == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        st.info("Hier kannst du deine Silostände und Feldverbräuche berechnen.")
        # Platz für deinen Ernte-Code...

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
        rabatt = c2.slider("Rabatt (%)", 0, 50, 0)

        # Die Rechnungsvorschau
        if st.session_state.rechnungs_posten:
            st.divider()
            with st.container(border=True):
                # Header
                h1, h2 = st.columns([1, 1])
                try:
                    h1.image("logo.png", width=150)
                except:
                    h1.write("### [LOGO]")
                
                h2.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                h2.write(f"**Kunde:** {kunde}")
                
                st.write("---")
                
                # Tabelle manuell mit Markdown bauen
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
