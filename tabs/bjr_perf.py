import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]

# Nama kolom janjang sesuai Rekap26.csv
COL_JAN_AKT = "Jjg Akt."  
COL_JAN_BGT = "Jjg Bgt."  

st.markdown(f"# ⚖️ BJR to Budget (Kg/Janjang)")
st.markdown(f"**Periode Analisis:** Bulan {pilihan_bulan} & s/d {pilihan_bulan}")

# --- FUNGSI PEWARNAAN TABEL SESUAI LOGIKA BARU BJR ---
def style_gap(val):
    # val adalah nilai Gap_Pct (Aktual % - 100%)
    if val > 0:
        bg = '#00B050'  # Hijau
        color = 'white'
    elif -5 <= val < 0:
        bg = '#FF8C00'  # Oranye
        color = 'white'
    elif val < -5:
        bg = '#FF0000'  # Merah
        color = 'white'
    else:
        bg = 'transparent'
        color = 'black'
    return f'background-color: {bg}; color: {color}; font-weight: bold; font-size: 11px;'

# =========================================================================
# 📊 SECTION 1: PROSES DATA LEVEL KEBUN (BULANAN & YTD)
# =========================================================================
df_murni_bln = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()
df_kebun_prod_bln = df_murni_bln.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', COL_JAN_AKT: 'sum', COL_JAN_BGT: 'sum'}).reset_index()

df_kebun_prod_bln['BJR Akt.'] = df_kebun_prod_bln['Kg Akt.'] / df_kebun_prod_bln[COL_JAN_AKT]
df_kebun_prod_bln['BJR Bgt.'] = df_kebun_prod_bln['Kg Bgt.'] / df_kebun_prod_bln[COL_JAN_BGT]
df_kebun_prod_bln["Persen"] = (df_kebun_prod_bln["BJR Akt."] / df_kebun_prod_bln["BJR Bgt."] * 100).fillna(0)
df_kebun_prod_bln["Gap_Bjr"] = df_kebun_prod_bln["BJR Akt."] - df_kebun_prod_bln["BJR Bgt."]
df_kebun_prod_bln["Gap_Pct"] = df_kebun_prod_bln["Persen"] - 100
df_kebun_bln = df_kebun_prod_bln.sort_values(by="Kebun").reset_index(drop=True)
df_kebun_bln.insert(0, 'No', range(1, 1 + len(df_kebun_bln)))

idx_bulan = list_bulan.index(pilihan_bulan)
df_akum_ytd = df_raw[df_raw['Bulan'].isin(list_bulan[:idx_bulan + 1])].copy()
df_kebun_prod_ytd = df_akum_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', COL_JAN_AKT: 'sum', COL_JAN_BGT: 'sum'}).reset_index()

df_kebun_prod_ytd['BJR Akt.'] = df_kebun_prod_ytd['Kg Akt.'] / df_kebun_prod_ytd[COL_JAN_AKT]
df_kebun_prod_ytd['BJR Bgt.'] = df_kebun_prod_ytd['Kg Bgt.'] / df_kebun_prod_ytd[COL_JAN_BGT]
df_kebun_prod_ytd["Persen"] = (df_kebun_prod_ytd["BJR Akt."] / df_kebun_prod_ytd["BJR Bgt."] * 100).fillna(0)
df_kebun_prod_ytd["Gap_Bjr"] = df_kebun_prod_ytd["BJR Akt."] - df_kebun_prod_ytd["BJR Bgt."]
df_kebun_prod_ytd["Gap_Pct"] = df_kebun_prod_ytd["Persen"] - 100
df_kebun_ytd = df_kebun_prod_ytd.sort_values(by="Kebun").reset_index(drop=True)
df_kebun_ytd.insert(0, 'No', range(1, 1 + len(df_kebun_ytd)))

# --- TAMPILAN GRAFIK & TABEL KEBUN ---
st.markdown("### 🏢 BJR - All Estate Satui")
c_b_b, c_b_y = st.columns(2)

with c_b_b:
    st.subheader(f"BJR Per Kebun Bulan {pilihan_bulan}")
    fig_k_bln = go.Figure()
    fig_k_bln.add_trace(go.Bar(x=df_kebun_bln["Kebun"], y=df_kebun_bln["BJR Akt."], name="Aktual Bulanan", marker_color="#28348A", width=0.4))
    fig_k_bln.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget Bulanan'))
    
    for idx, row in df_kebun_bln.iterrows():
        fig_k_bln.add_shape(type="line", x0=idx - 0.2, x1=idx + 0.2, y0=row["BJR Bgt."], y1=row["BJR Bgt."], line=dict(color="#00B050", width=4))
        fig_k_bln.add_annotation(x=idx, y=0, text=f"{row['Persen']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        
        # Logika Tanda Panah Baru: Hanya muncul jika capaian < 90%
        pct = row["Persen"]
        if pct < 90:
            fig_k_bln.add_annotation(
                x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_k_bln.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_k_bln, use_container_width=True)
    st.dataframe(df_kebun_bln[['No', 'Kebun', 'BJR Akt.', 'BJR Bgt.', 'Gap_Bjr', 'Gap_Pct']].style.format({"BJR Akt.": "{:.2f}", "BJR Bgt.": "{:.2f}", "Gap_Bjr": "{:+.2f}", "Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Gap_Pct']), use_container_width=True, hide_index=True)

with c_b_y:
    st.subheader(f"BJR Per Kebun s/d BI")
    fig_k_ytd = go.Figure()
    fig_k_ytd.add_trace(go.Bar(x=df_kebun_ytd["Kebun"], y=df_kebun_ytd["BJR Akt."], name="Aktual YTD", marker_color="#28348A", width=0.4))
    fig_k_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    for idx, row in df_kebun_ytd.iterrows():
        fig_k_ytd.add_shape(type="line", x0=idx - 0.2, x1=idx + 0.2, y0=row["BJR Bgt."], y1=row["BJR Bgt."], line=dict(color="#00B050", width=4))
        fig_k_ytd.add_annotation(x=idx, y=0, text=f"{row['Persen']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        
        # Logika Tanda Panah Baru YTD: Hanya muncul jika capaian < 90%
        pct = row["Persen"]
        if pct < 90:
            fig_k_ytd.add_annotation(
                x=idx, y=row["BJR Bgt."], ax=idx, ay=row["BJR Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_k_ytd.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_k_ytd, use_container_width=True)
    st.dataframe(df_kebun_ytd[['No', 'Kebun', 'BJR Akt.', 'BJR Bgt.', 'Gap_Bjr', 'Gap_Pct']].style.format({"BJR Akt.": "{:.2f}", "BJR Bgt.": "{:.2f}", "Gap_Bjr": "{:+.2f}", "Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Gap_Pct']), use_container_width=True, hide_index=True)


# =========================================================================
# 📍 SECTION 2: BREAKDOWN DETIL PER AFDELING
# =========================================================================
st.markdown("---")
st.markdown("## 📍 BJR Per Afdeling")

list_kebun_aktif = sorted(df_murni_bln["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat detail breakdown Afdeling:", list_kebun_aktif)

# --- PROSES DATA LEVEL AFDELING ---
df_a_murni = df_murni_bln[df_murni_bln["Kebun"] == pilihan_kebun].copy().sort_values('Afdeling').reset_index(drop=True)
df_a_murni['BJR_Akt'] = df_a_murni['Kg Akt.'] / df_a_murni[COL_JAN_AKT]
df_a_murni['BJR_Bgt'] = df_a_murni['Kg Bgt.'] / df_a_murni[COL_JAN_BGT]
df_a_murni['BJR_Pct'] = (df_a_murni['BJR_Akt'] / df_a_murni['BJR_Bgt'] * 100).fillna(0)
df_a_murni['BJR_Gap_Val'] = df_a_murni['BJR_Akt'] - df_a_murni['BJR_Bgt']
df_a_murni['BJR_Gap_Pct'] = df_a_murni['BJR_Pct'] - 100

df_a_akum = df_akum_ytd[df_akum_ytd["Kebun"] == pilihan_kebun].copy()
df_afd_ytd_grp = df_a_akum.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', COL_JAN_AKT: 'sum', COL_JAN_BGT: 'sum'}).reset_index().sort_values('Afdeling').reset_index(drop=True)
df_afd_ytd_grp['BJR_Akt'] = df_afd_ytd_grp['Kg Akt.'] / df_afd_ytd_grp[COL_JAN_AKT]
df_afd_ytd_grp['BJR_Bgt'] = df_afd_ytd_grp['Kg Bgt.'] / df_afd_ytd_grp[COL_JAN_BGT]
df_afd_ytd_grp['BJR_Pct'] = (df_afd_ytd_grp['BJR_Akt'] / df_afd_ytd_grp['BJR_Bgt'] * 100).fillna(0)
df_afd_ytd_grp['BJR_Gap_Val'] = df_afd_ytd_grp['BJR_Akt'] - df_afd_ytd_grp['BJR_Bgt']
df_afd_ytd_grp['BJR_Gap_Pct'] = df_afd_ytd_grp['BJR_Pct'] - 100

c_fig_afd_b, c_fig_afd_y = st.columns(2)

with c_fig_afd_b:
    st.subheader(f"BJR Per Afdeling Bulan {pilihan_bulan}")
    fig_a_b = go.Figure()
    fig_a_b.add_trace(go.Bar(x=df_a_murni["Afdeling"], y=df_a_murni["BJR_Akt"], name="Aktual Bulanan", marker_color="#28348A", width=0.4))
    fig_a_b.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget Bulanan'))
    
    for idx, row in df_a_murni.iterrows():
        fig_a_b.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["BJR_Bgt"], y1=row["BJR_Bgt"], line=dict(color="#00B050", width=4))
        fig_a_b.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
        
        # Logika Tanda Panah Afdeling Bulanan
        pct = row["BJR_Pct"]
        if pct < 90:
            fig_a_b.add_annotation(
                x=idx, y=row["BJR_Bgt"], ax=idx, ay=row["BJR_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_a_b.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_a_b, use_container_width=True)
    st.dataframe(df_a_murni[['Afdeling', 'BJR_Akt', 'BJR_Bgt', 'BJR_Gap_Val', 'BJR_Gap_Pct']].style.format({"BJR_Akt": "{:.2f}", "BJR_Bgt": "{:.2f}", "BJR_Gap_Val": "{:+.2f}", "BJR_Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['BJR_Gap_Pct']), use_container_width=True, hide_index=True)

with c_fig_afd_y:
    st.subheader(f"BJR Per Afdeling s/d BI")
    fig_a_y = go.Figure()
    fig_a_y.add_trace(go.Bar(x=df_afd_ytd_grp["Afdeling"], y=df_afd_ytd_grp["BJR_Akt"], name="YTD Aktual", marker_color="#28348A", width=0.4))
    fig_a_y.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    for idx, row in df_afd_ytd_grp.iterrows():
        fig_a_y.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["BJR_Bgt"], y1=row["BJR_Bgt"], line=dict(color="#00B050", width=4))
        fig_a_y.add_annotation(x=idx, y=0, text=f"{row['BJR_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
        
        # Logika Tanda Panah Afdeling YTD
        pct = row["BJR_Pct"]
        if pct < 90:
            fig_a_y.add_annotation(
                x=idx, y=row["BJR_Bgt"], ax=idx, ay=row["BJR_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_a_y.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_a_y, use_container_width=True)
    st.dataframe(df_afd_ytd_grp[['Afdeling', 'BJR_Akt', 'BJR_Bgt', 'BJR_Gap_Val', 'BJR_Gap_Pct']].style.format({"BJR_Akt": "{:.2f}", "BJR_Bgt": "{:.2f}", "BJR_Gap_Val": "{:+.2f}", "BJR_Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['BJR_Gap_Pct']), use_container_width=True, hide_index=True)