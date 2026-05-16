import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- GLOBALER SERVER-SPEICHER (SYNCHRONISIERT) ---
if not hasattr(st, "_global_hof_store"): st._global_hof_store = []
if not hasattr(st, "_global_lager_store"): st._global_lager_store = {"saat": 5000, "kalk": 20000, "dueng": 4000, "herbi": 2000, "diesel": 5000}
if not hasattr(st, "_global_bestell_store"): st._global_bestell_store = []
if not hasattr(st, "_global_felder_store"): st._global_felder_store = []
if not hasattr(st, "_global_fabriken_store"): st._global_fabriken_store = []

if not hasattr(st, "_global_fruchtarten"):
    st._global_fruchtarten = ["Weizen", "Gerste", "Hafer", "Raps", "Sonnenblumen", "Sojabohnen", "Mais", "Kartoffeln", "Zuckerrüben", "Gras", "Luzerne", "Spinat"]

if not hasattr(st, "_global_finanzen"):
    st._global_finanzen = {"start_saldo": 0.0, "einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}

LISTE_MONATE = ["01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"]

# --- HILFSFUNKTIONEN ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items(): txt = txt.replace(r, v)
    return txt

def fmt_int(wert): return f"{wert:,.0f}".replace(",", ".")
def fmt_float(wert): return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- DATA LOADING ---
SHEET_ID = "1nRViE_WnhMnAIJuYsYvZ3KaxAR43DnpDcHmtoA0qzPo"
PREIS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
KUNDEN_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=568043650"

@st.cache_data(ttl=5)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else ["Mein eigener Hof"]

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []

# --- SIDEBAR LIVE-ANZEIGE ---
st.sidebar.title("💰 Hof-Kasse (Live)")
einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
aktuelle_hof_kasse = st._global_finanzen["start_saldo"] + einn - ausg
st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")

st.sidebar.markdown("---")
st.sidebar.title("📦 Live-Lagerbestand")
st.sidebar.write(f"🌱 Saatgut: **{fmt_int(st._global_lager_store['saat'])} L**")
st.sidebar.write(f"⚪ Kalk: **{fmt_int(st._global_lager_store['kalk'])} L**")
st.sidebar.write(f"🧪 Dünger: **{fmt_int(st._global_lager_store['dueng'])} L**")

menu = st.sidebar.radio("Navigation", [
    "💰 Ernte & Verbrauchsraten", "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", "🛒 Material & Aufträge", "🏭 Produktionen", "📖 Kassenbuch"
])

# --- MENÜ: ERNTE & VERBRAUCHSRATEN ---
if menu == "💰 Ernte & Verbrauchsraten":
    st.title("🚜 Ernte-Kalkulator & Globale Raten")
    st.info("Hier siehst du die aktuellen globalen Logistik-Raten.")
    
    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.subheader("🌾 Ertragsfaktoren")
        st.write("Standard-Raten für Getreide und Feldfrüchte sind aktiv.")
    with col_r2:
        st.subheader("📈 Preislisten-Übersicht")
        if not df_preise.empty:
            st.dataframe(df_preise, use_container_width=True, hide_index=True)
        else:
            st.warning("Keine externen Preislisten-Daten geladen.")

# --- MENÜ: MEINE FELDER & ANBAU ---
elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung")
    st.write("Verwalte hier deine aktiven Felder und Fruchtfolgen.")

# --- MENÜ: RECHNUNGEN ---
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen")
    st.info("Hier können Rechnungen erstellt und verwaltet werden.")

# --- MENÜ: MATERIAL & AUFTRÄGE ---
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Logistik & Aufträge")
    st.write("Bestellungen für Saatgut, Kalk und Dünger.")

# --- MENÜ: PRODUKTIONEN (JETZT GEGEN KEYERROR ABGESICHERT) ---
elif menu == "🏭 Produktionen":
    st.title("🏭 Interaktive Fabrik- & Lagerverwaltung")
    st.markdown("Registriere Fabriken, bearbeite Input/Output-Lager manuell oder starte Zyklen-Simulationen!")

    col_form, col_summary = st.columns([1, 1])
    
    with col_form:
        st.subheader("🏗️ Neue Fabrik registrieren")
        f_bezeichnung = st.text_input("Eigener Name der Fabrik:", placeholder="z.B. Lohn-Mühle Süd")
        f_besitzer = st.selectbox("Betreiber / Besitzer (Hof):", aktuelle_kunden)
        
        c_p1, c_p2 = st.columns(2)
        f_input_name = c_p1.text_input("Welcher Rohstoff (Input)?", value="Weizen")
        f_output_name = c_p2.text_input("Welches Endprodukt (Output)?", value="Mehl")
        
        c_p3, c_p4, c_p5 = st.columns(3)
        f_verbrauch_zyklus = c_p3.number_input("Verbrauch pro Zyklus (L):", min_value=1, value=150)
        f_ertrag_zyklus = c_p4.number_input("Ertrag pro Zyklus (L):", min_value=1, value=90)
        f_kosten_zyklus = c_p5.number_input("Kosten pro Zyklus (€):", min_value=0.0, value=10.0)

        if st.button("🏗️ Fabrik auf Server registrieren", type="primary", use_container_width=True):
            if f_bezeichnung.strip():
                st._global_fabriken_store.append({
                    "Name": f_bezeichnung.strip(), "Besitzer": f_besitzer,
                    "Input_Name": f_input_name, "Input_Lager": 0.0, "Verbrauch_Pro_Zyklus": f_verbrauch_zyklus,
                    "Output_Name": f_output_name, "Output_Lager": 0.0, "Ertrag_Pro_Zyklus": f_ertrag_zyklus,
                    "Kosten_Pro_Zyklus": f_kosten_zyklus, "Zyklen_Gefahren": 0
                })
                st.success(f"'{f_bezeichnung}' wurde hochgefahren!")
                st.rerun()

    with col_summary:
        st.subheader("📊 Registrierte Wirtschaftsobjekte")
        
        # SPERRE GEGEN KEYERROR: Falls der Speicher leer ist, fangen wir das hier sauber ab!
        if st._global_fabriken_store:
            df_f = pd.DataFrame(st._global_fabriken_store)
        else:
            df_f = pd.DataFrame(columns=["Name", "Besitzer", "Input_Lager", "Output_Lager", "Zyklen_Gefahren"])
            
        st.dataframe(df_f[["Name", "Besitzer", "Input_Lager", "Output_Lager", "Zyklen_Gefahren"]], use_container_width=True, hide_index=True)
        
        if st._global_fabriken_store:
            if st.button("❌ Alle Fabriken liquidieren (Löschen)", type="secondary"):
                st._global_fabriken_store = []
                st.rerun()
        else:
            st.info("Keine Fabriken aktiv.")

    # --- DETAILLIERTE STEUERUNG FÜR JEDE FABRIK ---
    if st._global_fabriken_store:
        st.write("---")
        st.subheader("⚙️ Fabriken-Kontrollzentrum (Lager & Simulation)")
        
        for idx, fab in enumerate(st._global_fabriken_store):
            with st.expander(f"🏭 {fab['Name']} (Besitzer: {fab['Besitzer']})", expanded=True):
                
                c_stat1, c_stat2, c_stat3 = st.columns(3)
                c_stat1.metric(f"📦 Input-Lager ({fab['Input_Name']})", f"{fmt_int(fab['Input_Lager'])} Liter")
                c_stat2.metric(f"📦 Output-Lager ({fab['Output_Name']})", f"{fmt_int(fab['Output_Lager'])} Liter")
                c_stat3.metric("Durchgelaufene Zyklen", f"{fab['Zyklen_Gefahren']}")
                
                st.write("**Lagerbestände & Rezeptur manuell bearbeiten:**")
                c_edit1, c_edit2, c_edit3, c_edit4 = st.columns(4)
                
                new_in = c_edit1.number_input(f"Input-Bestand ({fab['Input_Name']}):", value=float(fab['Input_Lager']), key=f"in_b_{idx}")
                new_out = c_edit2.number_input(f"Output-Bestand ({fab['Output_Name']}):", value=float(fab['Output_Lager']), key=f"out_b_{idx}")
                new_v = c_edit3.number_input("Verbrauch/Zyklus:", value=int(fab['Verbrauch_Pro_Zyklus']), key=f"v_b_{idx}")
                new_e = c_edit4.number_input("Ertrag/Zyklus:", value=int(fab['Ertrag_Pro_Zyklus']), key=f"e_b_{idx}")
                
                st._global_fabriken_store[idx]["Input_Lager"] = new_in
                st._global_fabriken_store[idx]["Output_Lager"] = new_out
                st._global_fabriken_store[idx]["Verbrauch_Pro_Zyklus"] = new_v
                st._global_fabriken_store[idx]["Ertrag_Pro_Zyklus"] = new_e
                
                st.write("**⚡ In-Game Zyklen-Simulation ausführen:**")
                c_sim1, c_sim2 = st.columns([1, 2])
                
                anzahl_zyklen = c_sim1.number_input("Wie viele Zyklen simulieren?", min_value=1, value=10, key=f"sim_anz_{idx}")
                
                ges_bedarf = anzahl_zyklen * fab['Verbrauch_Pro_Zyklus']
                ges_ertrag = anzahl_zyklen * fab['Ertrag_Pro_Zyklus']
                ges_kosten = anzahl_zyklen * fab['Kosten_Pro_Zyklus']
                
                c_sim2.markdown(f"**Berechnete Vorschau für {anzahl_zyklen} Zyklen:**\n"
                                f"📉 Benötigt: **{fmt_int(ges_bedarf)}L** {fab['Input_Name']} | "
                                f"📈 Produziert: **{fmt_int(ges_ertrag)}L** {fab['Output_Name']}\n"
                                f"💸 Betriebskosten (Abzug Hofkasse): **{fmt_float(ges_kosten)} €**")
                
                if st.button(f"🚀 {anzahl_zyklen} Zyklen simulieren", key=f"run_sim_{idx}", type="primary"):
                    if fab['Input_Lager'] >= ges_bedarf:
                        st._global_fabriken_store[idx]["Input_Lager"] -= ges_bedarf
                        st._global_fabriken_store[idx]["Output_Lager"] += ges_ertrag
                        st._global_fabriken_store[idx]["Zyklen_Gefahren"] += anzahl_zyklen
                        
                        st._global_finanzen["ausgaben"] += ges_kosten
                        st._global_finanzen["historie"].append({
                            "In-Game Datum": "Simulation", "Sort_Jahr": 1, "Sort_Monat": "01",
                            "Typ": "Ausgabe", "Nummer": "#FAB-PROD",
                            "Details": f"Betriebskosten für {fab['Name']} ({anzahl_zyklen} Zyklen)", "Betrag (EUR)": ges_kosten
                        })
                        st.success(f"Simulation erfolgreich! {fmt_int(ges_ertrag)}L {fab['Output_Name']} wurden hergestellt.")
                        st.rerun()
                    else:
                        st.error(f"🚨 Fehler: Das Input-Lager hat nicht genug {fab['Input_Name']}! Benötigt werden {fmt_int(ges_bedarf)}L.")

# --- MENÜ: KASSENBUCH ---
elif menu == "📖 Kassenbuch":
    st.title("📖 Kassenbuch")
    if st._global_finanzen["historie"]:
        st.dataframe(pd.DataFrame(st._global_finanzen["historie"])[["In-Game Datum", "Typ", "Nummer", "Details", "Betrag (EUR)"]], use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Transaktionen im Kassenbuch verzeichnet.")
