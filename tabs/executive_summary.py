import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.markdown("# 🏛️ Executive Summary - Performa Produksi Site Satui")
st.markdown("---")

# --- DATA LOADING ---
FILE_BGT = "Rekap26.csv"
FILE_SNS = "Rekap26_Sns.csv"

# Pemetaan Kebun -> PT. Grup "FFD" ditandai eksplisit lewat nama kebun,
# sisanya (BKB, SC Inti, SC Plasma, Setarap, dll) otomatis masuk grup "BKB".
def map_kebun_to_pt(nama_kebun):
    nama_kebun = str(nama_kebun).strip().upper()
    if "FFD" in nama_kebun:
        return "FFD"
    return "BKB"

@st.cache_data(ttl=600)
def load_summary_data():
    df_b = pd.read_csv(FILE_BGT, sep=";", decimal=",", engine="python")
    df_b.columns = df_b.columns.str.strip().str.upper()
    df_s = pd.read_csv(FILE_SNS, sep=";", decimal=",", engine="python")
    df_s.columns = df_s.columns.str.strip().str.upper()
    for df in [df_b, df_s]:
        if 'BULAN' in df.columns: df['BULAN'] = df['BULAN'].astype(str).str.strip().str.upper()
        # Kolom 'PT' tidak selalu ada di file export Excel -> selalu diturunkan
        # ulang dari kolom 'KEBUN' agar tahan terhadap perubahan format file bulanan.
        if 'KEBUN' in df.columns:
            df['PT'] = df['KEBUN'].apply(map_kebun_to_pt)
        elif 'PT' in df.columns:
            df['PT'] = df['PT'].astype(str).str.strip().str.upper()
    return df_b, df_s

df_bgt, df_sns = load_summary_data()
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- FILTER PERIODE ---
pilihan_bulan = st.session_state.get("pilihan_bulan", "MEI")
target_aktif = st.session_state.get("global_target_type_picker", "Budget")

if pilihan_bulan == "CAWU I":
    bi_m, sd_m = ['JAN', 'FEB', 'MAR', 'APR'], ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == "CAWU II":
    bi_m, sd_m = ['MEI', 'JUN', 'JUL', 'AGT'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT']
elif pilihan_bulan == "CAWU III":
    bi_m, sd_m = ['SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
elif pilihan_bulan == "SEMESTER I":
    bi_m, sd_m = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN'], ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN']
elif pilihan_bulan == "SEMESTER II":
    bi_m, sd_m = ['JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES'], URUTAN_BULAN_STD
else:
    b = str(pilihan_bulan).upper()
    idx = URUTAN_BULAN_STD.index(b) if b in URUTAN_BULAN_STD else 4
    bi_m, sd_m = [URUTAN_BULAN_STD[idx]], URUTAN_BULAN_STD[:idx+1]

# --- ENGINE KALKULASI ---
def get_metrics_for_all_pt(target_type, bi_l, sd_l):
    df_t = df_bgt if target_type == "Budget" else df_sns
    results = {}
    for pt in ["BKB", "FFD", "TOTAL"]:
        def calc(list_b):
            sub_t = df_t[df_t['BULAN'].isin(list_b)] if pt == "TOTAL" else df_t[(df_t['BULAN'].isin(list_b)) & (df_t['PT'] == pt)]
            sub_b = df_bgt[df_bgt['BULAN'].isin(list_b)] if pt == "TOTAL" else df_bgt[(df_bgt['BULAN'].isin(list_b)) & (df_bgt['PT'] == pt)]
            if sub_t.empty or sub_b.empty: return 0,0,0,0,0,0
            
            luas, pokok = sub_b['LUAS'].sum(), sub_b['POKOK'].sum()
            kg_a, jjg_a = sub_b['KG AKT.'].sum(), sub_b['JJG AKT.'].sum()
            kg_t = sub_t['KG BGT.'].sum() if target_type == "Budget" else sub_t['KG SNS.'].sum()
            jjg_t = sub_t['JJG BGT.'].sum() if target_type == "Budget" else sub_t['JJG SNS.'].sum()
            
            y_a = (kg_a/1000)/luas if luas>0 else 0
            y_t = (kg_t/1000)/(sub_t['LUAS'].sum() if target_type=="Sensus" else luas) if (sub_t['LUAS'].sum() if target_type=="Sensus" else luas)>0 else 0
            r_a = jjg_a/pokok if pokok>0 else 0
            r_t = jjg_t/(sub_t['POKOK'].sum() if target_type=="Sensus" else pokok) if (sub_t['POKOK'].sum() if target_type=="Sensus" else pokok)>0 else 0
            b_a = kg_a/jjg_a if jjg_a>0 else 0
            b_t = kg_t/jjg_t if jjg_t>0 else 0
            return y_a, y_t, r_a, r_t, b_a, b_t
        y1, yt1, r1, rt1, b1, bt1 = calc(bi_l)
        y2, yt2, r2, rt2, b2, bt2 = calc(sd_l)
        results[pt] = (y1, yt1, r1, rt1, b1, bt1, y2, yt2, r2, rt2, b2, bt2)
    return results

data = get_metrics_for_all_pt(target_aktif, bi_m, sd_m)

# --- FUNGSI DETEKSI 3 TERENDAH ---
def get_lowest_performers_list(list_b, target_type):
    df_all = df_bgt[df_bgt['BULAN'].isin(list_b)]
    df_t = df_bgt if target_type == "Budget" else df_sns
    df_t_all = df_t[df_t['BULAN'].isin(list_b)]
    
    if df_all.empty or 'AFDELING' not in df_all.columns: return "Data tidak tersedia"
    
    df_group = df_all.groupby(['PT', 'AFDELING'])[['KG AKT.', 'LUAS']].sum().reset_index()
    target_col = 'KG BGT.' if target_type == "Budget" else 'KG SNS.'
    df_target = df_t_all.groupby(['PT', 'AFDELING'])[[target_col]].sum().reset_index()
    
    df_merge = pd.merge(df_group, df_target, on=['PT', 'AFDELING'])
    df_merge['YIELD'] = (df_merge['KG AKT.']/1000) / df_merge['LUAS']
    df_merge['PCT'] = (df_merge['KG AKT.'] / df_merge[target_col] * 100).fillna(0)
    
    output = []
    for pt in ["BKB", "FFD"]:
        df_pt = df_merge[df_merge['PT'] == pt].nsmallest(3, 'YIELD')
        if not df_pt.empty:
            list_afd = [f"Afd {row['AFDELING']} ({row['YIELD']:.2f} ton/ha / {row['PCT']:.1f}%)" for _, row in df_pt.iterrows()]
            output.append(f"**{pt}:** {', '.join(list_afd)}")
    return "\n\n".join(output)

# --- RENDERER ---
def render_bullet(df, title, y_axis_title, key):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["PT"], y=df["Aktual"], name="Aktual", marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df["Pct"]], textposition="inside", insidetextanchor="start",
        textfont=dict(color="white", size=12, family="Arial Black")
    ))
    fig.add_trace(go.Scatter(x=df["PT"], y=[None]*len(df), mode='lines', line=dict(color='#00B050', width=4), name=target_aktif))
    for idx, row in df.iterrows():
        fig.add_shape(type="line", x0=idx-0.2, x1=idx+0.2, y0=row["Target"], y1=row["Target"], line=dict(color="#00B050", width=4))
        if row["Pct"] < 90 or row["Pct"] > 110:
            fig.add_annotation(x=idx, y=row["Target"], ax=idx, ay=row["Aktual"], xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=2.5, arrowcolor='#FF0000')
    fig.update_layout(template="plotly_white", yaxis_title=y_axis_title, margin=dict(l=20, r=20, t=40, b=20), height=300, legend=dict(orientation="h", y=1.15))
    st.plotly_chart(fig, use_container_width=True, key=f"{key}_{pilihan_bulan}_{target_aktif}")

# Proses Rendering untuk 3 Metrik
for m_idx, m_name, y_title in [(0, "Yield", "Ton/Ha"), (2, "RJP", "Janjang/Pokok"), (4, "BJR", "Kg/Janjang")]:
    st.markdown(f"### {m_name}")
    df_mtd = pd.DataFrame({"PT": ["PT BKB", "PT FFD", "TOTAL GRUP"], "Aktual": [data["BKB"][m_idx], data["FFD"][m_idx], data["TOTAL"][m_idx]], "Target": [data["BKB"][m_idx+1], data["FFD"][m_idx+1], data["TOTAL"][m_idx+1]]})
    df_mtd["Pct"] = (df_mtd["Aktual"] / df_mtd["Target"] * 100).fillna(0)
    df_ytd = pd.DataFrame({"PT": ["PT BKB", "PT FFD", "TOTAL GRUP"], "Aktual": [data["BKB"][m_idx+6], data["FFD"][m_idx+6], data["TOTAL"][m_idx+6]], "Target": [data["BKB"][m_idx+7], data["FFD"][m_idx+7], data["TOTAL"][m_idx+7]]})
    df_ytd["Pct"] = (df_ytd["Aktual"] / df_ytd["Target"] * 100).fillna(0)
    
    col1, col2 = st.columns(2)
    with col1: render_bullet(df_mtd, f"{m_name} - BI", y_title, f"mtd_{m_name}")
    with col2: render_bullet(df_ytd, f"{m_name} - s.d BI", y_title, f"ytd_{m_name}")
    
    if m_name == "Yield":
        st.markdown("---")
        st.markdown(f"#### 📉 3 Afdeling Capaian Yield Terendah s.d {pilihan_bulan}")
        st.info(get_lowest_performers_list(sd_m, target_aktif), icon="⚠️")
        st.markdown("---")