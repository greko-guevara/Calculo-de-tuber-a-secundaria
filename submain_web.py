import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm

# ===============================
# BASE DE DATOS PVC - SDR
# ===============================
PVC_SDR = {
    "17": [37.18, 42.58, 53.21, 54.45, 78.44, 100.84, 148.46, 193.28],
    "26": [30.36, 38.9, 44.56, 55.71, 67.45, 82.04, 105.52,
           155.32, 202.22, 252.07, 298.95],
    "32.5": [39.0, 45.22, 56.63, 68.55, 83.42, 107.28,
             157.92, 205.62, 256.23, 303.93],
    "41": [39.8, 45.9, 57.38, 69.46, 84.58, 108.72,
           160.08, 208.42, 259.75, 308.05, 369.7]
}


# ===============================
# CONFIGURACIÓN GENERAL
# ===============================
st.set_page_config(
    page_title="Secundaria de Riego",
    layout="wide"
)

st.title("💧 Secundaria de Riego")
st.markdown(
    "**Diseño hidráulico de tuberías secundarias**  \n"
    "Prof. Gregory Guevara — Riego & Drenaje / Universidad EARTH"
)

# ===============================
# ENTRADAS
# ===============================
st.sidebar.header("🔧 Parámetros de entrada")

Q = st.sidebar.number_input("Caudal total (m³/h)", min_value=0.1, value=20.0)
S = st.sidebar.number_input("Espaciamiento entre salidas (m)", min_value=0.5, value=10.0)
LL = st.sidebar.number_input("Longitud total (m)", min_value=10.0, value=200.0)
HF_disp = st.sidebar.number_input("Pérdida disponible (m)", min_value=1.0, value=10.0)
C = st.sidebar.number_input("Coeficiente Hazen–Williams (C)", value=150)

# ===============================
# SELECCIÓN DE MATERIAL PVC
# ===============================
st.sidebar.header("🧱 Material de la tubería")

SDR_sel = st.sidebar.selectbox(
    "Seleccionar SDR del PVC",
    options=list(PVC_SDR.keys()),
    index=3  # SDR 41 por defecto
)

dia = np.array(PVC_SDR[SDR_sel])

st.sidebar.markdown(
    f"**Diámetros interiores disponibles (mm):**  \n"
    f"{', '.join([str(d) for d in dia])}"
)

# ===============================
# AYUDA TEÓRICA
# ===============================
with st.expander("📘 Ayuda teórica"):
    st.markdown("### 📐 Ecuación de Hazen–Williams (múltiples salidas)")

    st.latex(r"""
    H_f =
    1.131 \times 10^9
    \left(\frac{Q}{C}\right)^{1.852}
    L \;
    D^{-4.872}
    F
    """)

    st.markdown("""
    **Donde:**
    - **Hf** = pérdida de carga (m)
    - **Q** = caudal (L/s)
    - **C** = coeficiente Hazen–Williams
    - **L** = longitud (m)
    - **D** = diámetro interno (mm)
    - **F** = factor por múltiples salidas

    **Criterios adoptados**
    - Velocidad ≤ 3 m/s
    - HF total ≤ HF disponible
    - Reducción progresiva de diámetro
    """)

# ===============================
# CÁLCULOS GENERALES
# ===============================
Salidas = int(LL / S)
Q_salida = Q / Salidas

F = 2 * Salidas / (2 * Salidas - 1) * (
    (1 / 2.852) + (0.852 ** 0.5) / (6 * Salidas ** 2)
)

# ===============================
# SOLUCIÓN 1 DIÁMETRO
# ===============================
st.header("🔹 Solución con un diámetro")

sol1 = []

for d in dia:
    A = np.pi * (d / 2000) ** 2
    V = Q / A / 3600
    HF1 = 1.131e9 * (Q / C) ** 1.852 * LL * d ** -4.872 * F

    sol1.append({
        "Diámetro (mm)": d,
        "Velocidad (m/s)": round(V, 2),
        "HF (m)": round(HF1, 2),
        "Cumple": V <= 3 and HF1 <= HF_disp
    })

df1 = pd.DataFrame(sol1)
st.info(f"Material seleccionado: PVC – SDR {SDR_sel}")

st.dataframe(df1, use_container_width=True)

df1_ok = df1[df1["Cumple"]]

d1, HF1_sel = None, None
if not df1_ok.empty:
    d1 = df1_ok.iloc[0]["Diámetro (mm)"]
    HF1_sel = df1_ok.iloc[0]["HF (m)"]
    st.success(f"Diámetro recomendado: **{d1} mm**")
else:
    st.warning("⚠️ No hay solución con un solo diámetro.")

# ===============================
# SOLUCIÓN DOS DIÁMETROS
# ===============================
st.header("🔹 Solución con dos diámetros progresivos")

sol2 = None

for i in range(1, len(dia)):
    d1p, d2p = dia[i], dia[i - 1]

    for L1 in np.arange(S, LL, S):
        L2 = LL - L1
        Q2 = Q * L2 / LL

        A1 = np.pi * (d1p / 2000) ** 2
        A2 = np.pi * (d2p / 2000) ** 2

        V1 = Q / A1 / 3600
        V2 = Q2 / A2 / 3600

        HF = (
            1.131e9 * (Q / C) ** 1.852 * L1 * d1p ** -4.872 * F +
            1.131e9 * (Q2 / C) ** 1.852 * L2 * d2p ** -4.872 * F
        )

        if HF <= HF_disp and V1 <= 3 and V2 <= 3:
            sol2 = dict(D1=d1p, L1=L1, V1=V1,
                        D2=d2p, L2=L2, V2=V2, HF=HF)
            break
    if sol2:
        break
st.info(f"Material seleccionado: PVC – SDR {SDR_sel}")

if sol2:
    st.success("✅ Solución progresiva encontrada")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Tramo inicial")
        st.metric("Diámetro (mm)", f"{sol2['D1']}")
        st.metric("Longitud (m)", f"{sol2['L1']}")
        st.metric("Velocidad (m/s)", f"{sol2['V1']:.2f}")

    with col2:
        st.markdown("### Tramo final")
        st.metric("Diámetro (mm)", f"{sol2['D2']}")
        st.metric("Longitud (m)", f"{sol2['L2']}")
        st.metric("Velocidad (m/s)", f"{sol2['V2']:.2f}")

    st.markdown("---")
    st.metric("Pérdida de carga total (m)", f"{sol2['HF']:.2f}")


# ===============================
# GRÁFICO FAO
# ===============================
st.header("📈 Pérdida de carga acumulada")

x = np.arange(0, LL + S, S)

fig, ax = plt.subplots(figsize=(8, 5))

if HF1_sel:
    ax.plot(x, HF1_sel * x / LL,
            label="Un diámetro",
            color="#1f77b4", linewidth=2)

if sol2:
    ax.plot(x, sol2["HF"] * x / LL,
            label="Dos diámetros",
            color="#d62728", linestyle="--", linewidth=2)

ax.axhline(HF_disp, color="black",
           linestyle=":", linewidth=1,
           label="HF disponible")

ax.set_xlabel("Longitud acumulada (m)")
ax.set_ylabel("Pérdida de carga acumulada (m)")
ax.set_title("Pérdida de carga acumulada – Tubería secundaria")
ax.grid(True, linestyle=":", alpha=0.7)
ax.legend()

st.pyplot(fig)
fig.savefig("grafico_hf.png", dpi=300)

# ===============================
# PDF INSTITUCIONAL
# ===============================
# ===============================
# PDF ONE PAGE
# ===============================
st.header("📄 Exportar memoria de cálculo (1 página)")

if st.button("📥 Generar PDF"):
    pdf = "Secundaria_de_Riego_OnePage.pdf"
    doc = SimpleDocTemplate(
        pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    e = []

    # ---- ENCABEZADO ----
    e.append(Paragraph(
        "<b>SECUNDARIA DE RIEGO</b><br/>"
        "Diseño hidráulico de tuberías secundarias – Hazen–Williams<br/>"
        "Universidad EARTH | Riego & Drenaje<br/><br/>",
        styles["Title"]
    ))

    # ---- DATOS DE ENTRADA ----
    e.append(Paragraph("<b>Datos de entrada</b>", styles["Heading3"]))
    e.append(Paragraph(
        f"Caudal: {Q} m³/h &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"Longitud: {LL} m &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"HF disponible: {HF_disp} m<br/>"
        f"Número de salidas: {Salidas}"
        f"Material: PVC &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"SDR: {SDR_sel}",
        styles["Normal"]
    ))

    # ---- SOLUCIÓN 1 DIÁMETRO ----
    if d1:
        e.append(Spacer(1, 6))
        e.append(Paragraph("<b>Solución con un diámetro</b>", styles["Heading3"]))
        e.append(Paragraph(
            f"D = {d1} mm &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"HF = {HF1_sel:.2f} m",
            styles["Normal"]
        ))

    # ---- SOLUCIÓN 2 DIÁMETROS ----
    if sol2:
        e.append(Spacer(1, 6))
        e.append(Paragraph("<b>Solución con dos diámetros progresivos</b>", styles["Heading3"]))
        e.append(Table(
            [
                ["Tramo", "Diámetro (mm)", "Longitud (m)", "Velocidad (m/s)"],
                ["Inicial", sol2["D1"], sol2["L1"], f"{sol2['V1']:.2f}"],
                ["Final", sol2["D2"], sol2["L2"], f"{sol2['V2']:.2f}"],
            ],
            hAlign="LEFT"
        ))
        e.append(Paragraph(
            f"Pérdida de carga total: <b>{sol2['HF']:.2f} m</b>",
            styles["Normal"]
        ))

    # ---- GRÁFICO ----
    e.append(Spacer(1, 8))
    e.append(Image("grafico_hf.png", width=14*cm, height=7*cm))

    doc.build(e)

    st.success("📄 PDF ONE PAGE generado correctamente")
    st.download_button(
        "⬇️ Descargar PDF",
        open(pdf, "rb"),
        file_name=pdf
    )
