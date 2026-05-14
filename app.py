import streamlit as st

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager")

# 2. Login-Funktion
def check_password():
    """Gibt True zurück, wenn der Benutzer das richtige Passwort eingegeben hat."""
    def password_entered():
        # HIER kannst du Benutzername und Passwort ändern
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
    elif not st.session_state["password_correct"]:
        st.title("🔐 LS25 Hof-Login")
        st.text_input("Benutzername", on_change=password_entered, key="username")
        st.text_input("Passwort", type="password", on_change=password_entered, key="password")
        st.error("😕 Benutzername oder Passwort falsch.")
        return False
    else:
        return True

# 3. Hauptprogramm (wird nur ausgeführt, wenn Login korrekt)
if check_password():
    st.balloons() # Kleiner Effekt beim erfolgreichen Login
    st.success("Willkommen zurück auf dem Hof!")
    st.title("🚜 Mein ultimativer LS25 Hof-Manager")

    # Datenbank für Preise
    frucht_datenbank = {
        "Weizen": 1100, "Gerste": 1000, "Hafer": 1200, "Raps": 2100,
        "Sonnenblumen": 1900, "Sojabohnen": 3200, "Mais": 1050, 
        "Kartoffeln": 350, "Zuckerrüben": 280, "Reis": 1500,
        "Langkornreis": 1700
    }

    spalte_links, spalte_rechts = st.columns(2)

    with spalte_links:
        st.header("💰 Ernte- & Preisrechner")
        ausgewaehlte_frucht = st.selectbox("Fruchtsorte auswählen:", options=list(frucht_datenbank.keys()))
        standard_preis = frucht_datenbank[ausgewaehlte_frucht]
        
        menge = st.number_input("Menge im Silo (Liter):", min_value=0, value=25000, step=1000)
        aktueller_preis = st.number_input(f"Preis für {ausgewaehlte_frucht} (pro 1.000L):", min_value=0, value=standard_preis)
        
        gesamterloes = (menge / 1000) * aktueller_preis
        st.metric(label=f"Erlös für {ausgewaehlte_frucht}", value=f"{gesamterloes:,.2f} €")

    with spalte_rechts:
        st.header("🌱 Feld- & Verbrauchsrechner")
        feld_groesse = st.number_input("Feldgröße in Hektar (händisch):", min_value=0.0, value=2.5, step=0.1, format="%.2f")
        
        st.write("---")
        # Berechnung Verbrauch
        duenger = feld_groesse * 160
        saatgut = feld_groesse * 150
        kalk = feld_groesse * 2000
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.info(f"🧪 Dünger:\n**{int(duenger)} L**")
        with c2:
            st.info(f"🌾 Saatgut:\n**{int(saatgut)} L**")
        with c3:
            st.warning(f"⚪ Kalk:\n**{int(kalk)} L**")

    st.divider()
    if st.button("Abmelden"):
        st.session_state["password_correct"] = False
        st.rerun()
