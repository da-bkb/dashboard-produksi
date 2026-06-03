import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# Judul utama bersih sesuai format seragam
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

# --- 2. PERHITUNGAN AGREGASI DATA KEBUN ---
luas_kebun_mtd = df_mtd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
luas_kebun_ytd = df_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()

# MTD Level Kebun
df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Target'] = df_k_mtd['Kg Sns.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

# YTD Level Kebun
df_k_ytd = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
df_k_ytd['Luas'] = df_k_ytd['Kebun'].map(luas_kebun_ytd)
df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Target'] = df_k_ytd['Kg Sns.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

# --- 3. LAYOUT GRAFIK BERSEBELAHAN (KEBUN) ---
col_g1, col_g2 = st.columns(2)
# (Bagian grafik tidak dirubah sesuai permintaan Bapak)
for col, df, title in [(col_g1, df_k_mtd, "Bulan Ini"), (col_g2, df_k_ytd, "s.d Bulan Ini")]:
    with col:
        st.markdown(f"##### 📊 Yield Per Kebun - {title}")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["Kebun"], y=df["Aktual"], name="Aktual", marker_color="#28348A", width=0.35, text=[f"{p:,.1f}%" for p in df["Pct"]], textposition="inside", insidetextanchor="start", textfont=dict(color="white", size=12, family="Arial Black")))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
        for idx, row in df.iterrows():
            fig.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
            if row["Pct"] < 95 or row["Pct"] > 105:
                fig.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
        fig.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
        st.plotly_chart(fig, use_container_width=True)

# --- 4. DATA FRAME COMPILATION & STYLING ---
def style_gap_black(val): return 'color: black; font-weight: bold;'
def style_var_fill_koreksi(val):
    if isinstance(val, (int, float)):
        if val > 5: return 'background-color: #FFC000; color: black; font-weight: bold; text-align: right;'
        elif -5 <= val <= 5: return 'background-color: #A9D08E; color: black; font-weight: bold; text-align: right;'
        else: return 'background-color: #FF8585; color: black; font-weight: bold; text-align: right;'
    return ''

col_t1, col_t2 = st.columns(2)
with col_t1:
    st.markdown("##### 📋 Data Yield Per Kebun - Bulan Ini")
    df_f = df_k_mtd.copy()
    df_f['Var'] = df_f['Aktual'] - df_f['Target']
    # Total Site
    tot = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': df_f['Kg Akt.'].sum()/df_f['Luas'].sum()/1000, 'Target': df_f['Kg Sns.'].sum()/df_f['Luas'].sum()/1000}])
    tot['Var'] = tot['Aktual'] - tot['Target']
    tot['Pct'] = (tot['Aktual']/tot['Target']*100) - 100
    df_final = pd.concat([df_f[['Kebun','Aktual','Target','Var','Pct']], tot], ignore_index=True)
    df_final.insert(0, 'No', range(1, len(df_final)+1))
    df_final.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    st.dataframe(df_final.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap (Ton/Ha)']).map(style_var_fill_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True)

with col_t2:
    st.markdown("##### 📋 Data Yield Per Kebun - s.d Bulan Ini")
    df_f = df_k_ytd.copy()
    df_f['Var'] = df_f['Aktual'] - df_f['Target']
    tot = pd.DataFrame([{'Kebun': 'TOTAL SITE', 'Aktual': df_f['Kg Akt.'].sum()/df_f['Luas'].sum()/1000, 'Target': df_f['Kg Sns.'].sum()/df_f['Luas'].sum()/1000}])
    tot['Var'] = tot['Aktual'] - tot['Target']
    tot['Pct'] = (tot['Aktual']/tot['Target']*100) - 100
    df_final = pd.concat([df_f[['Kebun','Aktual','Target','Var','Pct']], tot], ignore_index=True)
    df_final.insert(0, 'No', range(1, len(df_final)+1))
    df_final.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    st.dataframe(df_final.style.format({'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'}).map(style_gap_black, subset=['Gap (Ton/Ha)']).map(style_var_fill_koreksi, subset=['Var (%)']), use_container_width=True, hide_index=True)

# --- 5. SUB DETAIL PER AFDELING ---
st.markdown("---")
st.markdown("### 🔎 Detail per Afdeling")
kebun_terpilih = st.selectbox("Pilih Kebun untuk melihat detail Afdeling:", sorted(df_raw['Kebun'].dropna().unique()), key="sb_sns_afd")
df_m_afd = df_mtd[df_mtd['Kebun'] == kebun_terpilih].copy()
df_y_afd = df_ytd[df_ytd['Kebun'] == kebun_terpilih].copy()

if not df_m_afd.empty:
    def calc_afd(df):
        luas = df.groupby('Afdeling')['Luas'].first()
        agg = df.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Sns.': 'sum'}).reset_index()
        agg['Luas'] = agg['Afdeling'].map(luas)
        agg['Aktual'] = agg['Kg Akt.'] / agg['Luas'] / 1000
        agg['Target'] = agg['Kg Sns.'] / agg['Luas'] / 1000
        agg['Var'] = agg['Aktual'] - agg['Target']
        agg['Pct'] = (agg['Aktual'] / agg['Target'] * 100) - 100
        return agg

    df_a_mtd, df_a_ytd = calc_afd(df_m_afd), calc_afd(df_y_afd)
    # Tampilkan tabel Afdeling (menggunakan df_a_mtd/ytd yang sudah punya kolom 'Var')
    st.dataframe(df_a_mtd[['Afdeling', 'Aktual', 'Target', 'Var', 'Pct']].style.format({'Var': '{:+,.2f}', 'Pct': '{:+,.1f}%'}), use_container_width=True)
else:
    st.warning("Tidak ada data Afdeling untuk kebun ini.")