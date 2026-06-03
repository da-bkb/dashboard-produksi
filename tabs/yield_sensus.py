import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

# Judul utama bersih tanpa kata Performance / Performa
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

# --- 3. LAYOUT GRAFIK BERSEBELAHAN ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown(f"##### 📊 Grafik Yield - Bulan Ini ({pilihan_bulan})")
    fig_mtd = go.Figure()
    
    fig_mtd.add_trace(go.Bar(
        x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
    
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95 or row["Pct"] > 105:
            fig_mtd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
            
    fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True)

with col_g2:
    st.markdown(f"##### 📊 Grafik Yield - s.d Bulan Ini ({pilihan_bulan})")
    fig_ytd = go.Figure()
    
    fig_ytd.add_trace(go.Bar(
        x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    fig_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Sensus'))
    
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 95 or row["Pct"] > 105:
            fig_ytd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
            
    fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True)


# --- 4. DATA FRAME COMPILATION & STYLING FOR TABLES ---
def style_variance(val):
    if isinstance(val, (int, float)):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}; font-weight: bold;'
    return ''

# CSS injected untuk membuat Judul Kolom (Header) rata tengah secara global di dataframe
st.markdown("""
    <style>
        th { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

col_t1, col_t2 = st.columns(2)

with col_t1:
    st.markdown(f"##### 📋 Tabel Summary Yield - Bulan Ini ({pilihan_bulan})")
    
    df_t_mtd = pd.DataFrame({'Kebun': df_k_mtd['Kebun'].unique()})
    df_t_mtd['Aktual'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Aktual'])
    df_t_mtd['Sensus'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Target'])
    df_t_mtd['Var'] = df_t_mtd['Aktual'] - df_t_mtd['Sensus']
    
    # RUMUS BARU: Var (%) = % Capaian - 100
    df_t_mtd['Pct'] = df_t_mtd['Kebun'].map(df_k_mtd.set_index('Kebun')['Pct']) - 100
    
    # Total Site MTD
    luas_site_mtd = luas_kebun_mtd.sum()
    site_mtd_akt = df_mtd['Kg Akt.'].sum() / luas_site_mtd / 1000
    site_mtd_sns = df_mtd['Kg Sns.'].sum() / luas_site_mtd / 1000
    site_mtd_var = site_mtd_akt - site_mtd_sns
    site_mtd_pct = ((site_mtd_akt / site_mtd_sns * 100) - 100) if site_mtd_sns > 0 else -100
    
    df_total_mtd = pd.DataFrame([{
        'Kebun': 'TOTAL SITE', 'Aktual': site_mtd_akt, 'Sensus': site_mtd_sns, 'Var': site_mtd_var, 'Pct': site_mtd_pct
    }])
    
    df_final_mtd = pd.concat([df_t_mtd, df_total_mtd], ignore_index=True)
    df_final_mtd.insert(0, 'No', range(1, len(df_final_mtd) + 1))
    
    # KOREKSI NAMA KOLOM SESUAI INSTRUKSI
    df_final_mtd.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    
    st.dataframe(
        df_final_mtd.style.format({
            'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'
        }).map(style_variance, subset=['Gap (Ton/Ha)', 'Var (%)'])
          .set_properties(subset=['No'], **{'text-align': 'center'}),  # KOLOM NO JADI RATA TENGAH
        use_container_width=True, hide_index=True
    )

with col_t2:
    st.markdown(f"##### 📋 Tabel Summary Yield - s.d Bulan Ini ({pilihan_bulan})")
    
    df_t_ytd = pd.DataFrame({'Kebun': df_k_ytd['Kebun'].unique()})
    df_t_ytd['Aktual'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Aktual'])
    df_t_ytd['Sensus'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Target'])
    df_t_ytd['Var'] = df_t_ytd['Aktual'] - df_t_ytd['Sensus']
    
    # RUMUS BARU: Var (%) = % Capaian - 100
    df_t_ytd['Pct'] = df_t_ytd['Kebun'].map(df_k_ytd.set_index('Kebun')['Pct']) - 100
    
    # Total Site YTD
    luas_site_ytd = luas_kebun_ytd.sum()
    site_ytd_akt = df_ytd['Kg Akt.'].sum() / luas_site_ytd / 1000
    site_ytd_sns = df_ytd['Kg Sns.'].sum() / luas_site_ytd / 1000
    site_ytd_var = site_ytd_akt - site_ytd_sns
    site_ytd_pct = ((site_ytd_akt / site_ytd_sns * 100) - 100) if site_ytd_sns > 0 else -100
    
    df_total_ytd = pd.DataFrame([{
        'Kebun': 'TOTAL SITE', 'Aktual': site_ytd_akt, 'Sensus': site_ytd_sns, 'Var': site_ytd_var, 'Pct': site_ytd_pct
    }])
    
    df_final_ytd = pd.concat([df_t_ytd, df_total_ytd], ignore_index=True)
    df_final_ytd.insert(0, 'No', range(1, len(df_final_ytd) + 1))
    
    # KOREKSI NAMA KOLOM SESUAI INSTRUKSI
    df_final_ytd.columns = ['No', 'Kebun', 'Aktual (Ton/Ha)', 'Sensus (Ton/Ha)', 'Gap (Ton/Ha)', 'Var (%)']
    
    st.dataframe(
        df_final_ytd.style.format({
            'Aktual (Ton/Ha)': '{:,.2f}', 'Sensus (Ton/Ha)': '{:,.2f}', 'Gap (Ton/Ha)': '{:+,.2f}', 'Var (%)': '{:+,.1f}%'
        }).map(style_variance, subset=['Gap (Ton/Ha)', 'Var (%)'])
          .set_properties(subset=['No'], **{'text-align': 'center'}),  # KOLOM NO JADI RATA TENGAH
        use_container_width=True, hide_index=True
    )