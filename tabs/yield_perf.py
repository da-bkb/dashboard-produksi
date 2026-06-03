import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def render_yield_perf():
    df_raw = st.session_state["df_raw"].copy()
    pilihan_bulan = st.session_state["pilihan_bulan"]

    st.markdown(f"### 🌱 Yield terhadap Budget (Bulan Operasional: {pilihan_bulan})")

    # Timeframe MTD & YTD
    df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()
    URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
    pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

    if pilihan_bulan_std in URUTAN_BULAN_STD:
        idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
        bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
    else:
        bulan_ytd = [pilihan_bulan_std]
    df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

    # Agregasi Kebun
    luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
    luas_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

    df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
    df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
    df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Target'] = df_k_mtd['Kg Bgt.'] / df_k_mtd['Luas'] / 1000
    df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

    df_k_ytd = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
    df_k_ytd['Luas'] = df_k_ytd['Kebun'].map(luas_kebun_ytd)
    df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Luas'] / 1000
    df_k_ytd['Target'] = df_k_ytd['Kg Bgt.'] / df_k_ytd['Luas'] / 1000
    df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

    # Grafik Bersebelahan
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("##### 📊 Yield Per Kebun - Bulan Ini")
        fig_mtd = go.Figure()
        fig_mtd.add_trace(go.Bar(x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside"))
        fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
        for idx, row in df_k_mtd.iterrows():
            fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_mtd, use_container_width=True)

    with col_g2:
        st.markdown("##### 📊 Yield Per Kebun - s.d Bulan Ini")
        fig_ytd = go.Figure()
        fig_ytd.add_trace(go.Bar(x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside"))
        fig_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget'))
        for idx, row in df_k_ytd.iterrows():
            fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_ytd, use_container_width=True)

    # Tabel Data Kebun
    def style_gap(val): return 'color: black; font-weight: bold;'
    def style_var(val):
        if isinstance(val, (int, float)):
            if val >= -10: return 'background-color: #A9D08E; color: black; font-weight: bold;'
            else: return 'background-color: #FF8585; color: black; font-weight: bold;'
        return ''

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown("##### 📋 Data Yield Per Kebun - Bulan Ini")
        df_t_mtd = pd.DataFrame({'Kebun': df_k_mtd['Kebun'].unique()})
        df_t_mtd['Aktual'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Aktual'])
        df_t_mtd['Budget'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Target'])
        df_t_mtd['Gap'] = df_t_mtd['Aktual'] - df_t_mtd['Budget']
        df_t_mtd['Var (%)'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Pct']) - 100
        st.dataframe(df_t_mtd.style.format({'Aktual': '{:,.2f}', 'Budget': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap, subset=['Gap']).map(style_var, subset=['Var (%)']), use_container_width=True, hide_index=True)

    with col_t2:
        st.markdown("##### 📋 Data Yield Per Kebun - s.d Bulan Ini")
        df_t_ytd = pd.DataFrame({'Kebun': df_k_ytd['Kebun'].unique()})
        df_t_ytd['Aktual'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Aktual'])
        df_t_ytd['Budget'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Target'])
        df_t_ytd['Gap'] = df_t_ytd['Aktual'] - df_t_ytd['Budget']
        df_t_ytd['Var (%)'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Pct']) - 100
        st.dataframe(df_t_ytd.style.format({'Aktual': '{:,.2f}', 'Budget': '{:,.2f}', 'Gap': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap, subset=['Gap']).map(style_var, subset=['Var (%)']), use_container_width=True, hide_index=True)

    # Detail Afdeling Dropdown
    st.markdown("---")
    list_kebun = sorted(df_raw['Kebun'].dropna().unique())
    kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", list_kebun, key="sb_bgt_afd")
    df_m_afd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].copy()
    
    if not df_m_afd.empty:
        df_a_mtd = df_m_afd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
        df_a_mtd['Luas'] = df_a_mtd['Afdeling'].map(df_m_afd.groupby('Afdeling')['Luas'].first())
        df_a_mtd['Aktual'] = df_a_mtd['Kg Akt.'] / df_a_mtd['Luas'] / 1000
        df_a_mtd['Target'] = df_a_mtd['Kg Bgt.'] / df_a_mtd['Luas'] / 1000
        
        st.markdown(f"##### 📊 Yield Per Afdeling ({kebun_terpilih})")
        fig_afd = go.Figure()
        fig_afd.add_trace(go.Bar(x=df_a_mtd["Afdeling"], y=df_a_mtd["Aktual"], name="Aktual", marker_color="#28348A"))
        st.plotly_chart(fig_afd, use_container_width=True)