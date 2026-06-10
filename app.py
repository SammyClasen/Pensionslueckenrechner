import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Makler-Pensionsrechner Pro", layout="wide")

# --- LOGO UPLOAD ---
with st.sidebar:
    st.header("Branding")
    uploaded_logo = st.file_uploader("Dein Firmenlogo hochladen (PNG/JPG)", type=["png", "jpg", "jpeg"])

# --- PDF GENERIERUNG MIT LOGO ---
def create_pdf(res, logo_file):
    pdf = FPDF()
    pdf.add_page()
    
    # Logo einbinden, wenn vorhanden
    if logo_file:
        # Streamlit-Upload in temporäre Datei oder Bytes umwandeln
        logo_data = BytesIO(logo_file.getvalue())
        pdf.image(logo_data, x=150, y=10, w=40) # Position: oben rechts
    
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(31, 73, 125) # Dunkelblau
    pdf.cell(0, 15, "Individuelle Pensionsanalyse", ln=True)
    
    pdf.set_draw_color(31, 73, 125)
    pdf.line(10, 30, 200, 30) # Trennlinie
    pdf.ln(15)
    
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    for key, value in res.items():
        pdf.set_font("Arial", "B", 11)
        pdf.cell(80, 10, f"{key}:", border=0)
        pdf.set_font("Arial", "", 11)
        pdf.cell(0, 10, f"{value}", border=0, ln=True)
    
    pdf.ln(20)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, "Rechtlicher Hinweis: Diese Berechnung basiert auf den aktuellen Versorgungssätzen von 1,79375% pro Dienstjahr und einem pauschalen Abzug für Steuern/PKV. Sie dient rein zur Illustration.")
    
    return pdf.output()

# --- LOGIK & EINGABE ---
st.title("?? Beamten-Pensionsrechner für Profis")

col1, col2 = st.columns([1, 1])

with col1:
    brutto = st.number_input("Aktuelles Brutto (Vollzeit) in €", value=5000)
    eintritt = st.number_input("Eintrittsalter", value=28)
    tz_jahre = st.number_input("Teilzeit-Jahre gesamt", value=5)
    tz_quote = st.slider("Mittlere Teilzeit-Quote (%)", 10, 100, 50)

# Berechnungen
dienstjahre = 67 - eintritt - tz_jahre + (tz_jahre * (tz_quote / 100))
satz = min(dienstjahre * 1.79375, 71.75)
netto_pension = (brutto * (satz / 100)) * 0.72
netto_aktuell = brutto * 0.75
luecke = max(0.0, netto_aktuell - netto_pension)

ergebnisse = {
    "Dienstjahre (berechnet)": f"{dienstjahre:.2f} Jahre",
    "Ruhegehaltssatz": f"{satz:.2f} %",
    "Voraussichtliche Pension (Netto)": f"{netto_pension:,.2f} €",
    "Netto-Einkommen (Aktuell)": f"{netto_aktuell:,.2f} €",
    "Monatliche Versorgungslücke": f"{luecke:,.2f} €"
}

with col2:
    st.subheader("Analyse-Ergebnis")
    st.metric("Pensionslücke", f"{luecke:,.2f} €", delta="- Monatlich", delta_color="inverse")
    
    # Download Sektion
    st.write("### Dokumente generieren")
    
    pdf_data = create_pdf(ergebnisse, uploaded_logo)
    st.download_button("?? PDF mit Logo herunterladen", data=bytes(pdf_data), file_name="Versorgungsanalyse.pdf", mime="application/pdf")
    
    # Button für Excel (hier könntest du die Funktion aus der vorigen Antwort einbinden)
    st.button("?? Excel-Rechner generieren (Vorschau)")
