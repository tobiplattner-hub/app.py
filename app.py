import streamlit as st
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# ---------------------------------------------------------
# SETUP & STATEMANAGEMENT (GLOBALER SERVER-SPEICHER)
# ---------------------------------------------------------
st.set_page_config(page_title="Agrar-Abrechnung", layout="wide")

# Initialisiere den globalen Speicher auf dem Server, falls noch nicht geschehen
if not hasattr(st, "_global_felder_store"):
    st._global_felder_store = []

# Lokaler Session State für das aktuell bearbeitete Feld
if "aktuelles_feld" not in st.session_state:
    st.session_state.aktuelles_feld = {
        "bezeichnung": "",
        "groesse": 0.0,
        "massnahmen": []
    }

# ---------------------------------------------------------
# STYLING & FORMATIERUNG
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main .block-container { padding-top: 2rem; }
    .stButton>button { width: 100%; border-radius: 5px; }
    div.data-block {
        border: 1px solid #ddd;
        padding: 15px;
        border-radius: 8px;
        background-color: #f9f9f9;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

def fmt_float(wert):
    """Formatiert Zahlen ins deutsche Format (z.B. 1.250,50)"""
    if isinstance(wert, str):
        return wert
    try:
        return f"{wert:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(wert)

# ---------------------------------------------------------
# HILFSFUNKTIONEN FÜR BERECHNUNGEN
# ---------------------------------------------------------
def berechne_massnahme_summe(m):
    typ = m.get("typ", "Pauschal")
    if typ == "Pro ha":
        return m.get("preis_ha", 0.0) * m.get("groesse_ref", 0.0)
    elif typ == "Pro Einheit":
        return m.get("preis_einheit", 0.0) * m.get("menge", 0.0)
    else:  # Pauschal
        return m.get("pauschalpreis", 0.0)

def berechne_feld_gesamtsumme(feld):
    return sum(berechne_massnahme_summe(m) for m in feld.get("massnahmen", []))

# ---------------------------------------------------------
# PDF GENERATOR
# ---------------------------------------------------------
def erstelle_pdf(rechnungsdaten, felder):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=22, spaceAfter=20, textColor=colors.HexColor("#1b4332"))
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#2d6a4f"))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14)
    bold_body = ParagraphStyle('BoldBody', parent=body_style, fontName='Helvetica-Bold')
    
    # Header: Absender & Empfänger
    header_data = [
        [Paragraph(f"<b>Dienstleister:</b><br/>{rechnungsdaten['absender']}", body_style),
         Paragraph(f"<b>Kunde / Auftraggeber:</b><br/>{rechnungsdaten['empfaenger']}", body_style)]
    ]
    t_header = Table(header_data, colWidths=[260, 260])
    t_header.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(t_header)
    story.append(Spacer(1, 25))
    
    # Titel & Metadaten
    story.append(Paragraph(f"Rechnung Nr. {rechnungsdaten['rechnungsnummer']}", title_style))
    meta_data = [
        [Paragraph(f"<b>Datum:</b> {rechnungsdaten['datum']}", body_style),
         Paragraph(f"<b>Leistungszeitraum:</b> {rechnungsdaten['zeitraum']}", body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[260, 260])
    story.append(t_meta)
    story.append(Spacer(1, 20))
    
    gesamtbrutto_alle_felder = 0.0
    
    # Schleife über alle Felder
    for idx, f in enumerate(felder):
        story.append(Paragraph(f"{idx+1}. Feld: {f['bezeichnung']} ({fmt_float(f['groesse'])} ha)", h2_style))
        
        # Tabelle für Maßnahmen dieses Feldes
        tbl_data = [[
            Paragraph("<b>Maßnahme / Leistung</b>", body_style),
            Paragraph("<b>Berechnungstyp</b>", body_style),
            Paragraph("<b>Ansatz / Menge</b>", body_style),
            Paragraph("<b>Betrag (€)</b>", body_style)
        ]]
        
        for m in f.get("massnahmen", []):
            typ = m.get("typ", "Pauschal")
            if typ == "Pro ha":
                ansatz = f"{fmt_float(m['preis_ha'])} €/ha × {fmt_float(m['groesse_ref'])} ha"
            elif typ == "Pro Einheit":
                ansatz = f"{fmt_float(m['preis_einheit'])} €/Einh. × {fmt_float(m['menge'])} {m['einheit_name']}"
            else:
                ansatz = f"Pauschal: {fmt_float(m['pauschalpreis'])} €"
                
            subtotal = berechne_massnahme_summe(m)
            
            tbl_data.append([
                Paragraph(m.get("name", ""), body_style),
                Paragraph(typ, body_style),
                Paragraph(ansatz, body_style),
                Paragraph(f"{fmt_float(subtotal)} €", body_style)
            ])
            
        feld_summe = berechne_feld_gesamtsumme(f)
        gesamtbrutto_alle_felder += feld_summe
        
        # Zeile für Feld-Gesamtsumme hinzufügen
        tbl_data.append([
            Paragraph(f"<b>Zwischensumme {f['bezeichnung']}:</b>", bold_body),
            "", "",
            Paragraph(f"<b>{fmt_float(feld_summe)} €</b>", bold_body)
        ])
        
        t_tbl = Table(tbl_data, colWidths=[180, 90, 150, 100])
        t_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2eafc")),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-2), 0.5, colors.lightgrey),
            ('LINEABOVE', (0,-1), (-1,-1), 1, colors.HexColor("#2d6a4f")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT')
        ]))
        story.append(t_tbl)
        story.append(Spacer(1, 15))
        
    story.append(Spacer(1, 15))
    
    # Abschluss-Berechnung (Steuer)
    st_satz = rechnungsdaten.get("steuersatz", 0.0)
    if st_satz > 0:
        netto = gesamtbrutto_alle_felder / (1 + (st_satz / 100))
        steuer_betrag = gesamtbrutto_alle_felder - netto
    else:
        netto = gesamtbrutto_alle_felder
        steuer_betrag = 0.0
        
    summary_data = [
        [Paragraph("<b>Gesamtsumme Netto:</b>", body_style), Paragraph(f"{fmt_float(netto)} €", body_style)],
        [Paragraph(f"<b>zzgl. {st_satz}% MwSt:</b>", body_style), Paragraph(f"{fmt_float(steuer_betrag)} €", body_style)],
        [Paragraph("<b>Rechnungsbetrag (Brutto):</b>", bold_body), Paragraph(f"<b>{fmt_float(gesamtbrutto_alle_felder)} €</b>", bold_body)]
    ]
    t_summary = Table(summary_data, colWidths=[150, 100])
    t_summary.setStyle(TableStyle([
        ('ALIGN', (1,0), (1,-1), 'RIGHT'),
        ('LINEABOVE', (0,2), (1,2), 1, colors.black),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    
    # Rechtsbündige Platzierung der Endsumme mittels einer Hilfstabelle
    wrapper_data = [["", t_summary]]
    t_wrapper = Table(wrapper_data, colWidths=[270, 250])
    story.append(t_wrapper)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# ---------------------------------------------------------
# OBERFLÄCHE / APP-STRUKTUR
# ---------------------------------------------------------
st.title("🚜 Agrardienstleistungen Abrechnungs-Zentrum")
st.subheader("Erfassen Sie feldbasierte Leistungen und erstellen Sie GoBD-konforme PDF-Rechnungen")

tab1, tab2 = st.tabs(["🌾 1. Felder & Maßnahmen erfassen", "📄 2. Rechnungsdaten & PDF erzeugen"])

# ---------------------------------------------------------
# TAB 1: DATENERFASSUNG (FELDER & MASSNAHMEN)
# ---------------------------------------------------------
with tab1:
    st.header("Schritt 1: Felder und zugehörige Arbeiten eintragen")
    
    col_f1, col_f2 = st.columns([1, 2])
    
    with col_f1:
        st.markdown("<div class='data-block'>", unsafe_allow_html=True)
        st.subheader("Aktuelles Feld")
        
        f_bez = st.text_input("Feld-/Schlagbezeichnung", value=st.session_state.aktuelles_feld["bezeichnung"], key="input_f_bez")
        f_groesse = st.number_input("Größe (in ha)", min_value=0.0, step=0.1, value=st.session_state.aktuelles_feld["groesse"], key="input_f_groesse")
        
        # Statemanagement synchronisieren
        st.session_state.aktuelles_feld["bezeichnung"] = f_bez
        st.session_state.aktuelles_feld["groesse"] = f_groesse
        
        st.markdown("---")
        st.subheader("Arbeit / Maßnahme hinzufügen")
        
        m_name = st.text_input("Name der Maßnahme", placeholder="z.B. Mähen, Grubbern, Pflanzenschutz")
        m_typ = st.selectbox("Abrechnungs-Modus", ["Pro ha", "Pro Einheit", "Pauschal"])
        
        m_daten = {"name": m_name, "typ": m_typ}
        
        if m_typ == "Pro ha":
            m_daten["preis_ha"] = st.number_input("Preis pro Hektar (€/ha)", min_value=0.0, step=1.0)
            m_daten["groesse_ref"] = st.number_input("Zu bearbeitende Fläche (ha)", min_value=0.0, max_value=f_groesse if f_groesse > 0 else 1000.0, value=f_groesse, step=0.1)
        elif m_typ == "Pro Einheit":
            m_daten["einheit_name"] = st.text_input("Einheit Name", value="Std")
            m_daten["preis_einheit"] = st.number_input("Preis pro Einheit (€)", min_value=0.0, step=1.0)
            m_daten["menge"] = st.number_input("Menge / Anzahl Einheiten", min_value=0.0, step=0.5)
        else:
            m_daten["pauschalpreis"] = st.number_input("Pauschalpreis (€)", min_value=0.0, step=5.0)
            
        if st.button("➕ Maßnahme dem Feld hinzufügen"):
            if not m_name:
                st.error("Bitte geben Sie einen Namen für die Maßnahme ein.")
            else:
                st.session_state.aktuelles_feld["massnahmen"].append(m_daten)
                st.success(f"Maßnahme '{m_name}' temporär vorgemerkt.")
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_f2:
        st.subheader("Vorschau des aktuellen Feldes")
        if st.session_state.aktuelles_feld["bezeichnung"]:
            st.info(f"**Feld:** {st.session_state.aktuelles_feld['bezeichnung']} | **Größe:** {fmt_float(st.session_state.aktuelles_feld['groesse'])} ha")
        else:
            st.warning("Noch kein Feld benannt.")
            
        if st.session_state.aktuelles_feld["massnahmen"]:
            for i, m in enumerate(st.session_state.aktuelles_feld["massnahmen"]):
                col_m1, col_m2 = st.columns([4, 1])
                with col_m1:
                    st.text(f" - {m['name']} ({m['typ']}) -> Summe: {fmt_float(berechne_massnahme_summe(m))} €")
                with col_m2:
                    if st.button("🗑️", key=f"del_m_{i}"):
                        st.session_state.aktuelles_feld["massnahmen"].pop(i)
                        st.rerun()
            st.markdown(f"**Voraussichtliche Feldsumme:** {fmt_float(berechne_feld_gesamtsumme(st.session_state.aktuelles_feld))} €")
        else:
            st.write("Noch keine Maßnahmen für dieses Feld hinzugefügt.")
            
        st.markdown("---")
        if st.button("💾 KOMPLETTES FELD SPEICHERN (In globale Liste übertragen)"):
            if not st.session_state.aktuelles_feld["bezeichnung"] or st.session_state.aktuelles_feld["groesse"] <= 0:
                st.error("Feldbezeichnung fehlt oder Größe ist 0.")
            elif not st.session_state.aktuelles_feld["massnahmen"]:
                st.error("Bitte fügen Sie mindestens eine Maßnahme hinzu, bevor Sie das Feld speichern.")
            else:
                st._global_felder_store.append(st.session_state.aktuelles_feld)
                st.session_state.aktuelles_feld = {"bezeichnung": "", "groesse": 0.0, "massnahmen": []}
                st.success("Feld erfolgreich gesichert!")
                st.rerun()

    # ---------------------------------------------------------
    # ÜBERSICHT ALLER BEREITS GESPEICHERTEN FELDER
    # ---------------------------------------------------------
    st.markdown("<br/><hr/>", unsafe_allow_html=True)
    st.header("🗂️ Bereits gespeicherte Felder im aktuellen Server-Lauf")
    
    if st._global_felder_store:
        # HIER WAR DER FEHLER: .get() sichert gegen alte, inkompatible Datenstrukturen ab
        ges_ha = sum(f.get("groesse", 0.0) for f in st._global_felder_store)
        ges_eur = sum(berechne_feld_gesamtsumme(f) for f in st._global_felder_store)
        
        st.metric(label="Anzahl Felder", value=len(st._global_felder_store), delta=f"{fmt_float(ges_ha)} ha Gesamtfläche")
        st.metric(label="Gesamtwert aller Felder (Brutto)", value=f"{fmt_float(ges_eur)} €")
        
        for idx, f in enumerate(st._global_felder_store):
            with st.expander(f"Feld {idx+1}: {f.get('bezeichnung', 'Unbekannt')} ({fmt_float(f.get('groesse', 0.0))} ha) - Gesamt: {fmt_float(berechne_feld_gesamtsumme(f))} €"):
                for m in f.get("massnahmen", []):
                    st.write(f"• {m.get('name')} ({m.get('typ')}) : {fmt_float(berechne_massnahme_summe(m))} €")
                if st.button("Feld komplett löschen", key=f"del_f_{idx}"):
                    st._global_felder_store.pop(idx)
                    st.rerun()
                    
        if st.button("🛑 RECHNUNGSLISTE VOLLSTÄNDIG LEEREN (Reset)"):
            st._global_felder_store = []
            st.rerun()
    else:
        st.info("Der globale Speicher ist leer. Bitte erfassen Sie ein Feld und klicken Sie auf 'Komplettes Feld speichern'.")

# ---------------------------------------------------------
# TAB 2: RECHNUNGSGENERIERUNG (PDF)
# ---------------------------------------------------------
with tab2:
    st.header("Schritt 2: Rechnungsdetails & PDF-Erzeugung")
    
    if not st._global_felder_store:
        st.warning("Sie müssen zuerst in Tab 1 Felder erfassen und speichern, bevor Sie eine Rechnung erstellen können.")
    else:
        col_r1, col_r2 = st.columns(2)
        
        with col_r1:
            st.subheader("Stammdaten & Belegdetails")
            r_num = st.text_input("Rechnungsnummer", value="RE-2026-001")
            r_datum = st.text_input("Rechnungsdatum", value="16.05.2026")
            r_zeitraum = st.text_input("Leistungszeitraum", value="Frühjahr 2026")
            r_steuer = st.slider("Enthaltener Mehrwertsteuersatz (%)", min_value=0, max_value=25, value=19, step=1)
            
        with col_r2:
            st.subheader("Adressaten")
            r_absender = st.text_area("Ihr Betrieb (Absender / Rechnungssteller)", 
                                      value="Agrarservice Musterstadt GmbH\nFeldweg 12\n12345 Musterstadt\nUSt-IdNr: DE 987654321")
            r_empfaenger = st.text_area("Kunde (Empfänger)", 
                                        value="Landwirtschaftsbetrieb Groß-Hof\nAn den Eichen 1\n12345 Musterstadt")
            
        rechnungsdaten = {
            "rechnungsnummer": r_num,
            "datum": r_datum,
            "zeitraum": r_zeitraum,
            "steuersatz": r_steuer,
            "absender": r_absender.replace("\n", "<br/>"),
            "empfaenger": r_empfaenger.replace("\n", "<br/>")
        }
        
        st.markdown("---")
        st.subheader("PDF generieren und abschließen")
        
        try:
            pdf_data = erstelle_pdf(rechnungsdaten, st._global_felder_store)
            
            st.success("PDF wurde fehlerfrei im Arbeitsspeicher generiert!")
            st.download_button(
                label="📥 Professionelle Rechnung als PDF herunterladen",
                data=pdf_data,
                file_name=f"Rechnung_{r_num}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Fehler bei der PDF-Erstellung: {str(e)}")
