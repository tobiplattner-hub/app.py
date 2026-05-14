import streamlit as st

# Layout auf "Weit" stellen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager")

st.title("🚜 Mein ultimativer LS25 Hof-Manager")

# Datenbank für Standardpreise (pro 1000L)
frucht_datenbank = {
    "Weizen": 1100, "Gerste": 1000, "Hafer": 1200, "Raps": 2100,
    "Sonnenblumen": 1900, "Sojabohnen": 3200, "Mais": 1050, 
    "Kartoffeln": 350, "Zuckerrüben": 280, "Reis": 1500,
    "Langkornreis": 1700
}

# Spalten-Layout
spalte_links, spalte_rechts = st.columns(2)

with spalte_links:
    st.header("💰 Ernte- & Preisrechner")
    
    ausgewaehlte_frucht = st.selectbox("Fruchtsorte auswählen:", options=list(frucht_datenbank.keys()))
    standard_preis = frucht_datenbank[ausgewaehlte_frucht]
    
    # Händische Eingabe der Liter
    menge = st.number_input("Menge im Silo / Anhänger (in Litern):", min_value=0, value=25000, step=1000)
    aktueller_preis = st.number_input(f"Aktueller Preis für {ausgewaehlte_frucht} (pro 1.000L):", min_value=0, value=standard_preis)
    
    # Berechnung Erlös
    gesamterloes = (menge / 1000) * aktueller_preis
    st.metric(label=f"Voraussichtlicher Erlös ({ausgewaehlte_frucht})", value=f"{gesamterloes:,.2f} €")

with spalte_rechts:
    st.header("🌱 Feld- & Verbrauchsrechner")
    
    # HÄNDISCHE EINGABE FÜR HEKTAR
    feld_groesse = st.number_input(
        "Wie groß ist dein Feld? (Hektar eingeben):", 
        min_value=0.0, 
        value=2.5, 
        step=0.1,
        format="%.2f" # Erlaubt zwei Nachkommastellen
    )
    
    st.write("---")
    st.subheader("Bedarf für dieses Feld:")
    
    # Durchschnittliche LS-Verbrauchswerte pro Hektar
    duenger_bedarf = feld_groesse * 160   # ca. 160L pro Hektar
    saatgut_bedarf = feld_groesse * 150   # ca. 150L pro Hektar
    kalk_bedarf = feld_groesse * 2000     # ca. 2000L pro Hektar (Kalk ist schwer!)
    
    # Anzeige in drei Boxen
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info(f"🧪 Dünger:\n**{int(duenger_bedarf)} L**")
    with c2:
        st.info(f"🌾 Saatgut:\n**{int(saatgut_bedarf)} L**")
    with c3:
        st.warning(f"⚪ Kalk:\n**{int(kalk_bedarf)} L**")
        
    st.caption(f"Info: Bei {feld_groesse} ha benötigst du ca. {round(kalk_bedarf/2000, 1)} BigBags Kalk.")

st.divider()
st.caption("LS25 Tool - Lokal auf deinem Mac gespeichert.")