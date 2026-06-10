import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# Konfiguration
st.set_page_config(page_title="Experten-Pensionsrechner 2026", layout="wide")

# --- DATEN-LOADER ---
@st.cache_data
def load_besoldung():
    try:
        # Liest die CSV ein. Wichtig: sep=";" passend zur Datei
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
            pass # Falls Bildformat nicht kompatibel
            
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "Beamten-Pensionsanalyse 2026", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "", 11)
    for k, v in res.items():
        # Umlaute-Schutz für PDF
        safe_k = k.replace("ä","ae").replace("ö","oe").replace("ü","ue").replace("ß","ss")
        safe_v = str(v).replace("€","Euro").replace("ä","ae").replace("ö","oe").replace("ü","ue")
        pdf.cell(85, 9, f"{safe_k}:", border=0)
        pdf.cell(0, 9, f"{safe_v}", border=0, ln=True)
        
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 5, "Hinweis: Diese Berechnung basiert auf den Werten fuer 2026. Sie stellt eine Schaetzung dar und ersetzt keine rechtliche Beratung.")
    return pdf.output()

# --- BENUTZEROBERFLÄCHE ---
st.title("🛡️ Dienstherren- & Pensions-Check 2026")

if not df_besoldung.empty:
    with st.sidebar:
        st.header("1. Dienstherr & Status")
        land_sel = st.selectbox("Bundesland / Bund", df_besoldung["Land"].unique())
        
        # Filter Gruppen basierend auf Land
        gruppen = df_besoldung[df_besoldung["Land"] == land_sel]["Gruppe"].unique()
        gruppe_sel = st.selectbox("Besoldungsgruppe", gruppen)
        
        stufe_sel = st.slider("Erfahrungsstufe", 1, 8, 4)
        beruf_sel = st.selectbox("Berufszweig", list(BERUFSGRUPPEN.keys()))
        
        st.divider()
        st.header("2. Branding")
        uploaded_logo = st.file_uploader("Logo für PDF (PNG/JPG)", type=["png", "jpg", "jpeg"])

    # Gehalt aus CSV ziehen
    row = df_besoldung[(df_besoldung["Land"] == land_sel) & (df_besoldung["Gruppe"] == gruppe_sel)]
    grundgehalt = float(row[f"Stufe_{stufe_sel}"].values[0])
    
    # Zulagen-Logik (Polizeizulage etc. ca. 190€ in 2026)
    zulage = 190.0 if beruf_sel in ["Polizeivollzug", "Feuerwehr", "Justizvollzug"] else 0.0
    brutto_gesamt = grundgehalt + zulage

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Dienstzeit-Parameter")
        eintritt = st.number_input("Eintrittsalter in den Dienst", 18, 55, 28)
        tz_jahre = st.number_input("Bisherige/Geplante Teilzeitjahre", 0, 45, 0)
        tz_quote = st.slider("Teilzeit-Satz in %", 10, 100, 50) if tz_jahre > 0 else 100

    # BERECHNUNG
    altersgrenze = BERUFSGRUPPEN[beruf_sel]
    dienstjahre_effektiv = (altersgrenze - eintritt) - tz_jahre + (tz_jahre * (tz_quote / 100))
    
    # Pensionssatz (1,79375 pro Jahr, max 71,75, min 35)
    satz = max(min(dienstjahre_effektiv * 1.79375, 71.75), 35.0)
    
    # Netto-Schätzungen (Pension ca. 72% vom Brutto nach Steuer/PKV, Aktuell ca. 75%)
    netto_pension = (brutto_gesamt * (satz / 100)) * 0.72
    netto_aktuell = brutto_gesamt * 0.75
    luecke = netto_aktuell - netto_pension

    # Ergebnis-Dict für PDF
    res_data = {
        "Dienstherr": land_sel,
        "Berufszweig": beruf_sel,
        "Besoldung": f"{gruppe_sel} / Stufe {stufe_sel}",
        "Brutto inkl. Zulagen": f"{brutto_gesamt:,.2f} €",
        "Dienstjahre (effektiv)": f"{dienstjahre_effektiv:.2f}",
        "Pensionssatz": f"{satz:.2f} %",
        "Netto-Pension (ca.)": f"{netto_pension:,.2f} €",
        "Versorgungsluecke": f"{luecke:,.2f} €"
    }

    with col2:
        st.subheader("Analyse-Ergebnis")
        st.metric("Voraussichtliche Netto-Pension", f"{netto_pension:,.2f} €")
        st.metric("Monatliche Lücke", f"{max(0.0, luecke):,.2f} €", delta_color="inverse")
        
        st.write(f"Erreichte Dienstzeit bis Alter {altersgrenze}: **{dienstjahre_effektiv:.2f} Jahre**")
        st.progress(satz / 71.75)
        
        st.divider()
        if st.download_button("📄 PDF-Analyse mit Logo erstellen", 
                             data=bytes(create_pdf(res_data, uploaded_logo)), 
                             file_name=f"Analyse_{land_sel}.pdf", 
                             mime="application/pdf"):
            st.balloons()
else:
    st.warning("⚠️ Bitte laden Sie die 'besoldung.csv' in Ihr GitHub-Repository hoch, um den Rechner zu starten.")
