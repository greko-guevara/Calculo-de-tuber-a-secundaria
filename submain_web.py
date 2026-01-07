import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm

# ===============================
# BASES DE DATOS
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

PE_PN = {
    "PN6": [35.4, 44.6, 56.0, 67.0, 80.8, 99.0,
            112.8, 126.4, 144.0, 162.0, 180.0],
    "PN8": [27.4, 34.4, 43.2, 54.4, 65.2, 78.2,
            95.8, 108.8, 122.0, 139.2, 156.8, 173.2],
    "PN10": [26.0, 32.6, 40.8, 51.4, 61.4, 73.6,
             90.0, 102.2, 114.6, 130.8, 147.2, 163.6]
}

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
Q = st.sidebar.number_input("Caudal total (m³/h)", 100.0)
S = st.sidebar.number_input("Espaciamiento entre salidas (m)", 10.0)
LL = st.sidebar.number_input("Longitud total (m)", 100.0)
HF_disp = st.sidebar.number_input("Pérdida disponible (m)", 1.0)
C = st.sidebar.number_input("Coeficiente Hazen–Williams (C)", 150)

# ===============================
# SELECCIÓN DE MATERIAL Y SDR/PN
# ===============================
st.sidebar.header("🧱 Material de la tubería")
material = st.sidebar.selectbox("Material", ["PVC", "PE (HDPE)"])

if material == "PVC":
    SDR_sel = st.sidebar.selectbox("SDR del PVC", list(PVC_SDR.keys()))
    dia = np.array(PVC_SDR[SDR_sel])
    mat_label = f"PVC – SDR {SDR_sel}"
else:
    PN_sel = st.sidebar.selectbox("Clase de presión PE", list(PE_PN.keys()))
    dia = np.array(PE_PN[PN_sel])
    mat_label = f"PE100 – {PN_sel}"

st.info(f"Material seleccionado: **{mat_label}**")
st.sidebar.markdown(f"Diámetros interiores disponibles: {', '.join([str(d) for d in dia])}")

# ===============================
# AYUDA TEÓRICA
# ===============================
with st.expander("📘 Ayuda teórica"):
    st.markdown("### 📐 Ecuación de Hazen–Williams (múltiples salidas)")
    st.latex(r"H_f = 1.131 \times 10^9 \left(\frac{Q}{C}\right)^{1.852} L \, D^{-4.872} F")
    st.markdown("""
**Donde:**  
- Hf = pérdida de carga (m)  
- Q = caudal (L/s)  
- C = coeficiente Hazen–Williams  
- L = longitud (m)  
- D = diámetro interno (mm)  
- F = factor por múltiples salidas  

**Criterios:**  
- Velocidad ≤ 3 m/s  
- HF total ≤ HF disponible  
- Reducción progresiva de diámetro
### ⏱️ Tiempo de avance del agua

El tiempo de avance representa el tiempo requerido para que el agua recorra la tubería desde el inicio hasta el último punto.
**Un solo diámetro:**
\[
t = \frac{L}{V}
\]

**Dos diámetros progresivos:**
\[
t = \frac{L_1}{V_1} + \frac{L_2}{V_2}
\]

Este criterio es clave para:
- Diseño operativo Fertirriego
- Evaluación de respuesta hidráulica
- Comparación de alternativas de diseño
                
### 📉 Velocidad del agua a lo largo de la tubería

En tuberías con múltiples salidas, el caudal disminuye progresivamente,
por lo que la velocidad también varía con la longitud.

\[
V(x) = \frac{Q(x)}{A}
\]

Este gráfico permite:
- Ver la reducción de velocidad hacia el extremo
- Comparar diámetro único vs. diseño progresivo
- Verificar criterios de autolimpieza y velocidad máxima


""")

# ===============================
# CÁLCULOS
# ===============================
Salidas = int(LL / S)
Q_salida = Q / Salidas
F = 2 * Salidas / (2 * Salidas - 1) * ((1 / 2.852) + 0.852**0.5 / (6 * Salidas**2))

# --- Solución 1 diámetro ---
st.header("🔹 Solución con un diámetro")
sol1 = []
for d in dia:
    A = np.pi * (d / 2000)**2
    V = Q / A / 3600
    HF1 = 1.131e9 * (Q / C)**1.852 * LL * d**-4.872 * F
    sol1.append({"Diámetro (mm)": d, "Velocidad (m/s)": round(V,2),
                 "HF (m)": round(HF1,2), "Cumple": V<=3 and HF1<=HF_disp})
df1 = pd.DataFrame(sol1)
df1_ok = df1[df1["Cumple"]]
d1, HF1_sel = None, None
if not df1_ok.empty:
    d1 = df1_ok.iloc[0]["Diámetro (mm)"]
    HF1_sel = df1_ok.iloc[0]["HF (m)"]
    st.success(f"Diámetro recomendado: **{d1} mm**")
else:
    st.warning("⚠️ No hay solución con un solo diámetro.")
st.dataframe(df1, use_container_width=True)
if d1:
    A1 = np.pi * (d1 / 2000)**2
    V1 = Q / A1 / 3600
    t1 = LL / V1              # segundos
    t1_min = t1 / 60
    st.metric("⏱️ Tiempo de avance (min)", f"{t1_min:.2f}")

# --- Solución 2 diámetros ---
st.header("🔹 Solución con dos diámetros progresivos")
sol2 = None
for i in range(1, len(dia)):
    d_up, d_dn = dia[i], dia[i-1]
    for L1 in np.arange(S, LL, S):
        L2 = LL - L1
        Q2 = Q * L2 / LL
        A1 = np.pi * (d_up/2000)**2
        A2 = np.pi * (d_dn/2000)**2
        V1 = Q / A1 / 3600
        V2 = Q2 / A2 / 3600
        HF = 1.131e9*(Q/C)**1.852*L1*d_up**-4.872*F + \
             1.131e9*(Q2/C)**1.852*L2*d_dn**-4.872*F
        if HF<=HF_disp and V1<=3 and V2<=3:
            sol2 = dict(D1=d_up, L1=L1, V1=V1, D2=d_dn, L2=L2, V2=V2, HF=HF)
            break
    if sol2: break

if sol2:
    st.success("✅ Solución progresiva encontrada")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tramo inicial: D (mm)", sol2["D1"])
        st.metric("L (m)", sol2["L1"])
        st.metric("V (m/s)", f"{sol2['V1']:.2f}")
    with col2:
        st.metric("Tramo final: D (mm)", sol2["D2"])
        st.metric("L (m)", sol2["L2"])
        st.metric("V (m/s)", f"{sol2['V2']:.2f}")
    st.metric("HF total (m)", f"{sol2['HF']:.2f}")
if sol2:
    t2 = sol2["L1"]/sol2["V1"] + sol2["L2"]/sol2["V2"]
    t2_min = t2 / 60
    st.metric("⏱️ Tiempo total de avance (min)", f"{t2_min:.2f}")


x = np.linspace(0, LL, 100)

# --- Velocidad para 1 diámetro ---
V1_x = None
if d1:
    A1 = np.pi * (d1 / 2000)**2
    Qx = Q * (1 - x / LL)
    V1_x = Qx / A1 / 3600

# --- Velocidad para 2 diámetros ---
V2_x = None
if sol2:
    V2_x = []
    for xi in x:
        if xi <= sol2["L1"]:
            A = np.pi * (sol2["D1"] / 2000)**2
            Qi = Q * (1 - xi / LL)
        else:
            A = np.pi * (sol2["D2"] / 2000)**2
            Qi = Q * (1 - xi / LL)
        V2_x.append(Qi / A / 3600)
    V2_x = np.array(V2_x)


# ===============================
# GRÁFICO
# ===============================
st.header("📈 Pérdida de carga acumulada")
x = np.arange(0, LL+S, S)
fig, ax = plt.subplots(figsize=(8,5))
if HF1_sel:
    ax.plot(x, HF1_sel*x/LL, label="1 diámetro", color="#1f77b4", linewidth=2)
if sol2:
    ax.plot(x, sol2["HF"]*x/LL, label="2 diámetros", color="#d62728", linestyle="--", linewidth=2)
ax.axhline(HF_disp, color="black", linestyle=":", linewidth=1, label="HF disponible")
ax.set_xlabel("Longitud acumulada (m)")
ax.set_ylabel("Pérdida de carga acumulada (m)")
ax.set_title("Pérdida de carga acumulada – Tubería secundaria")
ax.grid(True, linestyle=":", alpha=0.7)
ax.legend()
st.pyplot(fig)
fig.savefig("grafico_hf.png", dpi=300)

st.header("📉 Velocidad del agua a lo largo de la tubería")

fig_v, ax_v = plt.subplots(figsize=(8,5))

if V1_x is not None:
    ax_v.plot(x, V1_x, label="1 diámetro", linewidth=2)

if V2_x is not None:
    ax_v.plot(x, V2_x, label="2 diámetros progresivos", linestyle="--", linewidth=2)

ax_v.axhline(3, linestyle=":", linewidth=1, label="V máx recomendada (3 m/s)")
ax_v.axhline(0.6, linestyle=":", linewidth=1, label="V mín autolimpieza (0.6 m/s)")

ax_v.set_xlabel("Longitud acumulada (m)")
ax_v.set_ylabel("Velocidad (m/s)")
ax_v.set_title("Distribución de velocidades en la tubería secundaria")
ax_v.grid(True, linestyle=":", alpha=0.7)
ax_v.legend()

st.pyplot(fig_v)
fig_v.savefig("grafico_velocidad.png", dpi=300)


# ===============================
# PDF ONE PAGE
# ===============================
st.header("📄 Exportar memoria de cálculo (1 página)")
if st.button("📥 Generar PDF"):
    pdf = "Secundaria_de_Riego_OnePage.pdf"
    doc = SimpleDocTemplate(pdf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    e = []
    # --- Portada
    e.append(Paragraph("<b>SECUNDARIA DE RIEGO</b>", styles["Title"]))
    e.append(Paragraph("Diseño hidráulico de tuberías secundarias – Hazen–Williams", styles["Heading3"]))
    e.append(Paragraph("Universidad EARTH | Riego & Drenaje", styles["Heading4"]))
    e.append(Spacer(1,12))
    # --- Datos
    e.append(Paragraph("<b>Datos de entrada</b>", styles["Heading3"]))
    e.append(Paragraph(f"Caudal: {Q} m³/h | Longitud: {LL} m | HF disponible: {HF_disp} m | Salidas: {Salidas}", styles["Normal"]))
    e.append(Paragraph(f"Material: {mat_label}", styles["Normal"]))
    e.append(Spacer(1,6))
    # --- Solución 1 diámetro
    if d1:
        e.append(Paragraph("<b>Solución con un diámetro</b>", styles["Heading3"]))
        e.append(Paragraph(f"D = {d1} mm | HF = {HF1_sel:.2f} m", styles["Normal"]))
        e.append(Paragraph(f"Tiempo de avance = {t1_min:.2f} minutos",styles["Normal"]))

    # --- Solución 2 diámetros
    if sol2:
        e.append(Paragraph("<b>Solución con dos diámetros progresivos</b>", styles["Heading3"]))
        e.append(Table([
            ["Tramo","D (mm)","L (m)","V (m/s)"],
            ["Inicial", sol2["D1"], sol2["L1"], f"{sol2['V1']:.2f}"],
            ["Final", sol2["D2"], sol2["L2"], f"{sol2['V2']:.2f}"],
        ], hAlign="LEFT"))
        e.append(Paragraph(f"HF total = {sol2['HF']:.2f} m", styles["Normal"]))
        e.append(Paragraph(f"Tiempo total de avance = {t2_min:.2f} minutos",styles["Normal"]))

    # --- Gráfico
    e.append(Spacer(1,8))
    e.append(Image("grafico_hf.png", width=14*cm, height=7*cm))
    doc.build(e)
    st.success("📄 PDF ONE PAGE generado correctamente")
    st.download_button("⬇️ Descargar PDF", open(pdf,"rb"), file_name=pdf)

    e.append(Spacer(1,8))
    e.append(Paragraph("<b>Distribución de velocidades</b>", styles["Heading3"]))
    e.append(Image("grafico_velocidad.png", width=14*cm, height=7*cm))

