import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# Gunakan nama kolom yang sudah ada (Kg Akt. / Kg Sns.)
st.markdown(f"### 🎯 Yield terhadap Sensus (Ton/Ha)")

# --- 1. PROSES FILTER TIMEFRAME (MTD & YTD) ---
df_mtd = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()

URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STD:
    idx_bulan = URUTAN_BULAN_STD.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STD[:idx_bulan + 1]
else:
    bulan_ytd = [pilihan_bulan_std]

df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- 2. PERHITUNGAN AGREGASI ---
def get_yield_df(df):
    # Agregasi kebun sesuai struktur file
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Sns.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

df_k_mtd = get_yield_df(df_mtd)
df_k_ytd = get_yield_df(df_ytd)

# --- 3. STYLING FUNGSI (SAMA DENGAN JANJANG_SENSUS) ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_sensus_var_fill(val):
    if isinstance(val, (int, float)):
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

# --- 4. TAMPILAN TABEL ---
col_t1, col_t2 = st.columns(2)

def render_table(col, df_input, title):
    with col:
        st.markdown(f"##### 📋 {title}")
        df_tab = df_input[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_tab.columns = ['Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        
        # Tambah baris total
        tot = pd.DataFrame([{'Kebun': 'TOTAL SITE', 
                             'Aktual (Ton/Ha)': df_input['Aktual'].mean(), 
                             'Sensus (Ton/Ha)': df_input['Target'].mean(), 
                             'Gap (Ton/Ha)': df_input['Var'].mean(), 
                             'Var (%)': df_input['Pct'].mean()}])
        
        df_final = pd.concat([df_tab, tot], ignore_index=True)
        df_final.insert(0, 'No', range(1, len(df_final)+1))
        
        st.dataframe(df_final.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_gap_black, subset=['Gap (Ton/Ha)'])
                     .map(style_sensus_var_fill, subset=['Var (%)']), use_container_width=True, hide_index=True)

render_table(col_t1, df_k_mtd, "Data Yield Per Kebun - Bulan Ini")
render_table(col_t2, df_k_ytd, "Data Yield Per Kebun - s.d Bulan Ini")