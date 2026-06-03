import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_yield_periodik():
    df_raw = st.session_state["df_raw"].copy()

    st.markdown("### 📅 Analisa Yield Per Periode Makro (Ton/Ha)")

    MAP_PERIODE = {
        "Cawu 1": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR"], "bulan_sd": ["JAN", "FEB", "MAR", "APR"]},
        "Cawu 2": {"bulan_tunggal": ["MEI", "JUN", "JUL", "AGS"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS"]},
        "Semester 1": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN"]},
        "Setahun": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"]}
    }

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        pilihan_periode = st.selectbox("Pilih Periode Analisa:", list(MAP_PERIODE.keys()), key="sb_p_prd")
    with col_f2:
        jenis_analisa = st.selectbox("Pilih Basis Perbandingan:", ["Target Budget", "Target Sensus"], key="sb_p_jns")

    col_target = 'Kg Bgt.' if jenis_analisa == "Target Budget" else 'Kg Sns.'
    bulan_tunggal = MAP_PERIODE[pilihan_periode]["bulan_tunggal"]

    df_mtd = df_raw[df_raw['Bulan'].isin(bulan_tunggal)].copy()
    luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

    df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', col_target: 'sum'}).reset_index()
    df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
    df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Target'] = df_k_mtd[col_target] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

    st.markdown(f"##### 📊 Yield Per Kebun - {pilihan_periode}")
    fig_prd = go.Figure()
    fig_prd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A"))
    st.plotly_chart(fig_prd, use_container_width=True)