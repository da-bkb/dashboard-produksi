import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_yield_sensus():
    df_raw = st.session_state["df_raw"].copy()
    pilihan_bulan = st.session_state["pilihan_bulan"]

    st.markdown(f"### 🎯 Yield terhadap Sensus (Bulan Operasional: {pilihan_bulan})")

    df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()
    URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

    if pilihan_bulan_std in URUTAN_BULAN_STD:
        idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
        bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
    else:
        bulan_ytd = [pilihan_bulan_std]
    df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

    luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
    luas_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

    df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
    df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
    df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Target'] = df_k_mtd['Kg Sns.'] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("##### 📊 Yield Per Kebun - Bulan Ini")
        fig_mtd = go.Figure()
        fig_mtd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside"))
        fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
        for idx, row in df_k_mtd.iterrows():
            fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_mtd, use_container_width=True)
        
    with col_g2:
        st.write("*(Grafik s.d Bulan Ini mengikuti basis perhitungan Sensus)*")