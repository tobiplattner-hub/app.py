import streamlit as st
from datetime import date

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager")

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
    elif not st.session_state["password_correct"]:
        st.title("🔐 LS25 Hof-Login")
        st.text_input("Benutzername", on_change=password_entered, key="username")
        st.text_input("Passwort", type="password", on_change=password_entered, key="password")
        st.error("😕 Login falsch.")
        return False
    return True

# 3. Hauptprogramm
if check_password():
    # Menü in der Seitenleiste
    bereich = st.sidebar.radio("Bereich wählen:", ["💰 Ernte & Felder", "📋 Maschinen-Rechnung"])

    if bereich == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        
        # Frucht-Datenbank
        frucht_daten = {"Weizen": 1100, "Gerste": 1000, "Raps": 2100, "Mais": 1050, "Sojabohnen": 3200}
        
        col1, col2 = st.columns(2)
        with col1:
            st.header("Erlös-Rechner")
            frucht = st.selectbox("Frucht:", list(frucht_daten.keys()))
            menge = st.number_input("Liter im Silo:", value=20000, step=1000)
            preis = st.number_input("Preis pro 1000L:", value=frucht_daten[frucht])
            st.metric("Voraussichtlicher Erlös", f"{(menge/1000)*preis:,.2f} €")
            
        with col2:
            st.header("Verbrauchs-Rechner")
            hektar = st.number_input("Feldgröße (Hektar):", value=1.0, step=0.1)
            st.write(f"🧪 Dünger: **{int(hektar * 160)} L**")
            st.write(f"🌾 Saatgut: **{int(hektar * 150)} L**")
            st.warning(f"⚪ Kalkbedarf: **{int(hektar * 2000)} L**")

    elif bereich == "📋 Maschinen-Rechnung":
        st.title("📄 Rechnungs-Erstellung")
        
        col_a, col_b = st.columns(2)
        with col_a:
            kunde = st.text_input("Kunde / Mitspieler:", value="Hof Bergmann")
            geraet = st.text_input("Maschine:", value="Fendt 936 Vario")
            datum = st.date_input("Datum:", date.today())
            
        with col_b:
            stunden = st.number_input("Stunden:", min_value=0.0, value=1.0, step=0.5)
            satz = st.number_input("Preis pro Stunde (€):", min_value=0.0, value=150.0)
            rabatt = st.slider("Rabatt (%)", 0, 50, 0)

        # Berechnung
        brutto = stunden * satz
        abzug = brutto * (rabatt / 100)
        netto = brutto - abzug

        st.divider()

        # DIE RECHNUNGSVORSCHAU
        try:
            st.image("logo.png", width=250)
        except:
            st.info("💡 Lade ein Bild namens 'logo.png' bei GitHub hoch, um dein Logo hier zu sehen.")

        st.markdown(f"""
        ### RECHNUNG
        **Datum:** {datum} | **Nr:** {date.today().strftime('%Y%m')}-001
        
        **Empfänger:** {kunde}
        
        | Beschreibung | Menge | Einzelpreis | Gesamt |
        | :--- | :--- | :--- | :--- |
        | {geraet} | {stunden} h | {satz:.2f} € | {brutto:.2f} € |
        | **Rabatt** | | | **-{abzug:.2f} €** |
        | **SUMME** | | | **{netto:.2f} €** |
        
        ---
        *Vielen Dank für den Auftrag!*
        """)
        
        st.caption("Tipp: Drücke Strg+P zum Drucken oder Speichern als PDF.")
