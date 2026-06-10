import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# Konfiguration
st.set_page_config(page_title="Beamten-Pensionsrechner 2026 Pro", layout="wide")

# --- DATEN-LOADER ---
@st.cache_data
def load_besoldung():
    try:
        # Liest die CSV ein
        return pd.read_csv("besoldung.csv", sep=";", encoding="utf-8")
    except Exception as e:
        st.error(f"Fehler beim Laden der besoldung.csv: {e}")
        return pd.DataFrame()

df_besoldung = load_besoldung()

# Altersgrenzen nach Berufsgruppe
BERUFSGRUPPEN = {
    "Allgemeine Verwaltung": 67,
    "Polizeivollzug": 62,
    "Feuerwehr": 60,
    "Justizvollzug": 63
}

# --- PDF FUNKTION ---
def create_pdf(res, logo_file):
    pdf = FPDF()
    pdf.add_page()
    if logo_file:
        try:
            pdf.image(BytesIO(logo_file.getvalue()), x=150, y=10, w=40)
        except:
            pass
            
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "Dienstherren- & Pensionsanalyse 2026", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 12)
    for k, v in res.items():
        safe_k = k.replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
        safe_v = str(v).replace("€","Euro").replace("ä","ae").replace("ö","oe").replace("ü","ue")
        pdf.cell(85, 9, f"{safe_k}:", border=0)
        pdf.cell(0, 9, f"{safe_v}", border=0, ln=True)
        
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, "Hinweis: Diese Berechnung basiert auf den Werten fuer 2026. Sie stellt eine unverbindliche Schaetzung dar.")
    return pdf.output()

# --- BENUTZEROBERFLÄCHE ---
st.title("🛡️ Pensionslücken-Check & Besoldungs-Analyse")

if not df_besoldung.empty:
    with st.sidebar:
        st.header("⚙️ Konfiguration")
        land_sel = st.selectbox("Bundesland / Dienstherr", df_besoldung["Land"].unique())
        
        gruppen = df_besoldung[df_besoldung["Land"] == land_sel]["Gruppe"].unique()
        gruppe_sel = st.selectbox("Besoldungsgruppe", gruppen)
        
        stufe_sel = st.slider("Erfahrungsstufe (1-8)", 1, 8, 4)
        beruf_sel = st.selectbox("Berufszweig", list(BERUFSGRUPPEN.keys()))
        
        st.divider()
        uploaded_logo = st.file_uploader("Firmenlogo (PNG/JPG)", type=["png", "jpg", "jpeg"])

    # Gehalt aus CSV ziehen
    row = df_besoldung[(df_besoldung["Land"] == land_sel) & (df_besoldung["Gruppe"] == gruppe_sel)]
    grundgehalt = float(row[f"Stufe_{stufe_sel}"].values)
    
    # Zulagen-Logik (Polizeizulage etc. ca. 190€ in 2026)
    zulage = 190.0 if beruf_sel in ["Polizeivollzug", "Feuerwehr", "Justizvollzug"] else 0.0
    brutto_gesamt = grundgehalt + zulage

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 Eingabedaten")
        eintritt = st.number_input("Eintrittsalter", 18, 55, 28)
        tz_jahre = st.number_input("Jahre in Teilzeit", 0, 45, 0)
        tz_quote = st.slider("Teilzeit-Satz in %", 10, 100, 50) if tz_jahre > 0 else 100
        
        st.write("---")
        st.write(f"**Aktuelles Grundgehalt:** {grundgehalt:,.2f} €")
        if zulage > 0:
            st.write(f"**Zulagen (Polizei/FW/JV):** {zulage:,.2f} €")
        st.write(f"**Brutto Gesamt:** {brutto_gesamt:,.2f} €")

    # BERECHNUNG
    altersgrenze = BERUFSGRUPPEN[beruf_sel]
    dienstjahre_effektiv = (altersgrenze - eintritt) - tz_jahre + (tz_jahre * (tz_quote / 100))
    satz = max(min(dienstjahre_effektiv * 1.79375, 71.75), 35.0)
    
    # Netto-Schätzungen
    netto_pension = (brutto_gesamt * (satz / 100)) * 0.72
    netto_aktuell = brutto_gesamt * 0.75
    luecke = netto_aktuell - netto_pension

    # Ergebnis-Dict für PDF
    res_data = {
        "Dienstherr": land_sel,
        "Berufszweig": beruf_sel,
        "Besoldung": f"{gruppe_sel} / Stufe {stufe_sel}",
        "Brutto-Bezüge": f"{brutto_gesamt:,.2f} €",
        "Netto-Einkommen heute (ca.)": f"{netto_aktuell:,.2f} €",
        "Dienstjahre (effektiv)": f"{dienstjahre_effektiv:.2f}",
        "Pensionssatz": f"{satz:.2f} %",
        "Erwartete Netto-Pension": f"{netto_pension:,.2f} €",
        "Monatliche Lücke": f"{luecke:,.2f} €"
    }

    with col2:
        st.subheader("📊 Analyse-Ergebnis")
        
        st.metric("Voraussichtliche Netto-Pension", f"{netto_pension:,.2f} €")
        st.metric("Monatliche Versorgungslücke", f"{max(0.0, luecke):,.2f} €", delta_color="inverse")
        
        st.write(f"Berechnetes Netto-Gehalt heute: ~**{netto_aktuell:,.2f} €**")
        st.write(f"Anspruch bis Alter {altersgrenze}: **{satz:.2f} %**")
        st.progress(satz / 71.75)
        
        st.divider()
        st.download_button(
            label="📄 PDF-Analyse für Kunden erstellen", 
            data=bytes(create_pdf(res_data, uploaded_logo)), 
            file_name=f"Versorgungsanalyse_{land_sel}.pdf", 
            mime="application/pdf"
        )
else:
    st.warning("⚠️ Bitte laden Sie die 'besoldung.csv' in Ihr GitHub-Repository hoch, um den Rechner zu starten.")

