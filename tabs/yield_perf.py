import streamlit as st
import pandas as pd

# Ambil data dari app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield terhadap Budget (Ton/Ha)")

# --- 1. FILTER OTOMATIS ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
if pilihan_bulan == 'CAWU I': b_mtd, b_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II': b_mtd, b_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III': b_mtd, b_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else: b_mtd, b_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(b_mtd)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(b_ytd)].copy()

# --- 2. FUNGSI PERHITUNGAN ---
def calc_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Bgt.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

df_k_mtd, df_k_ytd = calc_yield(df_mtd), calc_yield(df_ytd)

# --- 3. STYLING ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_budget_var_fill(val):
    if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
    elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
    else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'

# --- 4. TABEL KEBUN (LAYOUT RJP) ---
col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, df_k_mtd, "Bulan Ini", "table_y_bgt_mtd"), (col_t2, df_k_ytd, "s.d Bulan Ini", "table_y_bgt_ytd")]:
    with col:
        st.markdown(f"##### 📋 Data Yield Per Kebun - {title}")
        df_f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_f.columns = ['Kebun', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        df_f.insert(0, 'No', range(1, len(df_f) + 1))
        st.dataframe(df_f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_gap_black, subset=['Gap (Ton/Ha)']).map(style_budget_var_fill, subset=['Var (%)'])
                     .set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key=k)

# --- 5. DETAIL AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
kb = st.selectbox("Pilih Kebun:", sorted(df_raw['Kebun'].unique()), key="sb_y_bgt_afd")
df_a = df_mtd[df_mtd['Kebun'] == kb].groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
df_a['Aktual'], df_a['Target'] = df_a['Kg Akt.']/df_a['Luas']/1000, df_a['Kg Bgt.']/df_a['Luas']/1000
df_a['Var'], df_a['Pct'] = df_a['Aktual'] - df_a['Target'], (df_a['Aktual']/df_a['Target']*100)-100
df_a.insert(0, 'No', range(1, len(df_a)+1))
df_a.columns = ['No', 'Afdeling', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
st.dataframe(df_a.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
             .map(style_budget_var_fill, subset=['Var (%)']), use_container_width=True, hide_index=True, key="table_y_bgt_afd")