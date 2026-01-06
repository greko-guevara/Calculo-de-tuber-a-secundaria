import streamlit as st
import pandas as pd
import numpy as np

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ===============================
# CONFIGURACIÓN
# ===============================
st.set_page_config(
    page_title="Diseño de tuberías secundarias",
    layout="wide"
)

st.title("💧 Diseño hidráulico de tuberías secundarias")
st.markdown("**Prof. Gregory Guevara — Riego & Drenaje / Universidad EARTH**")

# ===============================
# ENTRADAS
# ===============================
st.sidebar.header("🔧 Entradas del sistema")

Q = st.sidebar.number_input("Caudal total (m³/h)", 0.1, value=20.0)
S = st.sidebar.number_input("Espaciamiento entre salidas (m)", 1.0, value=10.0)
LL = st.sidebar.number_input("Longitud total (m)", 10.0, value=200.0)
HF_disp = st.sidebar.number_input("Pérdida disponible (m)", 1.0, value=10.0)
C = st.sidebar.number_input("Coeficiente Hazen–Williams (C)", value=150)

# DIÁMETROS ORIGINALES
dia = np.array([39.8, 45.9, 57.38, 84.58, 108.72, 160.08, 208.42, 259.75, 308.05, 369.7])

# ===============================
# AYUDA TEÓRICA
# ===============================
with st.expander("📘 Ayuda teórica"):
    st.markdown(r"""
**Modelo:** Hazen–Williams con salidas múltiples  

\[
HF = 1.131 \times 10^9
\left(\frac{Q}{C}\right)^{1.852}
L D^{-4.872} F
\]

**Criterios de diseño**
- Velocidad ≤ 3.0 m/s  
- HF ≤ HF disponible  
- Reducción progresiva cuando HF no cumple con un solo diámetro
""")

# ===============================
# CÁLCULOS GENERALES
# ===============================
Salidas = int(LL / S)
Q_salida = Q / Salidas

F = 2 * Salidas / (2 * Salidas - 1) * (
    (1 / 2.852) + 0.852 ** 0.5 / (6 * Salidas ** 2)
)

# ===============================
# 1️⃣ SOLUCIÓN CON UN DIÁMETRO
# ===============================
st.header("🔹 Solución con un solo diámetro")

sol_1 = []

for d in dia:
    Area = np.pi * (d / 2000) ** 2
    Vel = Q / Area / 3600
    HF1 = 1.131e9 * (Q / C) ** 1.852 * LL * d ** -4.872 * F

    sol_1.append({
        "Diámetro (mm)": d,
        "Velocidad (m/s)": round(Vel, 2),
        "HF (m)": round(HF1, 2),
        "Cumple": "✅" if (Vel <= 3 and HF1 <= HF_disp) else "❌"
    })

df1 = pd.DataFrame(sol_1)
st.dataframe(df1, use_container_width=True)

df1_ok = df1[df1["Cumple"] == "✅"]

if df1_ok.empty:
    st.warning("⚠️ Ningún diámetro cumple completamente con un solo tramo.")
    d1 = None
else:
    d1 = df1_ok.iloc[0]["Diámetro (mm)"]
    st.success(f"Diámetro recomendado: **{d1} mm**")

# ===============================
# 2️⃣ SOLUCIÓN CON DOS DIÁMETROS
# ===============================
st.header("🔹 Solución con dos diámetros progresivos")

sol_2 = None

for i in range(1, len(dia)):
    d_up = dia[i]
    d_dn = dia[i - 1]

    for L1 in np.arange(S, LL, S):
        L2 = LL - L1

        Q2 = Q * L2 / LL

        A1 = np.pi * (d_up / 2000) ** 2
        A2 = np.pi * (d_dn / 2000) ** 2

        V1 = Q / A1 / 3600
        V2 = Q2 / A2 / 3600

        HF_total = (
            1.131e9 * (Q / C) ** 1.852 * L1 * d_up ** -4.872 * F +
            1.131e9 * (Q2 / C) ** 1.852 * L2 * d_dn ** -4.872 * F
        )

        if HF_total <= HF_disp and V1 <= 3 and V2 <= 3:
            sol_2 = {
                "D1": d_up,
                "L1": L1,
                "D2": d_dn,
                "L2": L2,
                "HF": HF_total,
                "V1": V1,
                "V2": V2
            }
            break
    if sol_2:
        break

if sol_2:
    st.success("✅ Solución con dos diámetros encontrada")
    st.write(f"**{sol_2['D1']} mm × {round(sol_2['L1'],1)} m**")
    st.write(f"**{sol_2['D2']} mm × {round(sol_2['L2'],1)} m**")
    st.write(f"HF total: **{round(sol_2['HF'],2)} m**")
    st.write(f"Velocidades: {round(sol_2['V1'],2)} / {round(sol_2['V2'],2)} m/s")
else:
    st.error("❌ No se encontró solución con dos diámetros.")

# ===============================
# 📄 EXPORTAR PDF
# ===============================
st.header("📄 Exportar memoria de cálculo")

if st.button("📥 Generar PDF"):
    pdf_file = "memoria_diseño_tuberias.pdf"
    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    styles = getSampleStyleSheet()
    elems = []

    elems.append(Paragraph("Memoria de cálculo – Diseño de tuberías", styles["Title"]))
    elems.append(Spacer(1, 12))

    elems.append(Paragraph(f"Caudal: {Q} m³/h", styles["Normal"]))
    elems.append(Paragraph(f"Longitud total: {LL} m", styles["Normal"]))
    elems.append(Paragraph(f"Pérdida disponible: {HF_disp} m", styles["Normal"]))
    elems.append(Spacer(1, 12))

    if sol_2:
        elems.append(Paragraph("Solución adoptada: Dos diámetros", styles["Heading2"]))
        table = Table([
            ["Diámetro", "Longitud (m)", "Velocidad (m/s)"],
            [sol_2["D1"], round(sol_2["L1"],1), round(sol_2["V1"],2)],
            [sol_2["D2"], round(sol_2["L2"],1), round(sol_2["V2"],2)],
        ])
        elems.append(table)
        elems.append(Spacer(1, 12))
        elems.append(Paragraph(f"HF total: {round(sol_2['HF'],2)} m", styles["Normal"]))

    doc.build(elems)
    st.success("📄 PDF generado correctamente")
    st.download_button("⬇️ Descargar PDF", data=open(pdf_file, "rb"), file_name=pdf_file)
