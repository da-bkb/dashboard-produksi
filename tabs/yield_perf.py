import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Ambil data global dari session state
df_raw = st.session_state["df_raw"]
pilihan_bulan = st.session_state["pilihan_bulan"]
list_bulan = st.session_state["list_bulan"]

st.markdown(f"# 🌱 Yield to Budget (Ton/ha)")
st.markdown(f"**Periode Analisis:** Bulan {pilihan_bulan} & s/d {pilihan_bulan}")

# --- FUNGSI PEWARNAAN 4 WARNA SUT STYLER TABEL (Kuning Cerah #FFFF00) ---
def style_gap(val):
    persen_capaian = val + 100
    if persen_capaian >= 90:
        bg = '#00B050'  # Hijau
        color = 'white'
    elif persen_capaian >= 80:
        bg = '#FFFF00'  # Kuning Cerah (Sudah Diperbaiki)
        color = 'black'
    elif persen_capaian >= 70:
        bg = '#FF8C00'  # Oranye
        color = 'white'
    else:
        bg = '#FF0000'  # Merah
        color = 'white'
    return f'background-color: {bg}; color: {color}; font-weight: bold; font-size: 11px;'

# =========================================================================
# 📊 SECTION 1: PROSES DATA LEVEL KEBUN (BULANAN & YTD)
# =========================================================================
df_murni_bln = df_raw[df_raw['Bulan'] == pilihan_bulan].copy()
df_kebun_luas_bln = df_murni_bln.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum().reset_index()
df_kebun_prod_bln = df_murni_bln.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_kebun_bln = pd.merge(df_kebun_prod_bln, df_kebun_luas_bln, on='Kebun')
df_kebun_bln['Ton/ha Akt.'] = df_kebun_bln['Kg Akt.'] / df_kebun_bln['Luas'] / 1000
df_kebun_bln['Ton/ha Bgt.'] = df_kebun_bln['Kg Bgt.'] / df_kebun_bln['Luas'] / 1000
df_kebun_bln["Persen"] = (df_kebun_bln["Ton/ha Akt."] / df_kebun_bln["Ton/ha Bgt."] * 100).fillna(0)
df_kebun_bln["Gap_Ton"] = df_kebun_bln["Ton/ha Akt."] - df_kebun_bln["Ton/ha Bgt."]
df_kebun_bln["Gap_Pct"] = df_kebun_bln["Persen"] - 100
df_kebun_bln = df_kebun_bln.sort_values(by="Kebun").reset_index(drop=True)
df_kebun_bln.insert(0, 'No', range(1, 1 + len(df_kebun_bln)))

idx_bulan = list_bulan.index(pilihan_bulan)
df_akum_ytd = df_raw[df_raw['Bulan'].isin(list_bulan[:idx_bulan + 1])].copy()
df_kebun_luas_ytd = df_akum_ytd[df_akum_ytd['Bulan'] == pilihan_bulan].groupby('Kebun')['Luas'].sum().reset_index()
df_kebun_prod_ytd = df_akum_ytd.groupby('Kebun').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum'}).reset_index()
df_kebun_ytd = pd.merge(df_kebun_prod_ytd, df_kebun_luas_ytd, on='Kebun')
df_kebun_ytd['Ton/ha Akt.'] = df_kebun_ytd['Kg Akt.'] / df_kebun_ytd['Luas'] / 1000
df_kebun_ytd['Ton/ha Bgt.'] = df_kebun_ytd['Kg Bgt.'] / df_kebun_ytd['Luas'] / 1000
df_kebun_ytd["Persen"] = (df_kebun_ytd["Ton/ha Akt."] / df_kebun_ytd["Ton/ha Bgt."] * 100).fillna(0)
df_kebun_ytd["Gap_Ton"] = df_kebun_ytd["Ton/ha Akt."] - df_kebun_ytd["Ton/ha Bgt."]
df_kebun_ytd["Gap_Pct"] = df_kebun_ytd["Persen"] - 100
df_kebun_ytd = df_kebun_ytd.sort_values(by="Kebun").reset_index(drop=True)
df_kebun_ytd.insert(0, 'No', range(1, 1 + len(df_kebun_ytd)))

# --- TAMPILAN GRAFIK & TABEL KEBUN ---
st.markdown("### 🏢 Yield - All Estate Satui")
c_y_b, c_y_y = st.columns(2)

with c_y_b:
    st.subheader(f"Yield Per Kebun Bulan {pilihan_bulan}")
    fig_k_bln = go.Figure()
    fig_k_bln.add_trace(go.Bar(x=df_kebun_bln["Kebun"], y=df_kebun_bln["Ton/ha Akt."], name="Aktual Bulanan", marker_color="#28348A", width=0.4))
    fig_k_bln.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget Bulanan'))
    
    for idx, row in df_kebun_bln.iterrows():
        # Garis Target Budget
        fig_k_bln.add_shape(type="line", x0=idx - 0.2, x1=idx + 0.2, y0=row["Ton/ha Bgt."], y1=row["Ton/ha Bgt."], line=dict(color="#00B050", width=4))
        
        # Angka % di dasar batang
        fig_k_bln.add_annotation(x=idx, y=0, text=f"{row['Persen']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        
        # Logika Filter Tanda Panah Kebun Bulanan
        pct = row["Persen"]
        if pct < 90:
            # Panah MERAH naik ke arah budget
            fig_k_bln.add_annotation(
                x=idx, y=row["Ton/ha Bgt."], 
                ax=idx, ay=row["Ton/ha Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
        elif pct > 110:
            # Panah MERAH turun ke arah budget
            fig_k_bln.add_annotation(
                x=idx, y=row["Ton/ha Bgt."], 
                ax=idx, ay=row["Ton/ha Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_k_bln.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_k_bln, use_container_width=True)
    st.dataframe(df_kebun_bln[['No', 'Kebun', 'Ton/ha Akt.', 'Ton/ha Bgt.', 'Gap_Ton', 'Gap_Pct']].style.format({"Ton/ha Akt.": "{:.1f}", "Ton/ha Bgt.": "{:.1f}", "Gap_Ton": "{:+.1f}", "Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Gap_Pct']), use_container_width=True, hide_index=True)

with c_y_y:
    st.subheader(f"Yield Per Kebun s/d BI")
    fig_k_ytd = go.Figure()
    fig_k_ytd.add_trace(go.Bar(x=df_kebun_ytd["Kebun"], y=df_kebun_ytd["Ton/ha Akt."], name="Aktual YTD", marker_color="#28348A", width=0.4))
    fig_k_ytd.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    for idx, row in df_kebun_ytd.iterrows():
        # Garis Target Budget YTD
        fig_k_ytd.add_shape(type="line", x0=idx - 0.2, x1=idx + 0.2, y0=row["Ton/ha Bgt."], y1=row["Ton/ha Bgt."], line=dict(color="#00B050", width=4))
        
        # Angka % di dasar batang YTD
        fig_k_ytd.add_annotation(x=idx, y=0, text=f"{row['Persen']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight="bold"))
        
        # Logika Filter Tanda Panah Kebun YTD
        pct = row["Persen"]
        if pct < 90:
            # Panah MERAH naik ke arah budget
            fig_k_ytd.add_annotation(
                x=idx, y=row["Ton/ha Bgt."], 
                ax=idx, ay=row["Ton/ha Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
        elif pct > 110:
            # Panah MERAH turun ke arah budget
            fig_k_ytd.add_annotation(
                x=idx, y=row["Ton/ha Bgt."], 
                ax=idx, ay=row["Ton/ha Akt."],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_k_ytd.update_layout(height=380, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_k_ytd, use_container_width=True)
    st.dataframe(df_kebun_ytd[['No', 'Kebun', 'Ton/ha Akt.', 'Ton/ha Bgt.', 'Gap_Ton', 'Gap_Pct']].style.format({"Ton/ha Akt.": "{:.1f}", "Ton/ha Bgt.": "{:.1f}", "Gap_Ton": "{:+.1f}", "Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Gap_Pct']), use_container_width=True, hide_index=True)


# =========================================================================
# 📍 SECTION 2: BREAKDOWN DETIL PER AFDELING
# =========================================================================
st.markdown("---")
st.markdown("## 📍 Yield Per Afdeling")

list_kebun_aktif = sorted(df_murni_bln["Kebun"].unique())
pilihan_kebun = st.selectbox("Pilih Kebun untuk melihat detail breakdown Afdeling:", list_kebun_aktif)

# --- PROSES DATA LEVEL AFDELING ---
df_a_murni = df_murni_bln[df_murni_bln["Kebun"] == pilihan_kebun].copy().sort_values('Afdeling').reset_index(drop=True)
df_a_murni['Yield_Akt'] = df_a_murni['Kg Akt.'] / df_a_murni['Luas'] / 1000
df_a_murni['Yield_Bgt'] = df_a_murni['Kg Bgt.'] / df_a_murni['Luas'] / 1000
df_a_murni['Yield_Pct'] = (df_a_murni['Yield_Akt'] / df_a_murni['Yield_Bgt'] * 100).fillna(0)
df_a_murni['Yield_Gap_Ton'] = df_a_murni['Yield_Akt'] - df_a_murni['Yield_Bgt']
df_a_murni['Yield_Gap_Pct'] = df_a_murni['Yield_Pct'] - 100

df_a_akum = df_akum_ytd[df_akum_ytd["Kebun"] == pilihan_kebun].copy()
df_afd_ytd_grp = df_a_akum.groupby('Afdeling').agg({'Kg Akt.': 'sum', 'Kg Bgt.': 'sum', 'Luas': 'first'}).reset_index().sort_values('Afdeling').reset_index(drop=True)
df_afd_ytd_grp['Yield_Akt'] = df_afd_ytd_grp['Kg Akt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Bgt'] = df_afd_ytd_grp['Kg Bgt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Pct'] = (df_afd_ytd_grp['Yield_Akt'] / df_afd_ytd_grp['Yield_Bgt'] * 100).fillna(0)
df_afd_ytd_grp['Yield_Gap_Ton'] = df_afd_ytd_grp['Yield_Akt'] - df_afd_ytd_grp['Yield_Bgt']
df_afd_ytd_grp['Yield_Gap_Pct'] = df_afd_ytd_grp['Yield_Pct'] - 100

c_fig_afd_b, c_fig_afd_y = st.columns(2)

with c_fig_afd_b:
    st.subheader(f"Yield Per Afdeling Bulan {pilihan_bulan}")
    fig_a_b = go.Figure()
    fig_a_b.add_trace(go.Bar(x=df_a_murni["Afdeling"], y=df_a_murni["Yield_Akt"], name="Aktual Bulanan", marker_color="#28348A", width=0.4))
    fig_a_b.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget Bulanan'))
    
    for idx, row in df_a_murni.iterrows():
        fig_a_b.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Yield_Bgt"], y1=row["Yield_Bgt"], line=dict(color="#00B050", width=4))
        
        fig_a_b.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
        
        # Logika Filter Tanda Panah Afdeling Bulanan
        pct = row["Yield_Pct"]
        if pct < 90:
            fig_a_b.add_annotation(
                x=idx, y=row["Yield_Bgt"], 
                ax=idx, ay=row["Yield_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
        elif pct > 110:
            fig_a_b.add_annotation(
                x=idx, y=row["Yield_Bgt"], 
                ax=idx, ay=row["Yield_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_a_b.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_a_b, use_container_width=True)
    st.dataframe(df_a_murni[['Afdeling', 'Yield_Akt', 'Yield_Bgt', 'Yield_Gap_Ton', 'Yield_Gap_Pct']].style.format({"Yield_Akt": "{:.2f}", "Yield_Bgt": "{:.2f}", "Yield_Gap_Ton": "{:+.2f}", "Yield_Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Yield_Gap_Pct']), use_container_width=True, hide_index=True)

with c_fig_afd_y:
    st.subheader(f"Yield Per Afdeling s/d BI")
    fig_a_y = go.Figure()
    fig_a_y.add_trace(go.Bar(x=df_afd_ytd_grp["Afdeling"], y=df_afd_ytd_grp["Yield_Akt"], name="YTD Aktual", marker_color="#28348A", width=0.4))
    fig_a_y.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color='#00B050', width=4), name='Budget YTD'))
    
    for idx, row in df_afd_ytd_grp.iterrows():
        fig_a_y.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Yield_Bgt"], y1=row["Yield_Bgt"], line=dict(color="#00B050", width=4))
        
        fig_a_y.add_annotation(x=idx, y=0, text=f"{row['Yield_Pct']:.1f}%", showarrow=False, yshift=25, textangle=-90, font=dict(color="white", size=11, weight='bold'))
        
        # Logika Filter Tanda Panah Afdeling YTD
        pct = row["Yield_Pct"]
        if pct < 90:
            fig_a_y.add_annotation(
                x=idx, y=row["Yield_Bgt"], 
                ax=idx, ay=row["Yield_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
        elif pct > 110:
            fig_a_y.add_annotation(
                x=idx, y=row["Yield_Bgt"], 
                ax=idx, ay=row["Yield_Akt"],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2.5, arrowcolor='#FF0000',
                standoff=0, startstandoff=0
            )
            
    fig_a_y.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig_a_y, use_container_width=True)
    st.dataframe(df_afd_ytd_grp[['Afdeling', 'Yield_Akt', 'Yield_Bgt', 'Yield_Gap_Ton', 'Yield_Gap_Pct']].style.format({"Yield_Akt": "{:.2f}", "Yield_Bgt": "{:.2f}", "Yield_Gap_Ton": "{:+.2f}", "Yield_Gap_Pct": "{:+.1f}%"}).map(style_gap, subset=['Yield_Gap_Pct']), use_container_width=True, hide_index=True)