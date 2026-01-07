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


with st.expander("📘 Ayuda teórica – Fundamentos hidráulicos"):
    st.markdown(r"""
## 1. Flujo en tuberías con múltiples salidas

En una tubería secundaria de riego, el caudal **no es constante** a lo largo de la conducción.
Cada salida extrae una fracción del caudal total, por lo que el caudal remanente en el tramo *i* es:

\[
Q_i = Q - i \cdot q_{\text{salida}}
\]

donde:
- \(Q\) = caudal total de entrada \([m^3/h]\)
- \(q_{\text{salida}}\) = caudal por salida
- \(i\) = número de salidas aguas arriba del tramo

Este comportamiento implica que:
- la velocidad varía con la longitud
- las pérdidas por fricción deben corregirse
- el tiempo de avance **no puede calcularse con una sola velocidad promedio**

---

## 2. Pérdidas por fricción – Fórmula de Hazen–Williams

Para tuberías a presión, se utiliza la ecuación de Hazen–Williams:

\[
h_f = 10.67 \cdot \frac{L \cdot Q^{1.852}}{C^{1.852} \cdot D^{4.87}}
\]

En esta aplicación se utiliza la forma adaptada a:
- \(Q\) en \(m^3/h\)
- \(D\) en mm
- \(L\) en m

\[
h_f = 1.131 \times 10^9 \cdot \left(\frac{Q}{C}\right)^{1.852}
\cdot L \cdot D^{-4.872}
\]

---

## 3. Factor de corrección por múltiples salidas

Debido a la disminución progresiva del caudal, se introduce un factor de corrección \(F\):

\[
F = \frac{2n}{2n - 1}
\left[
\frac{1}{2.852} + \frac{\sqrt{0.852}}{6n^2}
\right]
\]

donde:
- \(n\) = número total de salidas

Este factor permite estimar correctamente la pérdida total por fricción
en tuberías con extracción distribuida.

---

## 4. Velocidad del flujo

La velocidad se calcula como:

\[
V = \frac{Q}{A}
\]

donde el área hidráulica es:

\[
A = \frac{\pi D^2}{4}
\]

Criterio usual de diseño:
- \(V \leq 3.0\ m/s\)

---

## 5. Tiempo de avance – Enfoque discreto (criterio correcto)

El **tiempo de avance** es el tiempo que tarda el agua en llegar desde la entrada
hasta el extremo final del sistema.

Dado que el caudal (y la velocidad) varían a lo largo de la tubería,
el tiempo de avance se calcula **tramo a tramo**:

\[
t_{\text{avance}} = \sum_{i=1}^{n} \frac{\Delta L}{V_i}
\]

donde:
- \(\Delta L\) = longitud entre salidas
- \(V_i\) = velocidad real en el tramo *i*

Este enfoque es fundamental para:
- fertirriego
- análisis de uniformidad
- evaluación del tiempo de respuesta hidráulica

---

## 6. Interpretación de los gráficos

Los gráficos presentan simultáneamente:

- **Velocidad (línea continua)**  
- **Tiempo acumulado (puntos)**  

permitiendo:
- identificar tramos críticos
- evaluar el efecto del cambio de diámetro
- comparar diseños hidráulicos de forma visual y didáctica
""")



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
st.header("📊 Análisis hidráulico: velocidad y tiempo de avance")

fig, axes = plt.subplots(1, 2, figsize=(16,5), sharex=True)

# ===============================
# SUBPLOT 1 – UN DIÁMETRO
# ===============================
ax1 = axes[0]
ax1.set_title("Un diámetro")
ax1.set_xlabel("Longitud acumulada (m)")
ax1.set_ylabel("Velocidad (m/s)", color="tab:red")
ax1.plot(df_t["long_acum"], df_t["v_tramo"], color="tab:red", linewidth=2)
ax1.tick_params(axis='y', labelcolor="tab:red")
ax1.grid(True, linestyle=":", alpha=0.6)

ax1b = ax1.twinx()
ax1b.set_ylabel("Tiempo acumulado (min)", color="tab:blue")
ax1b.scatter(df_t["long_acum"], df_t["t_acum"], color="tab:blue", s=25)
ax1b.tick_params(axis='y', labelcolor="tab:blue")

# ===============================
# SUBPLOT 2 – DOS DIÁMETROS
# ===============================
ax2 = axes[1]
ax2.set_title("Dos diámetros progresivos")
ax2.set_xlabel("Longitud acumulada (m)")
ax2.set_ylabel("Velocidad (m/s)", color="tab:red")
ax2.plot(df_t["long_acum"], df_t["v_tramo_comb"], color="tab:red", linewidth=2)
ax2.tick_params(axis='y', labelcolor="tab:red")
ax2.grid(True, linestyle=":", alpha=0.6)

ax2b = ax2.twinx()
ax2b.set_ylabel("Tiempo acumulado (min)", color="tab:blue")
ax2b.scatter(df_t["long_acum"], df_t["t_acum_comb"], color="tab:blue", s=25)
ax2b.tick_params(axis='y', labelcolor="tab:blue")

fig.tight_layout()
st.pyplot(fig)
fig.savefig("grafico_velocidad_tiempo.png", dpi=300)


# ===============================
# ONE PAGE – MEMORIA DE CÁLCULO
# ===============================
from reportlab.platypus import TableStyle
from reportlab.lib import colors


styles = getSampleStyleSheet()
story = []

story.append(Paragraph(
    "<b>Memoria de Cálculo Hidráulico – Tubería Secundaria de Riego</b>",
    styles["Title"]
))
story.append(Spacer(1, 8))

# ===============================
# DATOS DE ENTRADA
# ===============================
story.append(Paragraph("<b>Datos de entrada</b>", styles["Heading2"]))

tabla_entrada = Table([
    ["Parámetro", "Valor"],
    ["Caudal total Q (m³/h)", f"{Q}"],
    ["Longitud total L (m)", f"{LL}"],
    ["Espaciamiento entre salidas (m)", f"{S}"],
    ["Número de salidas", f"{Salidas}"],
    ["Pérdida disponible (m)", f"{HF_disp}"],
    ["Coeficiente Hazen–Williams C", f"{C}"],
    ["Material", mat_label],
], colWidths=[7*cm, 6*cm])

tabla_entrada.setStyle(TableStyle([
    ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
    ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
]))

story.append(tabla_entrada)
story.append(Spacer(1, 10))

# ===============================
# RESULTADOS HIDRÁULICOS
# ===============================
story.append(Paragraph("<b>Resultados hidráulicos</b>", styles["Heading2"]))

tabla_res = [
    ["Escenario", "Resultado"],
    ["Diámetro único recomendado (mm)", f"{d1}"],
    ["Tiempo de avance – 1 diámetro (min)", f"{t_avance}"],
]

if sol2:
    tabla_res += [
        ["Diámetro inicial (mm)", f"{sol2['D1']}"],
        ["Diámetro final (mm)", f"{sol2['D2']}"],
        ["Longitud cambio diámetro (m)", f"{sol2['L1']}"],
        ["Tiempo de avance – 2 diámetros (min)", f"{t_avance_comb}"],
    ]

tabla_resultados = Table(tabla_res, colWidths=[7*cm, 6*cm])
tabla_resultados.setStyle(TableStyle([
    ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
    ("BACKGROUND", (0,0), (-1,0), colors.whitesmoke),
]))

story.append(tabla_resultados)
story.append(Spacer(1, 10))

# ===============================
# GRÁFICO
# ===============================
story.append(Paragraph("<b>Análisis gráfico</b>", styles["Heading2"]))
story.append(Paragraph(
    "Variación de la velocidad y tiempo de avance a lo largo del manifold.",
    styles["Normal"]
))
story.append(Spacer(1, 6))

story.append(Image("grafico_velocidad_tiempo.png", width=16*cm, height=6*cm))

# ===============================
# CONSTRUCCIÓN PDF
# ===============================
doc = SimpleDocTemplate(
    "memoria_calculo_secundaria.pdf",
    pagesize=letter,
    rightMargin=1.5*cm,
    leftMargin=1.5*cm,
    topMargin=1.5*cm,
    bottomMargin=1.5*cm
)

doc.build(story)
