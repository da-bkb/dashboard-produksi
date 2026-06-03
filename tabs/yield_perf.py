import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Ambil data global dari session state app.py
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]

st.markdown(f"### 🌱 Yield Performance terhadap Budget (Ton/Ha)")

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
df_k_mtd = df_mtd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_k_mtd['Luas'] = df_k_mtd['Kebun'].map(luas_kebun_mtd)
df_k_mtd['Aktual'] = df_k_mtd['Kg Akt.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Target'] = df_k_mtd['Kg Bgt.'] / df_k_mtd['Luas'] / 1000
df_k_mtd['Pct'] = (df_k_mtd['Aktual'] / df_k_mtd['Target'] * 100).fillna(0)

# YTD Level Kebun
df_k_ytd = df_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_k_ytd['Luas'] = df_k_ytd['Kebun'].map(luas_kebun_ytd)
df_k_ytd['Aktual'] = df_k_ytd['Kg Akt.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Target'] = df_k_ytd['Kg Bgt.'] / df_k_ytd['Luas'] / 1000
df_k_ytd['Pct'] = (df_k_ytd['Aktual'] / df_k_ytd['Target'] * 100).fillna(0)

# --- 3. VISUALISASI GRAFIK BERSEBELAHAN DI ATAS ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown(f"##### 📊 Grafik Yield - Bulan Ini ({pilihan_bulan})")
    fig_mtd = go.Figure()
    
    # Batang Aktual
    fig_mtd.add_trace(go.Bar(
        x=df_k_mtd["Kebun"], y=df_k_mtd["Aktual"], name="Aktual MTD", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_mtd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    # Garis Target penanda di Legend
    fig_mtd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget MTD'))
    
    # Render Target Line & Kondisi Panah Merah MTD
    for idx, row in df_k_mtd.iterrows():
        fig_mtd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        
        # Aturan Panah Merah
        if row["Pct"] < 90:
            # Di bawah 90%: Panah mengarah ke ATAS (Ujung di Target, Pangkal di Aktual)
            fig_mtd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
        elif row["Pct"] > 110:
            # Di atas 110%: Panah mengarah ke BAWAH (Ujung di Target, Pangkal di Aktual)
            fig_mtd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
            
    fig_mtd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_mtd, use_container_width=True)

with col_g2:
    st.markdown(f"##### 📊 Grafik Yield - s.d Bulan Ini (YTD {pilihan_bulan})")
    fig_ytd = go.Figure()
    
    # Batang Aktual YTD
    fig_ytd.add_trace(go.Bar(
        x=df_k_ytd["Kebun"], y=df_k_ytd["Aktual"], name="Aktual YTD", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df_k_ytd["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    # Garis Target penanda di Legend
    fig_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    # Render Target Line & Kondisi Panah Merah YTD
    for idx, row in df_k_ytd.iterrows():
        fig_ytd.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        
        # Aturan Panah Merah
        if row["Pct"] < 90:
            # Di bawah 90%: Panah mengarah ke ATAS (Ujung di Target, Pangkal di Aktual)
            fig_ytd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
        elif row["Pct"] > 110:
            # Di atas 110%: Panah mengarah ke BAWAH (Ujung di Target, Pangkal di Aktual)
            fig_ytd.add_annotation(
                x=idx, y=row["Target"], ax=idx, ay=row["Aktual"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000'
            )
            
    fig_ytd.update_layout(template="plotly_white", yaxis_title="Ton/Ha", margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_ytd, use_container_width=True)

st.markdown("---")

# --- 4. DATA FRAME COMPILATION FOR MTD & YTD TABLE ---
st.markdown(f"##### 📋 Tabel Summary Yield Performa (MTD vs YTD)")

df_t_kebun = pd.DataFrame({'Kebun': df_k_mtd['Kebun'].unique()})

# Mapping data MTD
df_t_kebun['MTD_Akt'] = df_t_kebun['Kebun'].map(df_k_mtd.set_index('Kebun')['Aktual'])
df_t_kebun['MTD_Bgt'] = df_t_kebun['Kebun'].map(df_k_mtd.set_index('Kebun')['Target'])
df_t_kebun['MTD_Var'] = df_t_kebun['MTD_Akt'] - df_t_kebun['MTD_Bgt']
df_t_kebun['MTD_Var_Pct'] = (df_t_kebun['MTD_Var'] / df_t_kebun['MTD_Bgt']) * 100

# Mapping data YTD
df_t_kebun['YTD_Akt'] = df_t_kebun['Kebun'].map(df_k_ytd.set_index('Kebun')['Aktual'])
df_t_kebun['YTD_Bgt'] = df_t_kebun['Kebun'].map(df_k_ytd.set_index('Kebun')['Target'])
df_t_kebun['YTD_Var'] = df_t_kebun['YTD_Akt'] - df_t_kebun['YTD_Bgt']
df_t_kebun['YTD_Var_Pct'] = (df_t_kebun['YTD_Var'] / df_t_kebun['YTD_Bgt']) * 100

# Kalkulasi TOTAL SITE
luas_site_mtd, luas_site_ytd = luas_kebun_mtd.sum(), luas_kebun_ytd.sum()
site_mtd_akt = df_mtd['Kg Akt.'].sum() / luas_site_mtd / 1000
site_mtd_bgt = df_mtd['Kg Bgt.'].sum() / luas_site_mtd / 1000
site_mtd_var = site_mtd_akt - site_mtd_bgt

site_ytd_akt = df_ytd['Kg Akt.'].sum() / luas_site_ytd / 1000
site_ytd_bgt = df_ytd['Kg Bgt.'].sum() / luas_site_ytd / 1000
site_ytd_var = site_ytd_akt - site_ytd_bgt

df_total = pd.DataFrame([{
    'Kebun': 'TOTAL SITE',
    'MTD_Akt': site_mtd_akt, 'MTD_Bgt': site_mtd_bgt, 'MTD_Var': site_mtd_var, 'MTD_Var_Pct': (site_mtd_var/site_mtd_bgt)*100,
    'YTD_Akt': site_ytd_akt, 'YTD_Bgt': site_ytd_bgt, 'YTD_Var': site_ytd_var, 'YTD_Var_Pct': (site_ytd_var/site_ytd_bgt)*100
}])

df_final = pd.concat([df_t_kebun, df_total], ignore_index=True)
df_final.insert(0, 'No', range(1, len(df_final) + 1))

df_final.columns = [
    'No', 'Kebun', 
    'Akt (MTD)', 'Bgt (MTD)', 'Var (MTD)', 'Var MTD (%)',
    'Akt (YTD)', 'Bgt (YTD)', 'Var (YTD)', 'Var YTD (%)'
]

def style_variance(val):
    if isinstance(val, (int, float)):
        color = 'red' if val < 0 else 'green'
        return f'color: {color}; font-weight: bold;'
    return ''

st.dataframe(
    df_final.style.format({
        'Akt (MTD)': '{:,.2f}', 'Bgt (MTD)': '{:,.2f}', 'Var (MTD)': '{:+,.2f}', 'Var MTD (%)': '{:+,.2f}%',
        'Akt (YTD)': '{:,.2f}', 'Bgt (YTD)': '{:,.2f}', 'Var (YTD)': '{:+,.2f}', 'Var YTD (%)': '{:+,.2f}%'
    }).map(style_variance, subset=['Var (MTD)', 'Var MTD (%)', 'Var (YTD)', 'Var YTD (%)']),
    use_container_width=True,
    hide_index=True
)