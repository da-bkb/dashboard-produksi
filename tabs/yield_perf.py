import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield terhadap Budget (Ton/Ha)")

# --- 1. PROSES FILTER TIMEFRAME ---
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

if pilihan_bulan == 'CAWU I':
    bulan_mtd, bulan_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II':
    bulan_mtd, bulan_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III':
    bulan_mtd, bulan_ytd = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else:
    bulan_mtd, bulan_ytd = [pilihan_bulan], [pilihan_bulan]

df_mtd = df_raw[df_raw['Bulan'].isin(bulan_mtd)].copy()
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# --- 2. FUNGSI PERHITUNGAN YIELD ---
def calc_yield(df):
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Bgt.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

df_k_mtd = calc_yield(df_mtd)
df_k_ytd = calc_yield(df_ytd)

# --- 3. FUNGSI WARNA KOREKSI ---
def style_var_fill_koreksi(val):
    if isinstance(val, (int, float)):
        if val < -30: return 'background-color: #FF0000; color: white; font-weight: bold; text-align: right;' # Merah
        elif val < -20: return 'background-color: #FF9900; color: black; font-weight: bold; text-align: right;' # Orange
        elif val < -10: return 'background-color: #FFFF00; color: black; font-weight: bold; text-align: right;' # Kuning
        else: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;' # Hijau
    return ''

def style_gap_black(val): return 'color: black; font-weight: bold;'

# --- 4. GRAFIK (MEMUNCULKAN GRAFIK) ---
col_g1, col_g2 = st.columns(2)
for col, df, title, k in [(col_g1, df_k_mtd, "Bulan Ini", "bgt_chart_mtd"), (col_g2, df_k_ytd, "s.d Bulan Ini", "bgt_chart_ytd")]:
    with col:
        st.markdown(f"##### 📊 Grafik Yield - {title}")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Kebun'], y=df['Aktual'], name='Aktual', marker_color='#28348A'))
        fig.add_trace(go.Scatter(x=df['Kebun'], y=df['Target'], name='Budget', line=dict(color='#00B050', width=3)))
        st.plotly_chart(fig, use_container_width=True, key=k)

# --- 5. TABEL KEBUN (LAYOUT RJP) ---
col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, df_k_mtd, "Bulan Ini", "t_bgt_mtd"), (col_t2, df_k_ytd, "s.d Bulan Ini", "t_bgt_ytd")]:
    with col:
        st.markdown(f"##### 📋 Data Yield Per Kebun - {title}")
        df_f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_f.insert(0, 'No', range(1, len(df_f) + 1))
        df_f.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .map(style_gap_black, subset=['Gap (Ton/Ha)'])
                     .map(style_var_fill_koreksi, subset=['Var (%)'])
                     .set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key=k)

# --- 6. DETAIL AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
kb = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", sorted(df_raw['Kebun'].dropna().unique()), key="sb_y_bgt_afd")

df_a_mtd = df_mtd[df_mtd['Kebun'] == kb].copy()
if not df_a_mtd.empty:
    df_a = df_a_mtd.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'sum'}).reset_index()
    df_a['Aktual'] = df_a['Kg Akt.'] / df_a['Luas'] / 1000
    df_a['Target'] = df_a['Kg Bgt.'] / df_a['Luas'] / 1000
    df_a['Var'] = df_a['Aktual'] - df_a['Target']
    df_a['Pct'] = (df_a['Aktual'] / df_a['Target'] * 100) - 100
    
    df_a.insert(0, 'No', range(1, len(df_a)+1))
    df_a.columns = ['No', 'Afdeling', 'Aktual (Ton/Ha)', 'Budget (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    
    st.dataframe(df_a.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Budget (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                 .map(style_gap_black, subset=['Gap (Ton/Ha)'])
                 .map(style_var_fill_koreksi, subset=['Var (%)'])
                 .set_properties(subset=['No'], **{'text-align': 'center'}), use_container_width=True, hide_index=True, key="table_yield_bgt_afd")
