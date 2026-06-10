import streamlit as st
import pandas as pd
from io import BytesIO
from fpdf import FPDF

# --- DATEN-LOADER ---
@st.cache_data
def load_besoldung():
    try:
        # Liest die hochgeladene CSV-Datei ein
        return pd.read_csv("besoldung.csv", sep=";")
    except FileNotFoundError:
        st.error("Datei 'besoldung.csv' nicht gefunden. Bitte bei GitHub hochladen!")
        return pd.DataFrame()

df_besoldung = load_besoldung()

# Definition der Berufsgruppen und ihrer Altersgrenzen
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
    if logo_file: pdf.image(BytesIO(logo_file.getvalue()), x=150, y=10, w=40)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 15, "Beamten-Pensionsanalyse Pro", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 11)
    for k, v in res.items():
        pdf.cell(85, 9, f"{k}:", border=0)
        pdf.cell(0, 9, f"{str(v)}", border=0, ln=True)
    return pdf.output()

# --- HAUPTTEIL ---
st.title("🛡️ Experten-Pensionsrechner (Alle Bundesländer)")

if not df_besoldung.empty:
    with st.sidebar:
        st.header("Konfiguration")
        land_sel = st.selectbox("Land / Dienstherr", df_besoldung["Land"].unique())
        
        gruppen = df_besoldung[df_besoldung["Land"] == land_sel]["Gruppe"].unique()
        gruppe_sel = st.selectbox("Besoldungsgruppe", gruppen)
        
        stufe_sel = st.slider("Erfahrungsstufe", 1, 8, 4)
        beruf_sel = st.selectbox("Berufszweig", list(BERUFSGRUPPEN.keys()))
        uploaded_logo = st.file_uploader("Logo für PDF", type=["png", "jpg"])

    # Werte ermitteln
    grundgehalt = df_besoldung[(df_besoldung["Land"] == land_sel) & 
                               (df_besoldung["Gruppe"] == gruppe_sel)][f"Stufe_{stufe_sel}"].values[0]
    altersgrenze = BERUFSGRUPPEN[beruf_sel]

    # Eingaben für Dienstzeit
    c1, c2 = st.columns(2)
    with c1:
        eintritt = st.number_input("Eintrittsalter", 18, 50, 28)
        tz_jahre = st.number_input("Jahre in Teilzeit", 0, 45, 0)
        tz_quote = st.slider("Teilzeit-Satz (%)", 10, 100, 50) if tz_jahre > 0 else 100

    # Berechnung
    dienstzeit = altersgrenze - eintritt - tz_jahre + (tz_jahre * (tz_quote / 100))
    satz = max(min(dienstzeit * 1.79375, 71.75), 35.0)
    netto_pension = (grundgehalt * (satz / 100)) * 0.72
    luecke = (grundgehalt * 0.75) - netto_pension

    res = {
        "Dienstherr": land_sel,
        "Status": f"{gruppe_sel}, Stufe {stufe_sel}",
        "Grundgehalt": f"{grundgehalt:,.2f} Euro",
        "Altersgrenze": f"{altersgrenze} Jahre",
        "Pensionssatz": f"{satz:.2f} %",
        "Netto-Pension": f"{netto_pension:,.2f} Euro",
        "Versorgungsluecke": f"{luecke:,.2f} Euro"
    }

    with c2:
        st.subheader("Analyse")
        st.metric("Pension (geschätzt)", f"{netto_pension:,.2f} €")
        st.metric("Lücke", f"{luecke:,.2f} €", delta_color="inverse")
        st.progress(satz / 71.75)
        st.download_button("📄 PDF-Report", data=bytes(create_pdf(res, uploaded_logo)), file_name="Analyse.pdf")
else:
    st.warning("Bitte laden Sie zuerst die besoldung.csv hoch.")
