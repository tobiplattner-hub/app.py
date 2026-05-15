import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen - Zurück auf das klassische, breite Desktop-Layout
st.set_page_config(layout="wide", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- GLOBALER SERVER-SPEICHER (FÜR ALLE SPIELER SYNCHRONISIERT) ---
if not hasattr(st, "_global_hof_store"):
    st._global_hof_store = []

if not hasattr(st, "_global_lager_store"):
    st._global_lager_store = {"saat": 3000, "kalk": 10000, "dueng": 2000, "herbi": 2000, "diesel": 5000}

if not hasattr(st, "_global_bestell_store"):
    st._global_bestell_store = []

if not hasattr(st, "_global_finanzen"):
    st._global_finanzen = {
        "start_saldo": 0.0,
        "einnahmen": 0.0,
        "ausgaben": 0.0,
        "naechste_rechnung_id": 1,
        "naechste_bestellung_id": 1,
        "historie": []
    }

LISTE_MONATE = [
    "01 - Jan", "02 - Feb", "03 - Mrz", "04 - Apr", 
    "05 - Mai", "06 - Jun", "07 - Jul", "08 - Aug", 
    "09 - Sep", "10 - Okt", "11 - Nov", "12 - Dez"
]

# --- HILFSFUNKTIONEN ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items():
        txt = txt.replace(r, v)
    return txt

def fmt_int(wert):
    return f"{wert:,.0f}".replace(",", ".")

def fmt_float(wert):
    return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --- PDF KLASSEN ---
class InvoicePDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 15, 15, 40)
        else:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "LU-BETRIEB", ln=True)
        self.ln(20)

def generate_pdf(kunden_name, posten, rabatt_prozent, rechnungs_id, ingame_datum):
    pdf = InvoicePDF()
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
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(80, 10, "Leistung / Maschine", border=0)
    pdf.cell(30, 10, "Menge", border=0, align="C")
    pdf.cell(40, 10, "Einzelpreis", border=0, align="R")
    pdf.cell(40, 10, "Gesamt", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    summe = 0
    for p in posten:
        pdf.cell(80, 10, safe_str(p['name']), border=0)
        pdf.cell(30, 10, f"{p['menge']} {p['einheit']}", border=0, align="C")
        pdf.cell(40, 10, f"{fmt_float(p['preis'])} EUR", border=0, align="R")
        pdf.cell(40, 10, f"{fmt_float(p['gesamt'])} EUR", border=0, align="R")
        pdf.ln(10)
        summe += p['gesamt']
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    rabatt_betrag = summe * (rabatt_prozent / 100)
    total = summe - rabatt_betrag
    pdf.cell(150, 6, "Zwischensumme:", align="R")
    pdf.cell(40, 6, f"{fmt_float(summe)} EUR", align="R", ln=True)
    if rabatt_prozent > 0:
        pdf.cell(150, 6, f"Rabatt ({rabatt_prozent}%):", align="R")
        pdf.cell(40, 6, f"-{fmt_float(rabatt_betrag)} EUR", align="R", ln=True)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(150, 10, "GESAMTBETRAG:", align="R")
    pdf.cell(40, 10, f"{fmt_float(total)} EUR", align="R", ln=True)
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Vielen Dank fuer die gute Zusammenarbeit!", align="C")
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
    except: 
        return pd.DataFrame()

df_preise = load_data(PREIS_URL)
preis_dict = dict(zip(df_preise['Geraet'], df_preise['Preis'])) if not df_preise.empty else {}
df_kunden = load_data(KUNDEN_URL)
aktuelle_kunden = df_kunden['Name'].dropna().unique().tolist() if not df_kunden.empty else []

if "rechnungs_posten" not in st.session_state: 
    st.session_state.rechnungs_posten = []

PROD_DATA = {
    "Getreidemühle: Weizen zu Mehl": (36000, 27000, "Weizen", "Mehl"),
    "Bäckerei: Brot": (21600, 10800, "Mehl", "Brot"),
    "Ölmühle: Rapsöl": (14400, 7200, "Raps", "Rapsöl"),
    "Molkerei: Käse": (21600, 16200, "Milch", "Käse"),
    "➕ Eigenes / Mod-Rezept": (0, 0, "", "")
}

# --- SIDEBAR FINANZ-MANAGEMENT ---
st.sidebar.title("💰 Hof-Kasse (Server-Live)")

einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
aktuelle_hof_kasse = st._global_finanzen["start_saldo"] + einn - ausg

st.sidebar.metric("Aktueller Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")
st.sidebar.write(f"📈 Gesamteinnahmen: {fmt_float(einn)} €")
st.sidebar.write(f"📉 Gesamtausgaben: {fmt_float(ausg)} €")

st.sidebar.markdown("---")
st.sidebar.subheader("Manuelle Buchung / Startkapital")
st._global_finanzen["start_saldo"] = st.sidebar.number_input("Start-Saldo (€):", min_value=0.0, value=float(st._global_finanzen.get("start_saldo", 0.0)), step=10000.0)

m_typ = st.sidebar.radio("Buchungs-Typ:", ["Einnahme", "Ausgabe"])
m_betrag = st.sidebar.number_input("Betrag (€):", min_value=0.0, value=1000.0)
m_details = st.sidebar.text_input("Verwendungszweck:")
m_monat = st.sidebar.selectbox("In-Game Monat:", LISTE_MONATE, key="sb_m")
m_jahr = st.sidebar.number_input("In-Game Jahr:", min_value=1, value=1, key="sb_j")

if st.sidebar.button("💾 Buchung保存", use_container_width=True):
    if m_details.strip():
        in_game_datum_str = f"J{m_jahr}-{m_monat}"
        if m_typ == "Einnahme":
            st._global_finanzen["einnahmen"] += m_betrag
        else:
            st._global_finanzen["ausgaben"] += m_betrag
        st._global_finanzen["historie"].append({
            "In-Game Datum": in_game_datum_str, "Sort_Jahr": m_jahr, "Sort_Monat": m_monat,
            "Typ": m_typ, "Nummer": "MANUELL", "Details": m_details, "Betrag (EUR)": m_betrag
        })
        st.rerun()

if st.sidebar.button("🗑️ Kassenbuch komplett zurücksetzen", use_container_width=True):
    st._global_finanzen = {"start_saldo": 0.0, "einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}
    st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio("Hauptmenü Navigation", ["💰 Ernte & Felder", "📋 Rechnungen", "🛒 Material & Aufträge", "🏭 Produktionen"])

# --- SEITE 1 ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte-Kalkulator & Saatgut-Planer")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚙️ Standard-Verbrauchsraten anpassen")
        r_kalk = st.number_input("Kalk Bedarf (L/ha):", value=2000)
        r_duenger = st.number_input("Dünger Bedarf (L/ha):", value=160)
        r_saat = st.number_input("Saatgut Bedarf (L/ha):", value=150)
        r_herbi = st.number_input("Herbizid Bedarf (L/ha):", value=100)
        
    with col2:
        st.subheader("🧪 Feldbedarf berechnen")
        ha = st.number_input("Hektar Gesamtfläche (ha):", min_value=0.1, value=1.0, step=0.1)
        st.markdown(f"### Benötigtes Material für {ha} ha:")
        st.write(f"⚪ Kalk: **{fmt_int(ha * r_kalk)} Liter**")
        st.write(f"🧪 Dünger: **{fmt_int(ha * r_duenger)} Liter**")
        st.write(f"🌱 Saatgut: **{fmt_int(ha * r_saat)} Liter**")
        st.write(f"🌿 Herbizid: **{fmt_int(ha * r_herbi)} Liter**")

    st.write("---")
    st.subheader("📊 Erlösrechner für Ernteerträge")
    c1, c2 = st.columns(2)
    menge = c1.number_input("Geerntete Menge (Liter im Silo):", value=10000)
    preis_pro_1000 = c2.number_input("Aktueller Marktpreis (€ pro 1000L):", value=1200)
    erloes = (menge / 1000) * preis_pro_1000
    st.success(f"## 💵 Erwarteter Umsatz: {fmt_float(erloes)} EUR")

# --- SEITE 2 ---
elif menu == "📋 Rechnungen":
    st.title("📋 Dienstleistungs-Rechnungen erstellen")
    st.info(f"Nächste Rechnungsnummer auf dem Server: **#RE-{st._global_finanzen['naechste_rechnung_id']:04d}**")

    col_eingabe, col_liste = st.columns([1, 1])
    
    with col_eingabe:
        st.subheader("Posten hinzufügen")
        abrechnungs_art = st.selectbox("Abrechnungs-Methode:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Sonderposten"])
        
        if abrechnungs_art == "Sonderposten":
            auswahl = st.text_input("Freie Beschreibung:")
            menge = st.number_input("Menge:", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis (€):", value=0.0)
            einheit_str = "Stk"
        elif abrechnungs_art == "Nach Feldfläche (ha)":
            auswahl = st.text_input("Dienstleistung (z.B. Grubbern, Drillen):", value="Mähen")
            menge = st.number_input("Fläche (ha):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Hektar (€/ha):", value=50.0)
            einheit_str = "ha"
        else: 
            auswahl = st.selectbox("Maschine / Service aus Google-Sheet:", options=list(preis_dict.keys()) if preis_dict else ["Standard-Traktor"])
            menge = st.number_input("Gefahrene Stunden (h):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis pro Stunde (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
            einheit_str = "h"
            
        if st.button("➕ Posten zur Rechnung hinzufügen", use_container_width=True):
            if auswahl.strip():
                st.session_state.rechnungs_posten.append({"name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p})
                st.rerun()

    with col_liste:
        st.subheader("Rechnungsdaten & Vorschau")
        k_name = st.selectbox("Empfänger (Kunde):", aktuelle_kunden) if aktuelle_kunden else st.text_input("Empfänger (Hofname):")
        rabatt = st.slider("Rabatt auf Gesamtsumme (%)", 0, 50, 0)
        
        c_m, c_j = st.columns(2)
        re_monat = c_m.selectbox("In-Game Monat:", LISTE_MONATE, key="re_m")
        re_jahr = c_j.number_input("In-Game Jahr:", min_value=1, value=1, key="re_j")

    if st.session_state.rechnungs_posten:
        st.write("---")
        st.subheader("📑 Aktuelle Rechnungsposten")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        st.dataframe(df_preview[["name", "menge", "einheit", "preis", "gesamt"]], use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        rabatt_betrag = summe * (rabatt / 100)
        total = summe - rabatt_betrag
        
        c_res1, c_res2 = st.columns(2)
        c_res1.metric("Zwischensumme", f"{fmt_float(summe)} EUR")
        c_res2.metric("Endbetrag (inkl. Rabatt)", f"{fmt_float(total)} EUR")
        
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st._global_finanzen["naechste_rechnung_id"], full_ingame_date)
        
        col_b1, col_b2, col_b3 = st.columns(3)
        col_b1.download_button("📥 PDF generieren & laden", data=bytes(pdf_data), file_name=f"Rechnung_{k_name}_#RE{st._global_finanzen['naechste_rechnung_id']}.pdf", mime="application/pdf", use_container_width=True)
        
        if col_b2.button("💾 Als Einnahme buchen & Rechnungs-Nr erhöhen", type="primary", use_container_width=True):
            st._global_finanzen["einnahmen"] += total
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": re_jahr, "Sort_Monat": re_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st._global_finanzen['naechste_rechnung_id']:04d}",
                "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.rerun()
            
        if col_b3.button("🗑️ Rechnung verwerfen", use_container_width=True):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3 ---
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Materialeinkauf & Externe Dienstleistungen")
    
    st.subheader("📦 Aktueller Hof-Bestand (Wird live für alle Spieler synchronisiert)")
    c_l1, c_l2, c_l3, c_l4, c_l5 = st.columns(5)
    
    v_saat = c_l1.number_input("Saatgut (L):", min_value=0, value=int(st._global_lager_store["saat"]), step=500)
    v_kalk = c_l2.number_input("Kalk (L):", min_value=0, value=int(st._global_lager_store["kalk"]), step=1000)
    v_dueng = c_l3.number_input("Dünger (L):", min_value=0, value=int(st._global_lager_store["dueng"]), step=500)
    v_herbi = c_l4.number_input("Herbizid (L):", min_value=0, value=int(st._global_lager_store.get("herbi", 2000)), step=500)
    v_diesel = c_l5.number_input("Diesel (L):", min_value=0, value=int(st._global_lager_store.get("diesel", 5000)), step=500)
    
    if st.button("💾 Lagerbestände auf Server speichern", use_container_width=True):
        st._global_lager_store.update({"saat": v_saat, "kalk": v_kalk, "dueng": v_dueng, "herbi": v_herbi, "diesel": v_diesel})
        st.rerun()

    c_s1, c_s2, c_s3, c_s4, c_s5 = st.columns(5)
    def status_box(col, label, menge, limit):
        if menge < limit: col.error(f"🚨 {label}\n\n{fmt_int(menge)} L (Wenig!)")
        else: col.success(f"✅ {label}\n\n{fmt_int(menge)} L")
    
    status_box(c_s1, "Saatgut", st._global_lager_store["saat"], 1500)
    status_box(c_s2, "Kalk", st._global_lager_store["kalk"], 5000)
    status_box(c_s3, "Dünger", st._global_lager_store["dueng"], 1000)
    status_box(c_s4, "Herbizid", st._global_lager_store["herbi"], 1000)
    status_box(c_s5, "Diesel", st._global_lager_store["diesel"], 1500)
            
    st.write("---")
    
    col_links, col_rechts = st.columns(2)
    with col_links:
        st.subheader("🚜 Dienstleister / anderes LU beauftragen")
        lu_arbeit = st.text_input("Welche Arbeit soll erledigt werden?", placeholder="z.B. Häckseln Feld 4")
        c_lu1, c_lu2 = st.columns(2)
        lu_einheit = c_lu1.selectbox("Abrechnungseinheit:", ["ha", "h"])
        lu_menge = c_lu2.number_input("Menge (ha oder h):", min_value=0.1, value=1.0)
        
        if st.button("📝 Dienstleistung auf Einkaufsliste setzen", use_container_width=True):
            if lu_arbeit.strip():
                st._global_bestell_store.append({"artikel": f"LU: {lu_arbeit}", "menge": lu_menge, "einheit": lu_einheit})
                st.rerun()
                
    with col_rechts:
        st.subheader("📉 Automatischer Einkaufsvorschlag")
        c_p1, c_p2, c_p3 = st.columns(3)
        p_saat = c_p1.number_input("Saatgut (€/1k L):", value=900)
        p_kalk = c_p2.number_input("Kalk (€/1k L):", value=150)
        p_dueng = c_p3.number_input("Dünger (€/1k L):", value=1200)

        order_saat = st.number_input("Saatgut Kaufmenge (L):", min_value=0, value=2000 if st._global_lager_store["saat"] < 1500 else 0)
        order_kalk = st.number_input("Kalk Kaufmenge (L):", min_value=0, value=5000 if st._global_lager_store["kalk"] < 5000 else 0)
        order_dueng = st.number_input("Dünger Kaufmenge (L):", min_value=0, value=1000 if st._global_lager_store["dueng"] < 1000 else 0)
        
        if st.button("📝 Vorgeschlagene Waren auf Einkaufsliste setzen", use_container_width=True):
            if order_saat > 0: st._global_bestell_store.append({"artikel": "Saatgut", "menge": order_saat, "einheit": "L"})
            if order_kalk > 0: st._global_bestell_store.append({"artikel": "Kalk", "menge": order_kalk, "einheit": "L"})
            if order_dueng > 0: st._global_bestell_store.append({"artikel": "Fluessigduenger", "menge": order_dueng, "einheit": "L"})
            st.rerun()

    if st._global_bestell_store:
        st.write("---")
        st.subheader("📋 Aktuelle Einkaufs- & Auftragsliste")
        
        col_tbl, col_actions = st.columns([2, 1])
        with col_tbl:
            df_b = pd.DataFrame(st._global_bestell_store)
            st.dataframe(df_b[["artikel", "menge", "einheit"]], use_container_width=True, hide_index=True)
        
        with col_actions:
            loesch_optionen = [f"{i+1}: {p['artikel']}" for i, p in enumerate(st._global_bestell_store)]
            p_del = st.selectbox("Eintrag entfernen:", options=loesch_optionen)
            if st.button("❌ Eintrag löschen", use_container_width=True):
                st._global_bestell_store.pop(int(p_del.split(":")[0]) - 1)
                st.rerun()

            st.write("---")
            col_bm, col_bj = st.columns(2)
            bs_monat = col_bm.selectbox("Kauf im Monat:", LISTE_MONATE, key="bs_m")
            bs_jahr = col_bj.number_input("Kauf im Jahr:", min_value=1, value=1, key="bs_j")
            
            tatsaechliche_kosten = st.number_input("Rechnungsendbetrag (€):", min_value=0.0)
            full_bs_date = f"J{bs_jahr}-{bs_monat}"
            
            if st.button("✅ Liste abarbeiten & als Ausgabe buchen", type="primary", use_container_width=True):
                st._global_finanzen["ausgaben"] += tatsaechliche_kosten
                st._global_finanzen["historie"].append({
                    "In-Game Datum": full_bs_date, "Sort_Jahr": bs_jahr, "Sort_Monat": bs_monat,
                    "Typ": "Ausgabe", "Nummer": f"#BS-{st._global_finanzen['naechste_bestellung_id']:04d}",
                    "Details": f"Material/Dienstleistung eingekauft", "Betrag (EUR)": tatsaechliche_kosten
                })
                st._global_bestell_store = []
                st._global_finanzen["naechste_bestellung_id"] += 1
                st.rerun()

# --- SEITE 4 (KLASSISCHES DESKTOP LAYOUT + FIX FÜR KEYERROR) ---
elif menu == "🏭 Produktionen":
    st.title("🏭 Produktions-Kapazitäten & Jahresplaner")
    
    col_form, col_space = st.columns([1, 1])
    with col_form:
        st.subheader("Neue Fabrik / Produktionslinie registrieren")
        rezept = st.selectbox("Wähle das Rezept aus:", options=list(PROD_DATA.keys()))
        
        if rezept == "➕ Eigenes / Mod-Rezept":
            in_name = st.text_input("Rohstoff Name (Input):", value="Weizen")
            out_name = st.text_input("Produkt Name (Output):", value="Mehl")
            c_c1, c_c2 = st.columns(2)
            custom_in_std = c_c1.number_input("Input Menge pro Stunde (L):", min_value=1, value=50)
            custom_out_std = c_c2.number_input("Output Menge pro Stunde (L):", min_value=1, value=38)
            base_in = custom_in_std * 24 * 30
            base_out = custom_out_std * 24 * 30
            name_anzeige = f"Mod: {in_name} -> {out_name}"
        else:
            base_in, base_out, in_name, out_name = PROD_DATA[rezept]
            name_anzeige = rezept
            
        c_f1, c_f2 = st.columns(2)
        anzahl_fabriken = c_f1.number_input("Anzahl aktiver Linien:", min_value=1, value=1, step=1)
        monate = c_f2.slider("Betriebsmonate pro Jahr:", 1, 12, 12)
        
        aktueller_lagerbestand = st.number_input(f"📦 Aktueller Lagerbestand für '{in_name}' (Liter):", min_value=0, value=0, step=1000)
        
        if st.button("💾 Produktion für den Server speichern", type="primary", use_container_width=True):
            st._global_hof_store.append({
                "name": name_anzeige, "monate": monate, "linien": anzahl_fabriken,
                "in_typ": in_name, "in_menge": base_in * monate * anzahl_fabriken, 
                "out_typ": out_name, "out_menge": base_out * monate * anzahl_fabriken,
                "lager_ist": aktueller_lagerbestand,
                "basis_monat_input": base_in
            })
            st.rerun()

    if st._global_hof_store:
        st.write("---")
        st.subheader("🏭 Aktive Produktionen in der Übersicht")
        
        tabelle_daten = []
        for idx, item in enumerate(st._global_hof_store):
            # FIX: `.get()` verhindert den KeyError bei alten Einträgen auf dem Server
            basis_input = item.get("basis_monat_input", 0)
            lager_ist = item.get("lager_ist", 0)
            linien = item.get("linien", 1)
            
            monatlicher_verbrauch = basis_input * linien
            if monatlicher_verbrauch > 0 and lager_ist > 0:
                reichweite_monate = lager_ist / monatlicher_verbrauch
                if reichweite_monate >= 1.0:
                    reichweite_str = f"ca. {reichweite_monate:.1f} Monate"
                else:
                    reichweite_str = f"ca. {reichweite_monate * 30:.0f} Tage"
            else:
                reichweite_str = "k.A. / Lager leer"

            tabelle_daten.append({
                "ID": idx + 1,
                "Produktion/Rezept": item["name"],
                "Linien": linien,
                "Betriebsmonate/Jahr": item["monate"],
                "Lagerbestand (L)": fmt_int(lager_ist),
                "Reichweite Dauerbetrieb": reichweite_str,
                "Jahresbedarf Rohstoff (L)": fmt_int(item["in_menge"]),
                "Rohstoff-Typ": item["in_typ"],
                "Jahresertrag Produkt (L)": fmt_int(item["out_menge"]),
                "Produkt-Typ": item["out_typ"]
            })
            
        df_hof = pd.DataFrame(tabelle_daten)
        st.dataframe(df_hof, use_container_width=True, hide_index=True)
        
        if st.button("🗑️ Alle Produktionen aus der Übersicht löschen", use_container_width=True):
            st._global_hof_store = []
            st.rerun()

# --- FINANZ-HISTORIE DESKTOP-TABELLE ---
if st._global_finanzen["historie"]:
    st.write("---")
    st.subheader("📊 In-Game Monatsberichte & Finanzhistorie")
    df_raw = pd.DataFrame(st._global_finanzen["historie"])
    
    df_raw["Einnahme_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if r["Typ"] == "Einnahme" else 0.0, axis=1)
    df_raw["Ausgabe_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if r["Typ"] == "Ausgabe" else 0.0, axis=1)
    
    df_monat = df_raw.groupby(["In-Game Datum", "Sort_Jahr", "Sort_Monat"]).agg(
        Einnahmen=("Einnahme_Wert", "sum"),
        Ausgaben=("Ausgabe_Wert", "sum")
    ).reset_index().sort_values(by=["Sort_Jahr", "Sort_Monat"])
    
    df_monat["Gewinn"] = df_monat["Einnahmen"] - df_monat["Ausgaben"]
    
    c_tab1, c_tab2 = st.columns(2)
    with c_tab1:
        st.markdown("**Zusammenfassung nach In-Game Monaten:**")
        st.dataframe(df_monat[["In-Game Datum", "Einnahmen", "Ausgaben", "Gewinn"]], use_container_width=True, hide_index=True)
    with c_tab2:
        st.markdown("**Einzelbuchungen (Letzte zuerst):**")
        st.dataframe(df_raw[["In-Game Datum", "Typ", "Nummer", "Details", "Betrag (EUR)"]].iloc[::-1], use_container_width=True, hide_index=True)
