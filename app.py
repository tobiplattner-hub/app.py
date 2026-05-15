import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from fpdf import FPDF

# 1. Seiteneinstellungen
st.set_page_config(layout="centered", page_title="LS25 Hof-Manager", page_icon="🚜")

# --- GLOBALER SERVER-SPEICHER (FÜR ALLE SPIELER SYNCHRONISIERT) ---
if not hasattr(st, "_global_hof_store"):
    st._global_hof_store = []

# NEU: Globaler Speicher für Lagerbestände (Standardwerte, falls leer)
if not hasattr(st, "_global_lager_store"):
    st._global_lager_store = {"saat": 3000, "kalk": 10000, "dueng": 2000}

# NEU: Globaler Speicher für die Einkaufsliste / Bestellungen
if not hasattr(st, "_global_bestell_store"):
    st._global_bestell_store = []


# --- HILFSFUNKTIONEN FÜR FORMATIERUNG UND UMLAUTE ---
def safe_str(text):
    replacements = {'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue', 'ß': 'ss', '€': 'EUR'}
    txt = str(text)
    for r, v in replacements.items():
        txt = txt.replace(r, v)
    return txt

def fmt_int(wert):
    """Formatiert Ganzzahlen mit Punkt als Tausendertrenner (z.B. 10.000)"""
    return f"{wert:,.0f}".replace(",", ".")

def fmt_float(wert):
    """Formatiert Geldbeträge mit Punkt als Tausendertrenner und Komma als Dezimaltrenner (z.B. 1.250,50)"""
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

def generate_pdf(kunden_name, posten, rabatt_prozent):
    pdf = InvoicePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.multi_cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}\nRechnung-Nr: #{date.today().strftime('%Y%m%d')}-01", align="R")
    
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
        pdf.cell(30, 10, f"{p['std']} h", border=0, align="C")
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
    pdf.cell(0, 10, "Vielen Dank fuer die gute Zusammenarbeit! Der Betrag ist sofort faellig.", align="C")
    return pdf.output()

# NEU: Generiert PDF basierend auf den auf dem Server gespeicherten Bestellungen
def generate_order_pdf(bestell_liste):
    pdf = InvoicePDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_x(130)
    pdf.cell(65, 6, f"Datum: {date.today().strftime('%d.%m.%Y')}", align="R", ln=True)
    
    pdf.ln(35)
    pdf.set_x(65)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 15, "WARENBESTELLUNG", ln=True)
    
    pdf.ln(15)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(120, 10, "Artikel / Ware", border=0)
    pdf.cell(60, 10, "Bestellmenge (Liter)", border=0, align="R")
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Helvetica", size=11)
    
    for b in bestell_liste:
        pdf.cell(120, 10, safe_str(b["artikel"]), border=0)
        pdf.cell(60, 10, f"{fmt_int(b['menge'])} L", border=0, align="R")
        pdf.ln(10)
        
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 10, "Generiert ueber LS25 Hof-Manager. Bitte an den Landhandel uebermitteln.", align="C")
    return pdf.output()


# 2. Daten-Verbindung zu Google Sheets (Preise & Höfe)
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
    "Getreidemühle: Gerste zu Mehl": (36000, 27000, "Gerste", "Mehl"),
    "Bäckerei: Brot": (21600, 10800, "Mehl", "Brot"),
    "Bäckerei: Kuchen": (4320, 4320, "Mehl/Zucker/Milch/Eier/Erdbeeren (Mix)", "Kuchen"),
    "Ölmühle: Sonnenblumenöl": (14400, 7200, "Sonnenblumen", "Sonnenblumenöl"),
    "Ölmühle: Rapsöl": (14400, 7200, "Raps", "Rapsöl"),
    "Molkerei: Butter": (36000, 21600, "Milch", "Butter"),
    "Molkerei: Käse": (21600, 16200, "Milch", "Käse"),
    "Zuckerfabrik: Zuckerrohr": (28800, 28800, "Zuckerrohr", "Zucker"),
    "Zuckerfabrik: Zuckerrüben": (14400, 7200, "Zuckerrüben", "Zucker"),
    "➕ Eigenes / Mod-Rezept hinzufügen": (0, 0, "", "")
}

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["💰 Ernte & Felder", "📋 Rechnungs-Ersteller", "🛒 Saatgut-Bestellung", "🏭 Produktions-Planer"])

# --- SEITE 1 ---
if menu == "💰 Ernte & Felder":
    st.title("🚜 Ernte- & Feld-Manager")
    with st.expander("⚙️ Verbrauchs-Raten anpassen (pro Hektar)"):
        col_r1, col_r2, col_r3 = st.columns(3)
        r_kalk = col_r1.number_input("Kalk (L/ha):", value=2000)
        r_duenger = col_r2.number_input("Dünger (L/ha):", value=160)
        r_saat = col_r3.number_input("Saatgut (L/ha):", value=150)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🧪 Bedarfskalkulation")
        ha = st.number_input("Hektar (ha):", min_value=0.1, value=1.0, step=0.1)
        st.info(f"""
        **Benötigte Mengen für {ha} ha:**
        * Kalk: **{fmt_int(ha * r_kalk)} L**
        * Dünger: **{fmt_int(ha * r_duenger)} L**
        * Saatgut: **{fmt_int(ha * r_saat)} L**
        """)
    with col2:
        st.subheader("Erloesrechner")
        menge = st.number_input("Liter im Silo:", value=10000)
        preis_pro_1000 = st.number_input("EUR pro 1000L:", value=1200)
        erloes = (menge / 1000) * preis_pro_1000
        st.success(f"**Voraussichtlicher Erloes:**\n### {fmt_float(erloes)} EUR")

# --- SEITE 2 ---
elif menu == "📋 Rechnungs-Ersteller":
    st.title("📋 Rechnungs-Ersteller")
    with st.container(border=True):
        c1, c2, c3 = st.columns([2, 1, 1])
        auswahl = c1.selectbox("Maschine:", options=list(preis_dict.keys()) if preis_dict else ["-"])
        std = c2.number_input("Stunden:", min_value=0.1, value=1.0, step=0.1)
        e_p = c3.number_input("Preis (EUR/h):", value=float(preis_dict.get(auswahl, 0.0)))
        if st.button("➕ Hinzufuegen"):
            st.session_state.rechnungs_posten.append({"name": auswahl, "std": std, "preis": e_p, "gesamt": std * e_p})
            st.rerun()

    ck1, ck2 = st.columns(2)
    k_name = ck1.selectbox("Hof auswählen:", aktuelle_kunden) if aktuelle_kunden else ck1.text_input("Hofname:")
    rabatt = ck2.slider("Rabatt (%)", 0, 50, 0)

    if st.session_state.rechnungs_posten:
        st.write("---")
        st.subheader("📋 Aktuelle Posten")
        
        df_preview = pd.DataFrame(st.session_state.rechnungs_posten)
        df_preview.columns = ["Maschine", "Stunden", "Einzelpreis (EUR)", "Gesamt (EUR)"]
        st.dataframe(df_preview, use_container_width=True, hide_index=True)
        
        summe = sum(p['gesamt'] for p in st.session_state.rechnungs_posten)
        total = summe * (1 - rabatt/100)
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Zwischensumme", f"{fmt_float(summe)} EUR")
        col_m2.metric("Endbetrag", f"{fmt_float(total)} EUR")

        st.write("")
        col_b1, col_b2 = st.columns(2)
        pdf_data = generate_pdf(k_name, st.session_state.rechnungs_posten, rabatt)
        
        col_b1.download_button(
            label="📥 Rechnung als PDF herunterladen",
            data=bytes(pdf_data),
            file_name=f"Rechnung_{safe_str(k_name)}_{date.today().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        if col_b2.button("🗑️ Rechnung leeren"):
            st.session_state.rechnungs_posten = []
            st.rerun()

# --- SEITE 3: NEU MIT SERVER-SYNCHRONISATION ---
elif menu == "🛒 Saatgut-Bestellung":
    st.title("🛒 Material- & Lagerverwaltung")
    st.write("Diese Bestände und die Einkaufsliste sind **live für alle Spieler synchronisiert**.")
    
    if st.button("🔄 Bestände & Einkaufsliste aktualisieren"):
        st.rerun()
        
    st.subheader("📦 Aktueller Hof-Bestand (Server)")
    col_s, col_k, col_d = st.columns(3)
    
    # Zustand wird jetzt direkt im globalen Server-Dict gespeichert und editiert
    with col_s:
        st.markdown("### 🌱 Saatgut")
        v_saat = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["saat"]), step=500, key="nb_saat")
        g_saat = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_saat")
        b_saat = v_saat - g_saat
        st._global_lager_store["saat"] = b_saat # Auf Server sichern
        if b_saat < 1500: st.error(f"🚨 Kritisch: {fmt_int(b_saat)} L\n(Unter 1.500 L)")
        else: st.success(f"✅ Stabil: {fmt_int(b_saat)} L")
            
    with col_k:
        st.markdown("### ⚪ Kalk")
        v_kalk = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["kalk"]), step=1000, key="nb_kalk")
        g_kalk = st.number_input("Verbraucht (L):", min_value=0, value=0, step=500, key="g_kalk")
        b_kalk = v_kalk - g_kalk
        st._global_lager_store["kalk"] = b_kalk # Auf Server sichern
        if b_kalk < 5000: st.error(f"🚨 Kritisch: {fmt_int(b_kalk)} L\n(Unter 5.000 L)")
        else: st.success(f"✅ Stabil: {fmt_int(b_kalk)} L")
            
    with col_d:
        st.markdown("### 🧪 Flüssigdünger")
        v_dueng = st.number_input("Vorhanden (L):", min_value=0, value=int(st._global_lager_store["dueng"]), step=500, key="nb_dueng")
        g_dueng = st.number_input("Verbraucht (L):", min_value=0, value=0, step=100, key="g_dueng")
        b_dueng = v_dueng - g_dueng
        st._global_lager_store["dueng"] = b_dueng # Auf Server sichern
        if b_dueng < 1000: st.error(f"🚨 Kritisch: {fmt_int(b_dueng)} L\n(Unter 1.000 L)")
        else: st.success(f"✅ Stabil: {fmt_int(b_dueng)} L")
            
    st.write("---")
    
    # Sektion: Nachbestellungen aufgeben (Schreibt direkt auf den Server)
    if b_saat < 1500 or b_kalk < 5000 or b_dueng < 1000:
        st.subheader("🛒 Artikel auf Server-Einkaufsliste setzen")
        col_b1, col_b2 = st.columns(2)
        init_saat = 2000 if b_saat < 1500 else 0
        order_saat = col_b1.number_input("Saatgut Menge (Liter):", min_value=0, value=init_saat, step=500)
        b_typ = col_b2.text_input("Fruchtsorte (z.B. Weizen, Raps):", value="")
        
        col_b3, col_b4 = st.columns(2)
        init_kalk = 5000 if b_kalk < 5000 else 0
        order_kalk = col_b3.number_input("Kalk Menge (Liter):", min_value=0, value=init_kalk, step=1000)
        init_dueng = 1000 if b_dueng < 1000 else 0
        order_dueng = col_b4.number_input("Flüssigdünger Menge (Liter):", min_value=0, value=init_dueng, step=500)
        
        if st.button("📝 Auf gemeinsame Einkaufsliste setzen", type="primary"):
            if order_saat > 0:
                art = f"Saatgut ({b_typ})" if b_typ else "Saatgut"
                st._global_bestell_store.append({"artikel": art, "menge": order_saat})
            if order_kalk > 0:
                st._global_bestell_store.append({"artikel": "Kalk", "menge": order_kalk})
            if order_dueng > 0:
                st._global_bestell_store.append({"artikel": "Fluessigduenger", "menge": order_dueng})
            st.success("Erfolgreich zur Server-Einkaufsliste hinzugefügt!")
            st.rerun()
    else:
        st.info("ℹ️ Die Bestellfunktion schaltet sich automatisch frei, sobald ein Bestand unter das Limit rutscht.")

    # Sektion: Anzeige der globalen Bestellungen & PDF Export
    if st._global_bestell_store:
        st.write("---")
        st.subheader("📋 Offene Bestellungen auf dem Server")
        
        df_bestellungen = pd.DataFrame(st._global_bestell_store)
        df_bestellungen.columns = ["Artikel / Ware", "Bestellmenge (Liter)"]
        st.dataframe(df_bestellungen, use_container_width=True, hide_index=True)
        
        col_btn1, col_btn2 = st.columns(2)
        
        order_pdf_data = generate_order_pdf(st._global_bestell_store)
        col_btn1.download_button(
            label="📥 Bestellzettel (Gesamt) als PDF laden", 
            data=bytes(order_pdf_data), 
            file_name=f"Hof_Bestellung_{date.today().strftime('%Y%m%d')}.pdf", 
            mime="application/pdf"
        )
        
        if col_btn2.button("✅ Einkäufe erledigt (Liste leeren)"):
            st._global_bestell_store = []
            st.success("Einkaufsliste wurde erfolgreich geleert!")
            st.rerun()

# --- SEITE 4: PRODUKTIONS-PLANER (LIVE SERVER SPEICHER) ---
elif menu == "🏭 Produktions-Planer":
    st.title("🏭 LS-Produktionsketten Rechner")
    st.write("Füge hier deine Fabriken hinzu. Diese Liste wird **live mit allen Spielern auf dem Hof synchronisiert**!")
    
    if st.button("🔄 Server-Liste aktualisieren"):
        st.rerun()

    with st.container(border=True):
        st.subheader("🏭 Neue Produktion hinzufügen")
        rezept = st.selectbox("Wähle eine Produktion/Rezept aus:", options=list(PROD_DATA.keys()))
        
        if rezept == "➕ Eigenes / Mod-Rezept hinzufügen":
            st.write("---")
            col_custom1, col_custom2 = st.columns(2)
            in_name = col_custom1.text_input("Name des Rohstoffs (Input):", value="Dinkel")
            out_name = col_custom2.text_input("Name des Produkts (Output):", value="Altes Mehl")
            
            col_custom3, col_custom4, col_custom5 = st.columns(3)
            custom_in_menge = col_custom3.number_input(f"Menge pro Zyklus:", min_value=1, value=5)
            custom_out_menge = col_custom4.number_input(f"Menge pro Zyklus:", min_value=1, value=4)
            zyklen_pro_std = col_custom5.number_input("Zyklen pro Stunde:", min_value=1, value=30)
            
            base_in = custom_in_menge * zyklen_pro_std * 24 * 30
            base_out = custom_out_menge * zyklen_pro_std * 24 * 30
            name_anzeige = f"Mod-Rezept: {in_name} -> {out_name}"
        else:
            base_in, base_out, in_name, out_name = PROD_DATA[rezept]
            name_anzeige = rezept
            
        col_time1, col_time2 = st.columns(2)
        monate = col_time1.slider("Betriebsdauer im Jahr (Monate):", min_value=1, max_value=12, value=12, key="prod_monate")
        anzahl_fabriken = col_time2.number_input("Anzahl Linien / Fabriken:", min_value=1, value=1, step=1, key="prod_anzahl")
        
        if st.button("💾 Für ALLE speichern & synchronisieren", type="primary"):
            gesamt_input = base_in * monate * anzahl_fabriken
            gesamt_output = base_out * monate * anzahl_fabriken
            
            st._global_hof_store.append({
                "name": name_anzeige,
                "monate": monate,
                "linien": anzahl_fabriken,
                "in_typ": in_name,
                "in_menge": gesamt_input,
                "out_typ": out_name,
                "out_menge": gesamt_output
            })
            st.success(f"✅ {name_anzeige} wurde für alle Spieler gespeichert!")
            st.rerun()

    if st._global_hof_store:
        st.write("---")
        st.header("🏡 Aktive Produktionen auf dem Server")
        
        table_data = []
        for idx, item in enumerate(st._global_hof_store):
            table_data.append({
                "ID": idx + 1,
                "Produktion / Fabrik": item["name"],
                "Linien": item["linien"],
                "Laufzeit": f"{item['monate']} Monate",
                "Rohstoff Bedarf (Jahr)": f"{fmt_int(item['in_menge'])} L ({item['in_typ']})",
                "Produkt Ertrag (Jahr)": f"{fmt_int(item['out_menge'])} L ({item['out_typ']})"
            })
            
        df_prods = pd.DataFrame(table_data)
        st.dataframe(df_prods, use_container_width=True, hide_index=True)
        
        col_action1, col_action2 = st.columns(2)
        
        json_data = json.dumps(st._global_hof_store, indent=4)
        col_action1.download_button(
            label="📥 Server-Planung als Datei sichern",
            data=json_data,
            file_name=f"LS25_Hofplan_{date.today().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
        
        if col_action2.button("🗑️ Alle Produktionen vom Server löschen"):
            st._global_hof_store = []
            st.warning("Die globale Liste wurde für alle Spieler geleert.")
            st.rerun()
            
        st.write("---")
        st.subheader("📊 Logistik & Jahres-Ernteziele (Gesamt)")
        
        bedarf_dict = {}
        ertrag_dict = {}
        
        for p in st._global_hof_store:
            bedarf_dict[p['in_typ']] = bedarf_dict.get(p['in_typ'], 0) + p['in_menge']
            ertrag_dict[p['out_typ']] = ertrag_dict.get(p['out_typ'], 0) + p['out_menge']
            
        col_summary1, col_summary2 = st.columns(2)
        
        with col_summary1:
            st.markdown("#### 🌾 Benötigte Rohstoffe (Gesamtbedarf):")
            for stoff, menge in bedarf_dict.items():
                st.info(f"**{stoff}**:\n### {fmt_int(menge)} Liter")
                
        with col_summary2:
            st.markdown("#### 📦 Produzierte Endwaren (Gesamtertrag):")
            for ware, menge in ertrag_dict.items():
                st.success(f"**{ware}**:\n### {fmt_int(menge)} Liter / Einheiten")
                
    st.write("---")
    with st.expander("📤 Gesicherte Planung/Backup auf Server laden"):
        uploaded_file = st.file_uploader("Lade eine .json Datei hoch:", type="json")
        if uploaded_file is not None:
            try:
                st._global_hof_store = json.load(uploaded_file)
                st.success("✅ Planung erfolgreich hochgeladen und für alle synchronisiert!")
                st.rerun()
            except:
                st.error("Fehler beim Lesen der Backup-Datei.")
