import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen - "centered" ist ideal für mobile Geräte
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

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

def generate_order_pdf(bestell_liste, bestell_id, ingame_datum):
    pdf = InvoicePDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.cell(65, 6, f"In-Game Datum: {ingame_datum}\nAuftrags-Nr: #BS-{bestell_id:04d}", align="R", ln=True)
    pdf.ln(35)
    pdf.set_x(50)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, "BESTELLUNG / ARBEITSAUFTRAG", ln=True)
    pdf.ln(15)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 10, "Artikel oder Dienstleistung", border=0)
    pdf.cell(60, 10, "Menge / Einheit", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    for b in bestell_liste:
        pdf.cell(120, 10, safe_str(b["artikel"]), border=0)
        pdf.cell(60, 10, f"{b['menge']} {b['einheit']}", border=0, align="R")
        pdf.ln(10)
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
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

# --- SIDEBAR FINANZ-METRIKEN (Kompakt für Mobile) ---
st.sidebar.markdown("## 💰 Hof-Kasse (Live)")

einn = st._global_finanzen["einnahmen"]
ausg = st._global_finanzen["ausgaben"]
aktuelle_hof_kasse = st._global_finanzen["start_saldo"] + einn - ausg

st.sidebar.metric("Kontostand", f"{fmt_float(aktuelle_hof_kasse)} €")

with st.sidebar.expander("⚙️ Einstellungen & Buchung"):
    st._global_finanzen["start_saldo"] = st.number_input("Start-Saldo:", min_value=0.0, value=float(st._global_finanzen.get("start_saldo", 0.0)), step=5000.0)
    st.write("---")
    m_typ = st.radio("Typ:", ["Einnahme", "Ausgabe"])
    m_betrag = st.number_input("Betrag (€):", min_value=0.0, value=1000.0)
    m_details = st.text_input("Zweck:")
    m_monat = st.selectbox("Monat:", LISTE_MONATE, key="sb_m")
    m_jahr = st.number_input("Jahr:", min_value=1, value=1, key="sb_j")
    
    if st.button("💾 Buchen", use_container_width=True):
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

if st.sidebar.button("🗑️ Kassenbuch Reset", use_container_width=True):
    st._global_finanzen = {"start_saldo": 0.0, "einnahmen": 0.0, "ausgaben": 0.0, "naechste_rechnung_id": 1, "naechste_bestellung_id": 1, "historie": []}
    st.rerun()

st.sidebar.write("---")
# Menü als Selectbox auf Mobile oft angenehmer, hier als Radio belassen für schnellen Wechsel
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungen", "🛒 Material & Aufträge", "🏭 Produktionen"])

# --- SEITE 1 ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte & Felder")
    with st.expander("⚙️ Verbrauchs-Raten (ha)"):
        r_kalk = st.number_input("Kalk (L/ha):", value=2000)
        r_duenger = st.number_input("Dünger (L/ha):", value=160)
        r_saat = st.number_input("Saatgut (L/ha):", value=150)
        r_herbi = st.number_input("Herbizid (L/ha):", value=100)
    
    st.subheader("🧪 Bedarfskalkulation")
    ha = st.number_input("Hektar (ha):", min_value=0.1, value=1.0, step=0.1)
    st.info(f"""
    **Bedarf für {ha} ha:**
    * Kalk: **{fmt_int(ha * r_kalk)} L** | Dünger: **{fmt_int(ha * r_duenger)} L**
    * Saatgut: **{fmt_int(ha * r_saat)} L** | Herbizid: **{fmt_int(ha * r_herbi)} L**
    """)
    
    st.subheader("📊 Erlösrechner")
    menge = st.number_input("Liter im Silo:", value=10000)
    preis_pro_1000 = st.number_input("€ pro 1000L:", value=1200)
    st.success(f"**Voraussichtlicher Erlös:** {fmt_float((menge / 1000) * preis_pro_1000)} EUR")

# --- SEITE 2 ---
elif menu == "📋 Rechnungen":
    st.title("📋 Rechnungs-Ersteller")
    st.caption(f"Nächste Nummer: #RE-{st._global_finanzen['naechste_rechnung_id']:04d}")

    with st.container(border=True):
        abrechnungs_art = st.selectbox("Methode:", ["Nach Arbeitsstunden (h)", "Nach Feldfläche (ha)", "Sonderposten"])
        
        if abrechnungs_art == "Sonderposten":
            auswahl = st.text_input("Bezeichnung:")
            menge = st.number_input("Menge:", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis (€):", value=0.0)
            einheit_str = "Stk"
        elif abrechnungs_art == "Nach Feldfläche (ha)":
            auswahl = st.text_input("Leistung:", value="Mähen")
            menge = st.number_input("Fläche (ha):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis (€/ha):", value=50.0)
            einheit_str = "ha"
        else: 
            auswahl = st.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["Traktorenarbeit"])
            menge = st.number_input("Zeit (h):", min_value=0.1, value=1.0)
            e_p = st.number_input("Preis (€/h):", value=float(preis_dict.get(auswahl, 0.0)))
            einheit_str = "h"
            
        if st.button("➕ Hinzufügen", use_container_width=True):
            if auswahl.strip():
                st.session_state.rechnungs_posten.append({"name": auswahl, "menge": menge, "preis": e_p, "einheit": einheit_str, "gesamt": menge * e_p})
                st.rerun()

    k_name = st.selectbox("Hof:", aktuelle_kunden) if aktuelle_kunden else st.text_input("Hofname:")
    rabatt = st.slider("Rabatt (%)", 0, 50, 0)
    
    col_m, col_j = st.columns(2)
    re_monat = col_m.selectbox("Monat:", LISTE_MONATE, key="re_m")
    re_jahr = col_j.number_input("Jahr:", min_value=1, value=1, key="re_j")

    if st.session_state.rechnungs_posten:
        st.write("---")
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        st.dataframe(df_preview[["name", "menge", "einheit", "gesamt"]], use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        st.metric("Gesamtbetrag (inkl. Rabatt)", f"{fmt_float(total)} EUR")
        
        full_ingame_date = f"J{re_jahr}-{re_monat}"
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt, st._global_finanzen["naechste_rechnung_id"], full_ingame_date)
        
        st.download_button("📥 PDF herunterladen", data=bytes(pdf_data), file_name=f"Rechnung_{k_name}.pdf", mime="application/pdf", use_container_width=True)
        if st.button("💾 Auf Server buchen", type="primary", use_container_width=True):
            st._global_finanzen["einnahmen"] += total
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_ingame_date, "Sort_Jahr": re_jahr, "Sort_Monat": re_monat,
                "Typ": "Einnahme", "Nummer": f"#RE-{st._global_finanzen['naechste_rechnung_id']:04d}",
                "Details": f"Kunde: {k_name}", "Betrag (EUR)": total
            })
            st._global_finanzen["naechste_rechnung_id"] += 1
            st.session_state.rechnungs_posten = []
            st.rerun()
        if st.button("🗑️ Liste leeren", use_container_width=True):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3 (SMARTPHONE-OPTIMIERT: Zeilen statt engen Spalten) ---
elif menu == "🛒 Material & Aufträge":
    st.title("🛒 Material & Aufträge")
    
    st.subheader("📦 Aktueller Hof-Bestand")
    
    # Auf Smartphones nutzen wir expander für die Eingabe, um vertikal Platz zu sparen
    with st.expander("✏️ Bestände bearbeiten / Verbräuche eintragen"):
        # Max. 2 Spalten nebeneinander für Mobile, sonst zerbricht das Layout
        c_edit1, c_edit2 = st.columns(2)
        v_saat = c_edit1.number_input("Saatgut (L):", min_value=0, value=int(st._global_lager_store["saat"]), step=500)
        v_kalk = c_edit2.number_input("Kalk (L):", min_value=0, value=int(st._global_lager_store["kalk"]), step=1000)
        v_dueng = c_edit1.number_input("Dünger (L):", min_value=0, value=int(st._global_lager_store["dueng"]), step=500)
        v_herbi = c_edit2.number_input("Herbizid (L):", min_value=0, value=int(st._global_lager_store.get("herbi", 2000)), step=500)
        v_diesel = c_edit1.number_input("Diesel (L):", min_value=0, value=int(st._global_lager_store.get("diesel", 5000)), step=500)
        
        if st.button("💾 Bestände aktualisieren", use_container_width=True):
            st._global_lager_store.update({"saat": v_saat, "kalk": v_kalk, "dueng": v_dueng, "herbi": v_herbi, "diesel": v_diesel})
            st.rerun()

    # Saubere, untereinander gelistete Statuskarten (perfekt lesbar auf dem Smartphone)
    def status_card(label, menge, limit):
        if menge < limit: st.error(f"🚨 {label}: {fmt_int(menge)} L (Kritisch!)")
        else: st.success(f"✅ {label}: {fmt_int(menge)} L")

    status_card("🌱 Saatgut", st._global_lager_store["saat"], 1500)
    status_card("⚪ Kalk", st._global_lager_store["kalk"], 5000)
    status_card("🧪 Dünger", st._global_lager_store["dueng"], 1000)
    status_card("🌿 Herbizid", st._global_lager_store["herbi"], 1000)
    status_card("⛽ Diesel", st._global_lager_store["diesel"], 1500)
            
    st.write("---")
    
    art = st.selectbox("Aktion wählen:", ["🌾 Lager auffüllen", "🚜 Dienstleistung beauftragen"])

    if art == "🚜 Dienstleistung beauftragen":
        lu_arbeit = st.text_input("Welche Arbeit?", placeholder="z.B. Mähen Feld 12")
        col_lu1, col_lu2 = st.columns(2)
        lu_einheit = col_lu1.selectbox("Einheit:", ["ha", "h"])
        lu_menge = col_lu2.number_input("Menge:", min_value=0.1, value=1.0)
        
        if st.button("📝 Auftrag listen", use_container_width=True):
            if lu_arbeit.strip():
                st._global_bestell_store.append({"artikel": f"LU: {lu_arbeit}", "menge": lu_menge, "einheit": lu_einheit})
                st.rerun()
    else:
        with st.expander("📉 Automatischer Vorschlag (Preise anpassen)"):
            c_p1, c_p2 = st.columns(2)
            p_saat = c_p1.number_input("Saatgut (€/1k L):", value=900)
            p_kalk = c_p2.number_input("Kalk (€/1k L):", value=150)
            p_dueng = c_p1.number_input("Dünger (€/1k L):", value=1200)
            p_herbi = c_p2.number_input("Herbizid (€/1k L):", value=1000)
            p_diesel = c_p1.number_input("Diesel (€/1k L):", value=1400)

            order_saat = st.number_input("Saatgut (L):", min_value=0, value=2000 if st._global_lager_store["saat"] < 1500 else 0)
            order_kalk = st.number_input("Kalk (L):", min_value=0, value=5000 if st._global_lager_store["kalk"] < 5000 else 0)
            order_dueng = st.number_input("Dünger (L):", min_value=0, value=1000 if st._global_lager_store["dueng"] < 1000 else 0)
            order_herbi = st.number_input("Herbizid (L):", min_value=0, value=1000 if st._global_lager_store["herbi"] < 1000 else 0)
            order_diesel = st.number_input("Diesel (L):", min_value=0, value=3000 if st._global_lager_store["diesel"] < 1500 else 0)
            
            if st.button("📝 Standardgüter hinzufügen", use_container_width=True):
                if order_saat > 0: st._global_bestell_store.append({"artikel": "Saatgut", "menge": order_saat, "einheit": "L"})
                if order_kalk > 0: st._global_bestell_store.append({"artikel": "Kalk", "menge": order_kalk, "einheit": "L"})
                if order_dueng > 0: st._global_bestell_store.append({"artikel": "Fluessigduenger", "menge": order_dueng, "einheit": "L"})
                if order_herbi > 0: st._global_bestell_store.append({"artikel": "Herbizid", "menge": order_herbi, "einheit": "L"})
                if order_diesel > 0: st._global_bestell_store.append({"artikel": "Diesel", "menge": order_diesel, "einheit": "L"})
                st.rerun()

    if st._global_bestell_store:
        st.write("---")
        st.subheader("📋 Offene Posten")
        df_b = pd.DataFrame(st._global_bestell_store)
        st.dataframe(df_b[["artikel", "menge", "einheit"]], use_container_width=True, hide_index=True)
        
        loesch_optionen = [f"{i+1}: {p['artikel']}" for i, p in enumerate(st._global_bestell_store)]
        p_del = st.selectbox("Posten löschen:", options=loesch_optionen)
        if st.button("❌ Löschen", use_container_width=True):
            st._global_bestell_store.pop(int(p_del.split(":")[0]) - 1)
            st.rerun()

        col_bm, col_bj = st.columns(2)
        bs_monat = col_bm.selectbox("Monat:", LISTE_MONATE, key="bs_m")
        bs_jahr = col_bj.number_input("Jahr:", min_value=1, value=1, key="bs_j")
        
        tatsaechliche_kosten = st.number_input("Gesamtkosten (€):", min_value=0.0)
        
        full_bs_date = f"J{bs_jahr}-{bs_monat}"
        if st.button("✅ Erledigt & Geld abziehen", type="primary", use_container_width=True):
            st._global_finanzen["ausgaben"] += tatsaechliche_kosten
            st._global_finanzen["historie"].append({
                "In-Game Datum": full_bs_date, "Sort_Jahr": bs_jahr, "Sort_Monat": bs_monat,
                "Typ": "Ausgabe", "Nummer": f"#BS-{st._global_finanzen['naechste_bestellung_id']:04d}",
                "Details": "Material/Auftrag eingekauft", "Betrag (EUR)": tatsaechliche_kosten
            })
            st._global_bestell_store = []
            st._global_finanzen["naechste_bestellung_id"] += 1
            st.rerun()

# --- SEITE 4 ---
elif menu == "🏭 Produktionen":
    st.title("🏭 Produktions-Planer")
    
    with st.container(border=True):
        rezept = st.selectbox("Rezept:", options=list(PROD_DATA.keys()))
        base_in, base_out, in_name, out_name = PROD_DATA[rezept] if rezept != "➕ Eigenes / Mod-Rezept" else (0,0,"","")
        
        monate = st.slider("Monate/Jahr aktiv:", 1, 12, 12)
        anzahl_fabriken = st.number_input("Linien:", min_value=1, value=1)
        
        if st.button("💾 Speichern & Synchronisieren", type="primary", use_container_width=True):
            st._global_hof_store.append({
                "name": rezept, "monate": monate, "linien": anzahl_fabriken,
                "in_typ": in_name, "in_menge": base_in * monate * anzahl_fabriken, 
                "out_typ": out_name, "out_menge": base_out * monate * anzahl_fabriken
            })
            st.rerun()

    if st._global_hof_store:
        st.write("---")
        for idx, item in enumerate(st._global_hof_store):
            st.info(f"""
            **{idx+1}. {item['name']}** ({item['linien']} Linien)
            * 📉 Bedarf: {fmt_int(item['in_menge'])} L {item['in_typ']}
            * 📈 Ertrag: {fmt_int(item['out_menge'])} L {item['out_typ']}
            """)
        if st.button("🗑️ Alle Produktionen löschen", use_container_width=True):
            st._global_hof_store = []
            st.rerun()

# --- BILANZ-HISTORIE AM ENDE (Kompakt gelistet) ---
if st._global_finanzen["historie"]:
    st.write("---")
    st.subheader("📊 In-Game Monatsberichte")
    df_raw = pd.DataFrame(st._global_finanzen["historie"])
    df_raw["Einnahme_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if r["Typ"] == "Einnahme" else 0.0, axis=1)
    df_raw["Ausgabe_Wert"] = df_raw.apply(lambda r: r["Betrag (EUR)"] if r["Typ"] == "Ausgabe" else 0.0, axis=1)
    
    df_monat = df_raw.groupby(["In-Game Datum", "Sort_Jahr", "Sort_Monat"]).agg(
        Einnahmen=("Einnahme_Wert", "sum"), Ausgaben=("Ausgabe_Wert", "sum")
    ).reset_index().sort_values(by=["Sort_Jahr", "Sort_Monat"])
    
    df_monat["Gewinn"] = df_monat["Einnahmen"] - df_monat["Ausgaben"]
    
    # Vereinfachte Tabelle für schnellen mobilen Blick
    st.dataframe(df_monat[["In-Game Datum", "Gewinn"]], use_container_width=True, hide_index=True)
