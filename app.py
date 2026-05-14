import streamlit as st
from datetime import date
import pandas as pd

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
    # --- SESSION STATE FÜR RECHNUNGSPOSTEN ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []

    bereich = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Mehrfach-Rechnung"])

    if bereich == "💰 Ernte & Felder":
        st.title("🚜 Ernte- & Feld-Manager")
        # (Dein bisheriger Code für Ernte/Kalk kann hier bleiben)
        st.info("Dieser Bereich ist unverändert.")

    elif bereich == "📋 Mehrfach-Rechnung":
        st.title("📄 Professionelle Rechnungsstellung")
        
        # --- EINGABE-BEREICH ---
        with st.expander("➕ Neuen Posten hinzufügen", expanded=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                neues_geraet = st.text_input("Maschine / Leistung", placeholder="z.B. Fendt 936 Vario")
            with col2:
                neue_stunden = st.number_input("Stunden", min_value=0.0, value=1.0, step=0.5)
            with col3:
                neuer_satz = st.number_input("Preis pro Stunde (€)", min_value=0.0, value=100.0)
            
            if st.button("Posten zur Rechnung hinzufügen"):
                if neues_geraet:
                    posten = {
                        "Beschreibung": neues_geraet,
                        "Menge": neue_stunden,
                        "Einzelpreis": neuer_satz,
                        "Gesamt": neue_stunden * neuer_satz
                    }
                    st.session_state.rechnungs_posten.append(posten)
                    st.success(f"'{neues_geraet}' hinzugefügt!")
                else:
                    st.error("Bitte einen Namen für die Maschine eingeben.")

        # --- KUNDENDATEN ---
        col_k1, col_k2 = st.columns(2)
        with col_k1:
            kunde = st.text_input("Empfänger (Name/Hof):", value="Hof Bergmann")
        with col_k2:
            rabatt_prozent = st.slider("Rabatt auf Gesamtsumme (%)", 0, 50, 0)

        # --- RECHNUNGS-VORSCHAU ---
        if st.session_state.rechnungs_posten:
            st.divider()
            
            # Container für das "schöne" Design
            with st.container(border=True):
                # Header mit Logo
                c_logo, c_info = st.columns([1, 2])
                with c_logo:
                    try:
                        st.image("logo.png", width=180)
                    except:
                        st.write("### [DEIN LOGO]")
                with c_info:
                    st.write(f"**Rechnungsdatum:** {date.today().strftime('%d.%m.%Y')}")
                    st.write(f"**Rechnungs-Nr:** LS-{date.today().strftime('%y%m')}-{len(st.session_state.rechnungs_posten)}")
                    st.write(f"**Empfänger:** {kunde}")

                st.write("---")
                
                # Tabelle erstellen
                df = pd.DataFrame(st.session_state.rechnungs_posten)
                st.table(df) # Schöne statische Tabelle

                # Berechnungen
                summe_netto = df["Gesamt"].sum()
                rabatt_euro = summe_netto * (rabatt_prozent / 100)
                endbetrag = summe_netto - rabatt_euro

                # Total-Bereich
                c_empty, c_total = st.columns([2, 1])
                with c_total:
                    st.write(f"Zwischensumme: {summe_netto:,.2f} €")
                    if rabatt_prozent > 0:
                        st.write(f"Rabatt ({rabatt_prozent}%): -{rabatt_euro:,.2f} €")
                    st.subheader(f"Gesamt: {endbetrag:,.2f} €")

            # Aktionen
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("❌ Liste leeren"):
                    st.session_state.rechnungs_posten = []
                    st.rerun()
            with col_b2:
                st.caption("Nutze 'Strg+P' zum Drucken/Speichern")
        else:
            st.info("Noch keine Posten auf der Rechnung. Füge oben eine Maschine hinzu.")
