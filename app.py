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
    # --- SESSION STATE FÜR DIE RECHNUNG & PREISLISTE ---
    if "rechnungs_posten" not in st.session_state:
        st.session_state.rechnungs_posten = []
    
    # Hier kannst du deine Standard-Preisliste definieren
    if "preisliste" not in st.session_state:
        st.session_state.preisliste = {
            "Fendt 936 Vario": 150.0,
            "John Deere 8R": 160.0,
            "Claas Lexion": 250.0,
            "Grubbern": 80.0,
            "Säen": 90.0,
            "Transportfahrt": 60.0,
            "Eigenes Gerät (Manuell)": 0.0
        }

    # Navigation
    menu = st.sidebar.selectbox("Navigation", ["📋 Rechnungs-Ersteller", "⚙️ Preisliste bearbeiten", "💰 Ernte & Felder"])

    # --- BEREICH: PREISLISTE BEARBEITEN ---
    if menu == "⚙️ Preisliste bearbeiten":
        st.title("⚙️ Preisliste anpassen")
        st.write("Hier kannst du die Preise für deine Geräte hinterlegen.")
        
        for geraet, preis in st.session_state.preisliste.items():
            new_price = st.number_input(f"Preis für {geraet} (€/h):", value=float(preis), key=f"edit_{geraet}")
            st.session_state.preisliste[geraet] = new_price
        st.success("Preise wurden für diese Sitzung gespeichert!")

    # --- BEREICH: RECHNUNG ---
    elif menu == "📋 Rechnungs-Ersteller":
        st.title("📄 Rechnungs-Erstellung")
        
        # Eingabe-Bereich
        with st.container(border=True):
            st.subheader("➕ Posten hinzufügen")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                auswahl = st.selectbox("Gerät/Leistung wählen:", options=list(st.session_state.preisliste.keys()))
                # Falls manuelles Gerät, Name überschreiben erlauben
                if auswahl == "Eigenes Gerät (Manuell)":
                    name_final = st.text_input("Name der Leistung:")
                else:
                    name_final = auswahl
            
            with col2:
                std = st.number_input("Stunden:", min_value=0.0, value=1.0, step=0.5)
            
            with col3:
                # Holt den Preis aus der Preisliste
                standard_preis = st.session_state.preisliste[auswahl]
                einzelpreis = st.number_input("Preis (€/h):", value=float(standard_preis))
            
            if st.button("Hinzufügen"):
                st.session_state.rechnungs_posten.append({
                    "name": name_final, "std": std, "preis": einzelpreis, "gesamt": std * einzelpreis
                })
                st.rerun()

        # Kundendaten
        st.subheader("👤 Empfänger Details")
        c1, c2 = st.columns(2)
        kunde = c1.text_input("Kunde/Hof:", value="Hof Name")
        rabatt = c2.slider("Rabatt (%)", 0, 50, 0)

        # RECHNUNGS-LAYOUT (Kompakt)
        if st.session_state.rechnungs_posten:
            st.write("---")
            
            # Dieser Container simuliert das PDF-Blatt (Zentriert und Weiß)
            rechnungs_container = st.container(border=True)
            with rechnungs_container:
                # Kopfzeile
                col_logo, col_info = st.columns([1, 1])
                
                with col_logo:
                    if os.path.exists("logo.png"):
                        st.image("logo.png", width=150)
                    else:
                        st.markdown("### **MEIN HOF**\n*Lohnunternehmen*")
                
                with col_info:
                    st.write(f"**Datum:** {date.today().strftime('%d.%m.%Y')}")
                    st.write(f"**Kunde:** {kunde}")

                st.write("## RECHNUNG")
                st.write("---")
                
                # Tabelle
                tabelle = "| Beschreibung | Menge | Preis/h | Gesamt |\n| :--- | :--- | :--- | :--- |\n"
                summe_netto = 0
                for p in st.session_state.rechnungs_posten:
                    tabelle += f"| {p['name']} | {p['std']} h | {p['preis']:.2f} € | {p['gesamt']:.2f} € |\n"
                    summe_netto += p['gesamt']
                
                st.markdown(tabelle)
                
                # Fußzeile mit Summen
                abzug = summe_netto * (rabatt / 100)
                total = summe_netto - abzug
                
                st.write("---")
                e1, e2 = st.columns([2, 1])
                with e2:
                    st.write(f"Zwischensumme: **{summe_netto:.2f} €**")
                    if rabatt > 0:
                        st.write(f"Rabatt ({rabatt}%): -{abzug:.2f} €")
                    st.write(f"### Gesamt: {total:.2f} €")
                
                st.caption("Zahlbar innerhalb von 14 Tagen ohne Abzug.")

            if st.button("❌ Liste leeren"):
                st.session_state.rechnungs_posten = []
                st.rerun()
                
    elif menu == "💰 Ernte & Felder":
        st.title("💰 Ernte & Felder")
        # Hier dein alter Ernte/Feld Code (gekürzt für die Übersicht)
        st.write("Berechne hier deine Silostände.")
