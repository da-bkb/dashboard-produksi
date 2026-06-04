import streamlit as st
import pandas as pd
import plotly.graph_objects as go

df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🎯 Yield terhadap Sensus (Ton/Ha)")

# --- 1. FILTER & PERHITUNGAN ---
def get_yield_data(bulan_list):
    df = df_raw[df_raw['Bulan'].isin(bulan_list)].copy()
    df_g = df.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum', 'Luas': 'sum'}).reset_index()
    df_g['Aktual'] = df_g['Kg Akt.'] / df_g['Luas'] / 1000
    df_g['Target'] = df_g['Kg Sns.'] / df_g['Luas'] / 1000
    df_g['Var'] = df_g['Aktual'] - df_g['Target']
    df_g['Pct'] = (df_g['Aktual'] / df_g['Target'] * 100) - 100
    return df_g

# Logika filter Cawu
if pilihan_bulan == 'CAWU I': b_mtd, b_ytd = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == 'CAWU II': b_mtd, b_ytd = ['MEI', 'JUN', 'JUL', 'AGS'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS']
elif pilihan_bulan == 'CAWU III': b_mtd, b_ytd = ['SEP', 'OKT', 'NOV', 'DES'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
else: b_mtd, b_ytd = [pilihan_bulan], [pilihan_bulan]

df_k_mtd, df_k_ytd = get_yield_data(b_mtd), get_yield_data(b_ytd)

# --- 2. GRAFIK (MEMUNCULKAN GRAFIK) ---
col_g1, col_g2 = st.columns(2)
for col, df, title, k in [(col_g1, df_k_mtd, "Bulan Ini", "sns_c1"), (col_g2, df_k_ytd, "s.d Bulan Ini", "sns_c2")]:
    with col:
        st.markdown(f"##### 📊 Grafik Yield - {title}")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Kebun'], y=df['Aktual'], name='Aktual'))
        fig.add_trace(go.Scatter(x=df['Kebun'], y=df['Target'], name='Sensus', mode='lines+markers'))
        st.plotly_chart(fig, use_container_width=True, key=k)

# --- 3. TABEL (LAYOUT RJP - PERBAIKAN VALUE ERROR) ---
def style_var(val): return 'background-color: #A9D08E' if -5 <= val <= 5 else ('background-color: #FF8585' if val < -5 else 'background-color: #FFC000')

col_t1, col_t2 = st.columns(2)
for col, df, title, k in [(col_t1, df_k_mtd, "Bulan Ini", "sns_t1"), (col_t2, df_k_ytd, "s.d Bulan Ini", "sns_t2")]:
    with col:
        st.markdown(f"##### 📋 Data Yield - {title}")
        df_f = df[['Kebun', 'Aktual', 'Target', 'Var', 'Pct']].copy()
        df_f.insert(0, 'No', range(1, len(df_f) + 1))
        df_f.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
        st.dataframe(df_f.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'})
                     .applymap(style_var, subset=['Var (%)']), use_container_width=True, hide_index=True, key=k)