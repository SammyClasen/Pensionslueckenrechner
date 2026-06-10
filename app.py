import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# Konfiguration der Seite
st.set_page_config(page_title="Beamten-Pensionsrechner Pro", layout="wide")

# --- PDF GENERIERUNG (Sicher vor Sonderzeichen-Fehlern) ---
def create_pdf(res, logo_file):
    pdf = FPDF()
    pdf.add_page()
    
    if logo_file:
        logo_data = BytesIO(logo_file.getvalue())
        pdf.image(logo_data, x=150, y=10, w=40)
    
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "Individuelle Pensionsanalyse", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "", 12)
    for key, value in res.items():
        # Ersetze Umlaute und Euro fuer PDF-Kompatibilitaet
        safe_key = key.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
        safe_value = str(value).replace("€", "Euro")
        
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(85, 10, f"{safe_key}:", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 10, f"{safe_value}", border=0, ln=True)
    
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 9)
    pdf.multi_cell(0, 5, "Hinweis: Diese Berechnung stellt eine Schätzung dar (inkl. Abzug fuer Steuern/PKV). Keine Rechtsberatung.")
    return pdf.output()

# --- HAUPTPROGRAMM ---
st.title("?? Beamten-Pensionsrechner")
st.markdown("Berechnen Sie die voraussichtliche Pension und die monatliche Versorgungslücke.")

# Seitenleiste für Branding
with st.sidebar:
    st.header("Branding")
    uploaded_logo = st.file_uploader("Firmenlogo hochladen (PNG/JPG)", type=["png", "jpg", "jpeg"])
    st.info("Das Logo erscheint oben rechts im PDF-Protokoll.")

# Eingabe-Bereich
col_in, col_spacer, col_res = st.columns([4, 1, 6])

with col_in:
    st.subheader("Eingabedaten")
    brutto = st.number_input("Aktuelles Brutto (Vollzeit) in €", value=5000, step=100)
    eintritt = st.slider("Eintrittsalter", 18, 60, 28)
    tz_jahre = st.number_input("Jahre in Teilzeit", value=0, min_value=0, max_value=45)
    tz_quote = st.slider("Teilzeit-Quote (%)", 10, 100, 50) if tz_jahre > 0 else 100

# BERECHNUNGS-LOGIK
# 1,79375% pro Dienstjahr, max 71,75%
effektive_jahre = 67 - eintritt - tz_jahre + (tz_jahre * (tz_quote / 100))
pensionssatz = min(effektive_jahre * 1.79375, 71.75)
pensionssatz = max(pensionssatz, 35.0) # Mindestversorgung

brutto_pension = brutto * (pensionssatz / 100)
# Schaetzung: 72% vom Brutto bleiben nach Steuern und PKV
netto_pension = brutto_pension * 0.72 
netto_aktuell = brutto * 0.75
luecke = max(0.0, netto_aktuell - netto_pension)

ergebnisse = {
    "Dienstjahre (effektiv)": f"{effektive_jahre:.2f} Jahre",
    "Ruhegehaltssatz": f"{pensionssatz:.2f} %",
    "Erwartete Netto-Pension": f"{netto_pension:,.2f} €",
    "Aktuelles Netto (geschätzt)": f"{netto_aktuell:,.2f} €",
    "Monatliche Versorgungslücke": f"{luecke:,.2f} €"
}

# Anzeige-Bereich
with col_res:
    st.subheader("Ihre Analyse")
    
    m1, m2 = st.columns(2)
    m1.metric("Erwartete Pension (Netto)", f"{netto_pension:,.2f} €")
    m2.metric("Monatliche Lücke", f"{luecke:,.2f} €", delta=f"-{luecke:,.2f} €", delta_color="inverse")
    
    st.write(f"Ihr erreichter Pensionssatz: **{pensionssatz:.2f} %**")
    st.progress(pensionssatz / 71.75)
    
    st.write("---")
    st.subheader("Downloads")
    
    # PDF Button
    pdf_bytes = create_pdf(ergebnisse, uploaded_logo)
    st.download_button(
        label="?? PDF-Protokoll mit Logo",
        data=bytes(pdf_bytes),
        file_name="Pensionsanalyse.pdf",
        mime="application/pdf"
    )

    # Einfacher Excel-Export der Werte
    df_export = pd.DataFrame(list(ergebnisse.items()), columns=['Analysepunkt', 'Wert'])
    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
        df_export.to_excel(writer, index=False, sheet_name='Analyse')
    
    st.download_button(
        label="?? Excel-Daten exportieren",
        data=output_excel.getvalue(),
        file_name="Pensionsberechnung.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
