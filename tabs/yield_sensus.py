import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# Judul utama bersih sesuai format seragam
st.markdown(f"### 🎯 Yield terhadap Sensus (Ton/Ha)")

# --- 1. PROSES FILTER TIMEFRAME BERDASARKAN BULAN / CAWU / SEMESTER ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

if pilihan_bulan in ['CAWU I', 'CAWU II', 'CAWU III']:
    if pilihan_bulan == 'CAWU I':
        bulan_mtd_list, bulan_ytd_list = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
    elif pilihan_bulan == 'CAWU II':
        bulan_mtd_list, bulan_ytd_list = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
    else:
        bulan_mtd_list, bulan_ytd_list = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else:
    bulan_mtd_list, bulan_ytd_list = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(bulan_mtd_list)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd_list)].copy()

# --- 2. PERHITUNGAN AGREGASI DATA KEBUN ---
def calc_k_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Sns.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

df_k_mtd = calc_k_yield(df_mtd)
df_k_ytd = calc_k_yield(df_ytd)

# --- 3. STYLING FUNGSI (SAMA DENGAN JANJANG_SENSUS) ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_sensus_var_fill(val):
    if isinstance(val, (int, float)):
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

# --- 4. TAMPILAN TABEL KE KEBUN ---
col_t1, col_t2 = st.columns(2)
def render_table_kebun(col, df, title, k):
    with col:
        st.markdown(f"##### 📋 {title}")
        df_tab = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_tab.columns = ['Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_tab.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_gap_black, subset=['Gap (Ton/Ha)']).map(style_sensus_var_fill, subset=['Var (%)']), 
                     use_container_width=True, hide_index=True, key=k)

render_table_kebun(col_t1, df_k_mtd, "Data Yield Per Kebun - Bulan Ini", "tbl_sns_mtd")
render_table_kebun(col_t2, df_k_ytd, "Data Yield Per Kebun - s.d Bulan Ini", "tbl_sns_ytd")

# --- 5. SUB DETAIL PER AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
kebun_terpilih = st.selectbox("Pilih Kebun:", sorted(df_raw['Kebun'].dropna().unique()), key="sb_sns_afd")
df_a_mtd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
df_a_mtd['Aktual'] = df_a_mtd['Kg Akt.'] / df_a_mtd['Luas'] / 1000
df_a_mtd['Target'] = df_a_mtd['Kg Sns.'] / df_a_mtd['Luas'] / 1000

# Tampilkan tabel afdeling dengan key unik
col_ta1, col_ta2 = st.columns(2)
with col_ta1:
    st.markdown("##### 📋 Data Yield Per Afdeling - Bulan Ini")
    df_a_mtd['Var'] = df_a_mtd['Aktual'] - df_a_mtd['Target']
    df_a_mtd['Pct'] = (df_a_mtd['Aktual'] / df_a_mtd['Target'] * 100) - 100
    st.dataframe(df_a_mtd[['Afdeling', 'Aktual', 'Target', 'Var', 'Pct']].style.format({'Var': '{:+,.2f}', 'Pct': '{:+,.1f}%'})
                 .map(style_sensus_var_fill, subset=['Pct']), use_container_width=True, key="tbl_sns_afd_mtd")