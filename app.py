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
    st._global_finanzen = {"start_saldo": 250000.0, "einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}

LISTE_MONATE = ["01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"]

# --- HILFSFUNKTIONEN ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items(): txt = txt.replace(r, v)
    return txt

def fmt_int(wert): return f"{wert:,.0f}".replace(",", ".")
def fmt_float(wert): return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- PDF GENERATOR ---
class ManagementPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, "LU-BETRIEB MANAGEMENT & LOGISTIK", ln=True)
        self.line(10, 20, 200, 20)
        self.ln(15)
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Seite {self.page_no()}", align="C")

def generate_invoice_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum):
    pdf = ManagementPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.multi_cell(65, 6, f"In-Game Datum: {ingame_datum}\nRechnung-Nr: #RE-{rechnungs_id:04d}", align="R")
    pdf.ln(15)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 6, "Empfaenger:", ln=True)
    pdf.cell(0, 6, safe_str(kunden_name), ln=True)
    pdf.ln(20)
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "RECHNUNG", ln=True)
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    summe = 0
    for p in posten:
        pdf.set_font("Helvetica", size=11)
        pdf.cell(80, 10, safe_str(p['name']), border=0)
        pdf.cell(30, 10, f"{p['menge']} {p['einheit']}", border=0, align="C")
        pdf.cell(40, 10, f"{fmt_float(p['preis'])} EUR", border=0, align="R")
        pdf.cell(40, 10, f"{fmt_float(p['gesamt'])} EUR", border=0, align="R")
        pdf.ln(10)
        summe += p['gesamt']
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    total = summe - (summe * (rabatt_prozent / 100))
    pdf.cell(150, 6, "Zwischensumme:", align="R")
    pdf.cell(40, 6, f"{fmt_float(summe)} EUR", align="R", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    return pdf.output()

# --- DATEN-LOAD ---
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
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else ["Haupt-Hof", "Hof Alpha", "Lohnbetrieb West"]

if "rechnungs_posten" not in st.session_state: st.session_state.rechnungs_posten = []

# --- IN-GAME DATUM CONTROLLER ---
col_time1, col_time2 = st.columns(2)
with col_time1:
    ig_jahr = st.number_input("In-Game Jahr:", min_value=1, max_value=99, value=1, step=1)
with col_time2:
    ig_monat = st.selectbox("In-Game Monat:", LISTE_MONATE, index=4)
formatiertes_datum = f"Jahr {ig_jahr}, {ig_monat[5:]}"

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
st.sidebar.write(f"🌿 Herbizid: **{fmt_int(st._global_lager_store['herbi'])} L**")
st.sidebar.write(f"⛽ Diesel: **{fmt_int(st._global_lager_store['diesel'])} L**")

menu = st.sidebar.radio("Navigation", [
    "💰 Ernte & Verbrauchsraten", "🚜 Meine Felder & Anbau",
    "📋 Rechnungen", "🛒 Material & Aufträge", "🏭 Produktionen", "📖 Kassenbuch"
])

# --- MENÜ: ERNTE & VERBRAUCHSRATEN ---
if menu == "💰 Ernte & Verbrauchsraten":
    st.title("🌾 Ernte-Kalkulator & Preisliste")
    
    c_e1, c_e2, c_e3 = st.columns(3)
    f_fläche = c_e1.number_input("Feldfläche in Hektar (ha):", min_value=0.1, value=2.5)
    f_frucht = c_e2.selectbox("Fruchtart:", st._global_fruchtarten)
    f_ertrag_pro_ha = c_e3.number_input("Erwarteter Ertrag pro ha (Liter):", min_value=100, value=8500)
    
    gesamtertrag_calc = f_fläche * f_ertrag_pro_ha
    st.metric(f"Berechnete Gesamternte ({f_frucht})", f"{fmt_int(gesamtertrag_calc)} Liter")
    
    st.markdown("---")
    st.subheader("📈 Aktuelle LU-Dienstleistungspreise (Google Sheets)")
    if not df_preise.empty:
        st.dataframe(df_preise, use_container_width=True, hide_index=True)
    else:
        st.warning("Keine Preisdaten verfügbar.")

# --- MENÜ: MEINE FELDER & ANBAU ---
elif menu == "🚜 Meine Felder & Anbau":
    st.title("🚜 Feld-Verwaltung & Anbauplanung")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        st.subheader("📍 Neues Feld erfassen")
        f_nr = st.number_input("Feldnummer:", min_value=1, value=12)
        f_groesse = st.number_input("Größe (ha):", min_value=0.0, value=3.4)
        f_akt_frucht = st.selectbox("Aktuelle Frucht:", st._global_fruchtarten)
        
        if st.button("➕ Feld hinzufügen", use_container_width=True):
            st._global_felder_store.append({"Feld": f_nr, "Größe (ha)": f_groesse, "Frucht": f_akt_frucht})
            st.success(f"Feld {f_nr} gespeichert!")
            st.rerun()
            
    with col_f2:
        st.subheader("📋 Feld-Kataster")
        if st._global_felder_store:
            df_fel = pd.DataFrame(st._global_felder_store)
            st.dataframe(df_fel, use_container_width=True, hide_index=True)
            if st.button("🗑️ Alle Felder löschen"):
                st._global_felder_store = []
                st.rerun()
        else:
            st.info("Noch keine Felder registriert.")

# --- MENÜ: RECHNUNGEN ---
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
    
    c_r1, c_r2 = st.columns(2)
    kunde_wähl = c_r1.selectbox("Kunde / Ziel-Hof:", aktuelle_kunden)
    rabatt = c_r2.slider("Rabatt (%)", 0, 50, 0)
    
    st.markdown("### 🛒 Posten hinzufügen")
    c_p1, c_p2, c_p3 = st.columns(3)
    arbeit = c_p1.selectbox("Arbeitsschritt / Gerät:", list(preis_dict.keys()) if preis_dict else ["Dreschen", "Säen", "Grubbern"])
    menge = c_p2.number_input("Menge (z.B. ha oder Std):", min_value=0.1, value=1.0)
    einheit = c_p3.selectbox("Einheit:", ["ha", "Std", "Fuhren", "L"])
    
    preis_stueck = preis_dict.get(arbeit, 50.0)
    st.write(f"Stückpreis laut Liste: **{fmt_float(preis_stueck)} €**")
    
    if st.button("➕ Posten zur Rechnung hinzufügen"):
        st.session_state.rechnungs_posten.append({
            "name": arbeit, "menge": menge, "einheit": einheit, "preis": preis_stueck, "gesamt": preis_stueck * menge
        })
        
    if st.session_state.rechnungs_posten:
        st.markdown("### Aktuelle Rechnungsaufstellung")
        df_posten = pd.DataFrame(st.session_state.rechnungs_posten)
        st.dataframe(df_posten, use_container_width=True)
        
        summe = df_posten["gesamt"].sum()
        endbetrag = summe - (summe * (rabatt / 100))
        
        st.write(f"**Gesamtsumme (inkl. Rabatt): {fmt_float(endbetrag)} €**")
        
        if st.button("💾 Rechnung finalisieren & buchen", type="primary"):
            r_id = st._global_finanzen["naechste_rechnung_id"]
            st._global_finanzen["einnahmen"] += endbetrag
            st._global_finanzen["historie"].append({
                "In-Game Datum": formatiertes_datum, "Sort_Jahr": ig_jahr, "Sort_Monat": ig_monat[:2],
                "Typ": "Einnahme", "Nummer": f"#RE-{r_id:04d}", "Details": f"Rechnung an {kunde_wähl}", "Betrag (EUR)": endbetrag
            })
            
            # PDF Erzeugen
            pdf_data = generate_invoice_pdf(kunde_wähl, st.session_state.rechnungs_posten, rabatt, r_id, formatiertes_datum)
            st.download_button("📥 PDF-Rechnung herunterladen", data=pdf_data, file_name=f"Rechnung_RE-{r_id}.pdf", mime="application/pdf")
            
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.success("Rechnung erfolgreich verbucht!")

# --- MENÜ: MATERIAL & AUFTRÄGE ---
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Wareneinkauf & Logistik")
    
    st.subheader("🏪 Saatgut & Düngemittel einkaufen")
    c_m1, c_m2 = st.columns(2)
    ware = c_m1.selectbox("Ware:", ["Saatgut", "Kalk", "Dünger", "Herbizid", "Diesel"])
    menge_kauf = c_m2.number_input("Menge in Liter (L):", min_value=100, value=1000, step=100)
    
    preise_logistik = {"Saatgut": 0.90, "Kalk": 0.15, "Dünger": 0.60, "Herbizid": 1.20, "Diesel": 1.40}
    kosten_log = menge_kauf * preise_logistik[ware]
    
    st.write(f"Gesamtkosten Einkauf: **{fmt_float(kosten_log)} €**")
    
    if st.button("🛒 Kostenpflichtig bestellen & einlagern", type="primary"):
        if aktuelle_hof_kasse >= kosten_log:
            st._global_finanzen["ausgaben"] += kosten_log
            
            # Lagerzuordnung
            key_map = {"Saatgut": "saat", "Kalk": "kalk", "Dünger": "dueng", "Herbizid": "herbi", "Diesel": "diesel"}
            st._global_lager_store[key_map[ware]] += menge_kauf
            
            st._global_finanzen["historie"].append({
                "In-Game Datum": formatiertes_datum, "Sort_Jahr": ig_jahr, "Sort_Monat": ig_monat[:2],
                "Typ": "Ausgabe", "Nummer": "#LOG-EINK", "Details": f"{menge_kauf}L {ware} gekauft", "Betrag (EUR)": kosten_log
            })
            st.success(f"{menge_kauf}L {ware} wurden ins Hof-Lager eingebucht!")
            st.rerun()
        else:
            st.error("Zu wenig Geld auf dem Konto!")

# --- MENÜ: PRODUKTIONEN ---
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
                            "In-Game Datum": formatiertes_datum, "Sort_Jahr": ig_jahr, "Sort_Monat": ig_monat[:2],
                            "Typ": "Ausgabe", "Nummer": "#FAB-PROD",
                            "Details": f"Betriebskosten für {fab['Name']} ({anzahl_zyklen} Zyklen)", "Betrag (EUR)": ges_kosten
                        })
                        st.success(f"Simulation erfolgreich! {fmt_int(ges_ertrag)}L {fab['Output_Name']} wurden hergestellt.")
                        st.rerun()
                    else:
                        st.error(f"🚨 Fehler: Das Input-Lager hat nicht genug {fab['Input_Name']}! Benötigt werden {fmt_int(ges_bedarf)}L.")

# --- MENÜ: KASSENBUCH ---
elif menu == "📖 Kassenbuch":
    st.title("📖 Kassenbuch & Finanzhistorie")
    if st._global_finanzen["historie"]:
        st.dataframe(pd.DataFrame(st._global_finanzen["historie"])[["In-Game Datum", "Typ", "Nummer", "Details", "Betrag (EUR)"]], use_container_width=True, hide_index=True)
    else:
        st.info("Noch keine Transaktionen im Kassenbuch verzeichnet.")
