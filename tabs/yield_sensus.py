import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🎯 Yield terhadap Sensus (Ton/Ha)")

# --- LOGIKA FILTER ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
if pilihan_bulan == 'CAWU I': bulan_mtd, bulan_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II': bulan_mtd, bulan_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III': bulan_mtd, bulan_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else: bulan_mtd, bulan_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd, df_ytd = df_raw[df_raw['Bulan'].isin(bulan_mtd)].copy(), df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

def calc_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Sns.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

# --- TABEL DESAIN RJP ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_sensus_var_fill(val):
    if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
    elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
    else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'

col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, calc_yield(df_mtd), "Bulan Ini", "table_yield_sns_kebun_mtd"), 
                         (col_t2, calc_yield(df_ytd), f"s.d {pilihan_bulan}", "table_yield_sns_kebun_ytd")]:
    with col:
        st.markdown(f"##### 📋 Data Yield Per Kebun - {title}")
        df_f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_f.columns = ['Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        df_f.insert(0, 'No', range(1, len(df_f) + 1))
        st.dataframe(df_f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_gap_black, subset=['Gap (Ton/Ha)']).map(style_sensus_var_fill, subset=['Var (%)'])
                     .set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key=k)