import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

# ===============================
# CONFIGURACIÓN GENERAL
# ===============================
st.set_page_config(
    page_title="Secundaria de Riego",
    layout="wide"
)

st.title("💧 Secundaria de Riego")
st.markdown("**Diseño hidráulico de tuberías secundarias**  \n"
            "Prof. Gregory Guevara — Riego & Drenaje / Universidad EARTH")

# ===============================
# ENTRADAS
# ===============================
st.sidebar.header("🔧 Parámetros de entrada")

Q = st.sidebar.number_input("Caudal total (m³/h)", min_value=0.1, value=20.0)
S = st.sidebar.number_input("Espaciamiento entre salidas (m)", min_value=0.5, value=10.0)
LL = st.sidebar.number_input("Longitud total (m)", min_value=10.0, value=200.0)
HF_disp = st.sidebar.number_input("Pérdida disponible (m)", min_value=1.0, value=10.0)
C = st.sidebar.number_input("Coeficiente Hazen–Williams (C)", value=150)

# Diámetros SDR 41 (ORIGINALES)
dia = np.array([39.8, 45.9, 57.38, 84.58, 108.72, 160.08,
                208.42, 259.75, 308.05, 369.7])

# ===============================
# AYUDA TEÓRICA
# ===============================
with st.expander("📘 Ayuda teórica"):
    st.markdown("### 📐 Ecuación de Hazen–Williams (tubería secundaria con múltiples salidas)")

    st.latex(r"""
    H_f =
    1.131 \times 10^9 \;
    \left(\frac{Q}{C}\right)^{1.852}
    \; L \;
    D^{-4.872}
    \; F
    """)

    st.markdown("""
    **Donde:**

    - **H<sub>f</sub>** = pérdida de carga por fricción (m)  
    - **Q** = caudal (L/s)  
    - **C** = coeficiente de Hazen–Williams  
    - **L** = longitud de la tubería (m)  
    - **D** = diámetro interno (mm)  
    - **F** = factor de corrección por múltiples salidas  

    ---
    ### 📋 Criterios de diseño adoptados
    - Velocidad del flujo ≤ **3 m/s**
    - Pérdida de carga total ≤ **HF disponible**
    - **Reducción progresiva del diámetro** en la solución a doble diámetro
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
st.dataframe(df1, use_container_width=True)

df1_ok = df1[df1["Cumple"]]

if df1_ok.empty:
    st.warning("⚠️ Ningún diámetro cumple con solución única.")
    d1 = None
else:
    d1 = df1_ok.iloc[0]["Diámetro (mm)"]
    HF1_sel = df1_ok.iloc[0]["HF (m)"]
    st.success(f"Diámetro recomendado: **{d1} mm**")

# ===============================
# SOLUCIÓN DOS DIÁMETROS
# ===============================
st.header("🔹 Solución con dos diámetros progresivos")

sol2 = None

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
            sol2 = {
                "D1": d_up, "L1": L1,
                "D2": d_dn, "L2": L2,
                "HF": HF_total,
                "V1": V1, "V2": V2
            }
            break
    if sol2:
        break

if sol2:
    st.success("✅ Solución progresiva encontrada")
    st.write(f"{sol2['D1']} mm × {sol2['L1']} m")
    st.write(f"{sol2['D2']} mm × {sol2['L2']} m")
    st.write(f"HF total = {round(sol2['HF'],2)} m")
else:
    st.error("❌ No se encontró solución progresiva.")

# ===============================
# GRÁFICOS
# ===============================
st.header("📈 Pérdida acumulada")

x = np.arange(S, LL + S, S)
hf_acum_1 = HF1_sel * x / LL if d1 else np.zeros_like(x)
hf_acum_2 = sol2["HF"] * x / LL if sol2 else None

fig, ax = plt.subplots()
ax.plot(x, hf_acum_1, label="1 diámetro")
if sol2:
    ax.plot(x, hf_acum_2, label="2 diámetros", linestyle="--")

ax.set_xlabel("Longitud (m)")
ax.set_ylabel("HF acumulada (m)")
ax.legend()
ax.grid(True)

st.pyplot(fig)

fig.savefig("grafico_hf.png", dpi=150)

# ===============================
# PDF
# ===============================
st.header("📄 Exportar memoria de cálculo")

if st.button("📥 Generar PDF"):
    pdf = "Secundaria_de_Riego.pdf"
    doc = SimpleDocTemplate(pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    e = []

    e.append(Paragraph("Secundaria de Riego", styles["Title"]))
    e.append(Paragraph("Memoria de cálculo", styles["Heading2"]))
    e.append(Spacer(1, 12))

    e.append(Paragraph(f"Caudal: {Q} m³/h", styles["Normal"]))
    e.append(Paragraph(f"Longitud: {LL} m", styles["Normal"]))
    e.append(Paragraph(f"HF disponible: {HF_disp} m", styles["Normal"]))
    e.append(Paragraph(f"# salidas: {Salidas} ", styles["Normal"]))
    e.append(Spacer(1, 12))

    if d1:
        e.append(Paragraph("Solución con un diámetro", styles["Heading3"]))
        e.append(Paragraph(f"D = {d1} mm", styles["Normal"]))
        e.append(Paragraph(f"HF = {round(HF1_sel,2)} m", styles["Normal"]))

    if sol2:
        e.append(Spacer(1, 12))
        e.append(Paragraph("Solución con dos diámetros", styles["Heading3"]))
        table = Table([
            ["Diámetro", "Longitud (m)", "Velocidad (m/s)"],
            [sol2["D1"], sol2["L1"], round(sol2["V1"],2)],
            [sol2["D2"], sol2["L2"], round(sol2["V2"],2)],
        ])
        e.append(table)

    e.append(Spacer(1, 12))
    e.append(Image("grafico_hf.png", width=400, height=250))

    doc.build(e)

    st.success("📄 PDF generado correctamente")
    st.download_button("⬇️ Descargar PDF", open(pdf, "rb"), file_name=pdf)
