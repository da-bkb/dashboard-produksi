import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"].copy()

st.markdown("### 📅 Analisa Yield Per Periode Makro (Ton/Ha)")

# --- 1. DEFINISI KAMUS PERIODE & BULAN ---
MAP_PERIODE = {
    "Cawu 1": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR"], "bulan_sd": ["JAN", "FEB", "MAR", "APR"]},
    "Cawu 2": {"bulan_tunggal": ["MEI", "JUN", "JUL", "AGS"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS"]},
    "Cawu 3": {"bulan_tunggal": ["SEP", "OKT", "NOV", "DES"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"]},
    "Semester 1": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN"]},
    "Semester 2": {"bulan_tunggal": ["JUL", "AGS", "SEP", "OKT", "NOV", "DES"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"]},
    "Setahun": {"bulan_tunggal": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"], "bulan_sd": ["JAN", "FEB", "MAR", "APR", "MEI", "JUN", "JUL", "AGS", "SEP", "OKT", "NOV", "DES"]}
}

# --- 2. FILTER SELECTION ---
col_f1, col_f2 = st.columns(2)
with col_f1:
    pilihan_periode = st.selectbox("Pilih Periode Analisa:", list(MAP_PERIODE.keys()), key="sb_p_prd")
with col_f2:
    jenis_analisa = st.selectbox("Pilih Basis Perbandingan:", ["Target Budget", "Target Sensus"], key="sb_p_jns")

col_target = 'Kg Bgt.' if jenis_analisa == "Target Budget" else 'Kg Sns.'
label_target = 'Budget' if jenis_analisa == "Target Budget" else 'Sensus'
pct_min, pct_max = (90, 110) if jenis_analisa == "Target Budget" else (95, 105)

bulan_tunggal = MAP_PERIODE[pilihan_periode]["bulan_tunggal"]
bulan_sd = MAP_PERIODE[pilihan_periode]["bulan_sd"]

df_mtd = df_raw[df_raw['Bulan'].isin(bulan_tunggal)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_sd)].copy()

# --- 3. AGREGASI DATA KEBUN ---
luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
luas_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

# Periode Ini
df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', col_target: 'sum'}).reset_index()
df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Target'] = df_k_mtd[col_target] / df_k_mtd['Luas'] / 1000
df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

# s.d Periode Ini
df_k_ytd = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', col_target: 'sum'}).reset_index()
df_k_ytd['Luas'] = df_k_ytd['Kebun'].map(luas_kebun_ytd)
df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Target'] = df_k_ytd[col_target] / df_k_ytd['Luas'] / 1000
df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

# --- 4. LAYOUT GRAFIK BERSEBELAHAN (KEBUN) ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown(f"##### 📊 Yield Per Kebun - {pilihan_periode}")
    fig_mtd = go.Figure()
    fig_mtd.add_trace(go.Bar(
        x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name=label_target))
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < pct_min or row["Pct"] > pct_max:
            fig_mtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True)

with col_g2:
    st.markdown(f"##### 📊 Yield Per Kebun - s.d {pilihan_periode}")
    fig_ytd = go.Figure()
    fig_ytd.add_trace(go.Bar(
        x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    fig_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name=label_target))
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < pct_min or row["Pct"] > pct_max:
            fig_ytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True)

# --- 5. LOGIKA PEWARNAAN TABEL ---
def style_gap_black_pr(val): return 'color: black; font-weight: bold;'
def style_var_fill_kondisional_pr(val):
    if not isinstance(val, (int, float)): return ''
    if jenis_analisa == "Target Budget":
        if val >= -10: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        elif -20 <= val < -10: return 'background-color: #FFF2CC; color: black; font-weight: bold; text-align: right;'
        elif -30 <= val < -20: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    else:
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown(f"##### 📋 Data Yield Per Kebun - {pilihan_periode}")
    df_t_mtd = pd.DataFrame({'Kebun': df_k_mtd['Kebun'].unique()})
    df_t_mtd['Aktual'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Aktual'])
    df_t_mtd['Target'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Target'])
    df_t_mtd['Var'] = df_t_mtd['Aktual'] - df_t_mtd['Target']
    df_t_mtd['Pct'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Pct']) - 100
    
    luas_site_mtd = luas_kebun_mtd.sum()
    site_mtd_akt = df_mtd['Kg Akt.'].sum() / luas_site_mtd / 1000
    site_mtd_tgt = df_mtd[col_target].sum() / luas_site_mtd / 1000
    site_mtd_var = site_mtd_akt - site_mtd_tgt
    site_mtd_pct = ((site_mtd_akt / site_mtd_tgt * 100) - 100) if site_mtd_tgt > 0 else -100
    
    df_total_mtd = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': site_mtd_akt, 'Target': site_mtd_tgt, 'Var': site_mtd_var, 'Pct': site_mtd_pct}])
    df_final_mtd = pd.concat([df_t_mtd, df_total_mtd], ignore_index=True)
    df_final_mtd.insert(0, 'No', range(1, len(df_final_mtd) + 1))
    df_final_mtd.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', f'{label_target} (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    st.dataframe(df_final_mtd.style.format({'Aktual (Ton/Ha)': '{:,.2f}', f'{label_target} (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black_pr, subset=['Gap (Ton/Ha)']).map(style_var_fill_kondisional_pr, subset=['Var (%)']), use_container_width=True, hide_index=True)

with col_t2:
    st.markdown(f"##### 📋 Data Yield Per Kebun - s.d {pilihan_periode}")
    df_t_ytd = pd.DataFrame({'Kebun': df_k_ytd['Kebun'].unique()})
    df_t_ytd['Aktual'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Aktual'])
    df_t_ytd['Target'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Target'])
    df_t_ytd['Var'] = df_t_ytd['Aktual'] - df_t_ytd['Target']
    df_t_ytd['Pct'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Pct']) - 100
    
    luas_site_ytd = luas_kebun_ytd.sum()
    site_ytd_akt = df_ytd['Kg Akt.'].sum() / luas_site_ytd / 1000
    site_ytd_tgt = df_ytd[col_target].sum() / luas_site_ytd / 1000
    site_ytd_var = site_ytd_akt - site_ytd_tgt
    site_ytd_pct = ((site_ytd_akt / site_ytd_tgt * 100) - 100) if site_ytd_tgt > 0 else -100
    
    df_total_ytd = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': site_ytd_akt, 'Target': site_ytd_tgt, 'Var': site_ytd_var, 'Pct': site_ytd_pct}])
    df_final_ytd = pd.concat([df_t_ytd, df_total_ytd], ignore_index=True)
    df_final_ytd.insert(0, 'No', range(1, len(df_final_ytd) + 1))
    df_final_ytd.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', f'{label_target} (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    st.dataframe(df_final_ytd.style.format({'Aktual (Ton/Ha)': '{:,.2f}', f'{label_target} (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black_pr, subset=['Gap (Ton/Ha)']).map(style_var_fill_kondisional_pr, subset=['Var (%)']), use_container_width=True, hide_index=True)

# --- 6. SUB DETAIL PER AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
list_kebun = sorted(df_raw['Kebun'].dropna().unique())
kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", list_kebun, key="sb_prd_afd_p")

df_m_afd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].copy()
df_y_afd = df_ytd[df_ytd['Kebun'] == kebun_terpilih].copy()

if not df_m_afd.empty:
    luas_afd_mtd = df_m_afd.groupby('Afdeling')['Luas'].first()
    luas_afd_ytd = df_y_afd.groupby('Afdeling')['Luas'].first()

    df_a_mtd = df_m_afd.groupby('Afdeling').agg({'Kg Akt.': 'sum', col_target: 'sum'}).reset_index()
    df_a_mtd['Luas'] = df_a_mtd['Afdeling'].map(luas_afd_mtd)
    df_a_mtd['Aktual'] = df_a_mtd['Kg Akt.'] / df_a_mtd['Luas'] / 1000
    df_a_mtd['Target'] = df_a_mtd[col_target] / df_a_mtd['Luas'] / 1000
    df_a_mtd['Pct'] = (df_a_mtd['Aktual'] / df_a_mtd['Target'] * 100).fillna(0)

    df_a_ytd = df_y_afd.groupby('Afdeling').agg({'Kg Akt.': 'sum', col_target: 'sum'}).reset_index()
    df_a_ytd['Luas'] = df_a_ytd['Afdeling'].map(luas_afd_ytd)
    df_a_ytd['Aktual'] = df_a_ytd['Kg Akt.'] / df_a_ytd['Luas'] / 1000
    df_a_ytd['Target'] = df_a_ytd[col_target] / df_a_ytd['Luas'] / 1000
    df_a_ytd['Pct'] = (df_a_ytd['Aktual'] / df_a_ytd['Target'] * 100).fillna(0)

    col_ga1, col_ga2 = st.columns(2)
    with col_ga1:
        st.markdown(f"##### 📊 Yield Per Afdeling ({kebun_terpilih}) - {pilihan_periode}")
        fig_amtd = go.Figure()
        fig_amtd.add_trace(go.Bar(x=df_a_mtd["Afdeling"], y=df_a_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_mtd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_amtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name=label_target))
        for idx, row in df_a_mtd.iterrows():
            fig_amtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < pct_min or row["Pct"] > pct_max:
                fig_amtd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_amtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_amtd, use_container_width=True)

    with col_ga2:
        st.markdown(f"##### 📊 Yield Per Afdeling ({kebun_terpilih}) - s.d {pilihan_periode}")
        fig_aytd = go.Figure()
        fig_aytd.add_trace(go.Bar(x=df_a_ytd["Afdeling"], y=df_a_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df_a_ytd["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=11, family="Arial Black")))
        fig_aytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name=label_target))
        for idx, row in df_a_ytd.iterrows():
            fig_aytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < pct_min or row["Pct"] > pct_max:
                fig_aytd.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig_aytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig_aytd, use_container_width=True)

    col_ta1, col_ta2 = st.columns(2)
    with col_ta1:
        st.markdown(f"##### 📋 Data Yield Per Afdeling - {pilihan_periode}")
        df_ta_mtd = pd.DataFrame({'Afdeling': df_a_mtd['Afdeling'].unique()})
        df_ta_mtd['Aktual'] = df_ta_mtd['Afdeling'].map(df_a_mtd.set_index('Afdeling')['Aktual'])
        df_ta_mtd['Target'] = df_ta_mtd['Afdeling'].map(df_a_mtd.set_index('Afdeling')['Target'])
        df_ta_mtd['Var'] = df_ta_mtd['Aktual'] - df_ta_mtd['Target']
        df_ta_mtd['Pct'] = df_ta_mtd['Afdeling'].map(df_a_mtd.set_index('Afdeling')['Pct']) - 100
        df_ta_mtd.insert(0, 'No', range(1, len(df_ta_mtd) + 1))
        df_ta_mtd.columns = ['No', 'Afdeling', 'Aktual (Ton/Ha)', f'{label_target} (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_ta_mtd.style.format({'Aktual (Ton/Ha)': '{:,.2f}', f'{label_target} (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black_pr, subset=['Gap (Ton/Ha)']).map(style_var_fill_kondisional_pr, subset=['Var (%)']), use_container_width=True, hide_index=True)

    with col_ta2:
        st.markdown(f"##### 📋 Data Yield Per Afdeling - s.d {pilihan_periode}")
        df_ta_ytd = pd.DataFrame({'Afdeling': df_a_ytd['Afdeling'].unique()})
        df_ta_ytd['Aktual'] = df_ta_ytd['Afdeling'].map(df_a_ytd.set_index('Afdeling')['Aktual'])
        df_ta_ytd['Target'] = df_ta_ytd['Afdeling'].map(df_a_ytd.set_index('Afdeling')['Target'])
        df_ta_ytd['Var'] = df_ta_ytd['Aktual'] - df_ta_ytd['Target']
        df_ta_ytd['Pct'] = df_ta_ytd['Afdeling'].map(df_a_ytd.set_index('Afdeling')['Pct']) - 100
        df_ta_ytd.insert(0, 'No', range(1, len(df_ta_ytd) + 1))
        df_ta_ytd.columns = ['No', 'Afdeling', 'Aktual (Ton/Ha)', f'{label_target} (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_ta_ytd.style.format({'Aktual (Ton/Ha)': '{:,.2f}', f'{label_target} (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black_pr, subset=['Gap (Ton/Ha)']).map(style_var_fill_kondisional_pr, subset=['Var (%)']), use_container_width=True, hide_index=True)
else:
    st.warning("Tidak ada data Afdeling untuk kebun ini.")