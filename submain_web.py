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
st.set_page_config(page_title="Secundaria de Riego", layout="wide")
st.title("💧 Diseño de Tubería Secundaria de Riego")
st.caption("Diseño hidráulico + tiempo de avance discreto | Prof. Gregory Guevara")

# ===============================
# ENTRADAS
# ===============================
st.sidebar.header("🔧 Parámetros de entrada")

Q = st.sidebar.number_input("Caudal total (m³/h)", value=20.0)
S = st.sidebar.number_input("Espaciamiento entre salidas (m)", value=10.0)
LL = st.sidebar.number_input("Longitud total (m)", value=100.0)
HF_disp = st.sidebar.number_input("Pérdida disponible (m)", value=1.0)
C = st.sidebar.number_input("Coeficiente Hazen–Williams (C)", value=150)

Salidas = int(LL / S)
Q_salida = Q / Salidas

# ===============================
# MATERIAL
# ===============================
st.sidebar.header("🧱 Material")

material = st.sidebar.selectbox("Material", ["PVC", "PE (HDPE)"])

if material == "PVC":
    SDR_sel = st.sidebar.selectbox("SDR", list(PVC_SDR.keys()))
    dia = np.array(PVC_SDR[SDR_sel])
    mat_label = f"PVC SDR {SDR_sel}"
else:
    PN_sel = st.sidebar.selectbox("Clase PN", list(PE_PN.keys()))
    dia = np.array(PE_PN[PN_sel])
    mat_label = f"PE100 {PN_sel}"

st.info(f"Material seleccionado: **{mat_label}**")

# ===============================
# FACTOR MULTISALIDAS
# ===============================
F = 2 * Salidas / (2 * Salidas - 1) * ((1 / 2.852) + 0.852**0.5 / (6 * Salidas**2))

# ===============================
# SOLUCIÓN UN DIÁMETRO
# ===============================
st.header("🔹 Solución con un diámetro")

sol1 = []
for d in dia:
    A = np.pi * (d / 2000)**2
    V = Q / A / 3600
    HF = 1.131e9 * (Q / C)**1.852 * LL * d**-4.872 * F
    sol1.append({
        "Diámetro (mm)": d,
        "Velocidad (m/s)": round(V, 2),
        "HF (m)": round(HF, 2),
        "Cumple": V <= 3 and HF <= HF_disp
    })

df1 = pd.DataFrame(sol1)
st.dataframe(df1, use_container_width=True)

df1_ok = df1[df1["Cumple"]]

d1 = None
if not df1_ok.empty:
    d1 = df1_ok.iloc[0]["Diámetro (mm)"]
    st.success(f"Diámetro recomendado: **{d1} mm**")

# ===============================
# SOLUCIÓN DOS DIÁMETROS
# ===============================
st.header("🔹 Solución con dos diámetros")

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

        HF = (
            1.131e9 * (Q/C)**1.852 * L1 * d_up**-4.872 * F +
            1.131e9 * (Q2/C)**1.852 * L2 * d_dn**-4.872 * F
        )

        if HF <= HF_disp and V1 <= 3 and V2 <= 3:
            sol2 = dict(D1=d_up, L1=L1, V1=V1,
                        D2=d_dn, L2=L2, V2=V2, HF=HF)
            break
    if sol2:
        break

if sol2:
    st.success("Solución progresiva encontrada")
    st.write(sol2)

# ===============================
# TIEMPO DE AVANCE (ALGORITMO DISCRETO)
# ===============================
st.header("⏱️ Tiempo de avance del agua")

df_t = pd.DataFrame()
df_t["salida"] = range(1, Salidas + 1)
df_t["long_acum"] = df_t["salida"] * S

qq = Q + Q_salida
q_tramo = []

for _ in df_t["salida"]:
    qq -= Q_salida
    q_tramo.append(qq)

df_t["q_tramo"] = q_tramo

# --- Un diámetro
A1 = np.pi * (d1 / 2000)**2
df_t["v_tramo"] = df_t["q_tramo"] / A1 / 3600
df_t["t_tramo"] = S / df_t["v_tramo"]
df_t["t_acum"] = df_t["t_tramo"].cumsum() / 60
t_avance = round(df_t["t_tramo"].sum() / 60, 2)

st.metric("Tiempo de avance (1 diámetro) [min]", t_avance)

# --- Dos diámetros
if sol2:
    df_t["v_tramo_comb"] = df_t.apply(
        lambda r: r["q_tramo"]/(
            np.pi * (sol2["D1"]/2000)**2
        )/3600 if r["long_acum"] <= sol2["L1"]
        else r["q_tramo"]/(
            np.pi * (sol2["D2"]/2000)**2
        )/3600,
        axis=1
    )

    df_t["t_tramo_comb"] = S / df_t["v_tramo_comb"]
    df_t["t_acum_comb"] = df_t["t_tramo_comb"].cumsum() / 60
    t_avance_comb = round(df_t["t_tramo_comb"].sum() / 60, 2)

    st.metric("Tiempo de avance (2 diámetros) [min]", t_avance_comb)

st.dataframe(df_t, use_container_width=True)

# ===============================
# GRÁFICO VELOCIDAD VS LONGITUD
# ===============================
st.header("📉 Velocidad vs Longitud")

fig, ax = plt.subplots(figsize=(8,4))
ax.plot(df_t["long_acum"], df_t["v_tramo"], label="1 diámetro")

if sol2:
    ax.plot(df_t["long_acum"], df_t["v_tramo_comb"], "--", label="2 diámetros")

ax.axhline(3, linestyle=":", label="V máx")
ax.axhline(0.6, linestyle=":", label="V mín")
ax.set_xlabel("Longitud acumulada (m)")
ax.set_ylabel("Velocidad (m/s)")
ax.grid(True)
ax.legend()

st.pyplot(fig)
fig.savefig("grafico_velocidad.png", dpi=300)

# ===============================
# EXPORTAR PDF
# ===============================
st.header("📄 Exportar memoria de cálculo")

if st.button("Generar PDF"):
    pdf = "Secundaria_Riego.pdf"
    doc = SimpleDocTemplate(pdf, pagesize=letter)
    styles = getSampleStyleSheet()
    e = []

    e.append(Paragraph("<b>SECUNDARIA DE RIEGO</b>", styles["Title"]))
    e.append(Paragraph(f"Material: {mat_label}", styles["Normal"]))
    e.append(Paragraph(f"Caudal = {Q} m³/h | Longitud = {LL} m", styles["Normal"]))
    e.append(Paragraph(f"Tiempo de avance = {t_avance} min", styles["Normal"]))

    if sol2:
        e.append(Paragraph(f"Tiempo avance combinado = {t_avance_comb} min", styles["Normal"]))

    e.append(Spacer(1,10))
    e.append(Image("grafico_velocidad.png", width=14*cm, height=7*cm))

    doc.build(e)
    st.success("PDF generado correctamente")
    st.download_button("Descargar PDF", open(pdf,"rb"), file_name=pdf)
