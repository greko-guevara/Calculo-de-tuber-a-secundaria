import streamlit as st
import pandas as pd
import numpy as np

st.title("Diseño de tuberías secundarias")
st.write("Prof. Gregory Guevara — Riego & Drenaje / Universidad EARTH")

# ---- ENTRADAS ----
st.header("Entradas del sistema")

Q = st.number_input("Caudal (m³/h)", min_value=0.0, step=0.1)
S = st.number_input("Espaciamiento entre salidas (m)", min_value=0.0, step=0.1)
L = st.number_input("Largo de tubería (m)", min_value=0.0, step=0.1)
HF = st.number_input("Pérdidas por fricción disponibles (m)", min_value=0.0, step=0.1)

if st.button("Calcular"):

    C = 150
    Salidas = L / S
    F = 2 * Salidas / (2 * Salidas - 1) * ((1/2.852) + 0.852**0.5 / (6 * Salidas**2))
    Q_salida = Q / Salidas

    dia = [39.8,45.9,57.38,84.58,108.72,160.08,208.42,259.75,308.05,369.7]
    LL = L
    LLL = 0
    n = -1
    HF3 = HF

    # --- BÚSQUEDA DEL DIÁMETRO ---
    for j in dia:
        HF1 = (1.131e9 * (Q/C)**1.852 * L * j**-4.872 * F)

        if j == 39.8:
            jj = 0
        else:
            n += 1
            jj = dia[n]

        Area = np.pi * (j/2000)**2
        Vel = Q / Area / 3600

        if Vel > 3:
            continue

        if HF1 < HF:
            while HF3 >= HF:
                L -= S
                LLL = LL - L
                Salida1 = L/S
                Salida2 = LLL/S

                F1 = 2 * Salida1 / (2 * Salida1 - 1) * ((1/2.852) + 0.852**0.5/(6*Salida1**2))
                F2 = 2 * Salida2 / (2 * Salida2 - 1) * ((1/2.852) + 0.852**0.5/(6*Salida2**2))

                Area2 = np.pi * (jj/2000)**2
                Q2 = Q * L / LL
                Vel2 = Q2 / Area2 / 3600

                HF3 = (1.131e9*(Q2/C)**1.852*L*jj**-4.872*F1) + \
                      (1.131e9*(Q/C)**1.852*LLL*j**-4.872*F2)

            break

    # --- CÁLCULO TIEMPO DE AVANCE ---
    df = pd.DataFrame(columns=["salidas","long_acum","q_tramo","v_tramo","t_tramo"])

    a = range(1, int(Salidas)+1)
    qq = Q + Q_salida
    ss = 0

    for x in a:
        qq -= Q_salida
        ss += S
        df.loc[x,"salidas"] = j
        df.loc[x,"long_acum"] = ss
        df.loc[x,"q_tramo"] = qq

    df["v_tramo"] = df["q_tramo"] / Area / 3600
    df["t_tramo"] = S / df["v_tramo"]
    df["t_tramo_acum"] = df["t_tramo"].cumsum() / 60
    t_avance = round(df["t_tramo"].sum() / 60, 2)

    # COMBINADO
    df["v_tramo_comb"] = np.where(
        df["long_acum"] < LLL,
        df["v_tramo"],
        df["q_tramo"] / Area2 / 3600
    )

    df["t_tramo_comb"] = S / df["v_tramo_comb"]
    df["t_tramo_comb_acum"] = df["t_tramo_comb"].cumsum() / 60
    t_avance_comb = round(df["t_tramo_comb"].sum() / 60, 2)

    # ---- RESULTADOS ----
    st.header("Solución con un diámetro")
    st.write(f"**Diámetro sugerido:** {j} mm")
    st.write(f"**Pérdidas por fricción:** {round(HF1,2)} m")
    st.write(f"**Velocidad:** {round(Vel,2)} m/s")
    st.write(f"**Tiempo de avance:** {t_avance} min")

    st.header("Solución con dos diámetros")
    st.write(f"**Primer diámetro / largo:** {j} mm × {round(LLL,2)} m")
    st.write(f"**Segundo diámetro / largo:** {jj} mm × {round(L,2)} m")
    st.write(f"**Pérdidas:** {round(HF3,2)} m")
    st.write(f"**Velocidades:** {round(Vel,2)} m/s y {round(Vel2,2)} m/s")
    st.write(f"**Tiempo avance combinado:** {t_avance_comb} min")

    st.subheader("Tabla detallada")
    st.dataframe(df)
