import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

st.markdown("# 🏛️ Executive Summary - Performa Produksi Site Satui")
st.markdown("---")

FILE_BGT = "Rekap26.csv"
FILE_SNS = "Rekap26_Sns.csv"

@st.cache_data(ttl=600)
def load_summary_data():
    df_b = pd.read_csv(FILE_BGT, sep=";", decimal=",", engine="python")
    df_s = pd.read_csv(FILE_SNS, sep=";", decimal=",", engine="python")
    # Bersihkan spasi di nama kolom
    for df in [df_b, df_s]:
        df.columns = df.columns.str.strip().str.upper()
        if 'BULAN' in df.columns: df['BULAN'] = df['BULAN'].astype(str).str.strip().str.upper()
        if 'PT' in df.columns: df['PT'] = df['PT'].astype(str).str.strip().str.upper()
    return df_b, df_s

df_bgt, df_sns = load_summary_data()
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- FILTER PERIODE ---
pilihan_bulan = st.session_state.get("pilihan_bulan", "MEI")
target_aktif = st.session_state.get("global_target_type_picker", "Budget")

b = str(pilihan_bulan).upper()
idx = URUTAN_BULAN_STD.index(b) if b in URUTAN_BULAN_STD else 4
bi_m, sd_m = [URUTAN_BULAN_STD[idx]], URUTAN_BULAN_STD[:idx+1]

# --- ENGINE KALKULASI DENGAN DEBUGGING ---
def get_metrics_for_all_pt(target_type, bi_l, sd_l):
    df_t = df_bgt if target_type == "Budget" else df_sns
    results = {}
    
    # Fungsi pembantu untuk mencari kolom yang paling mendekati
    def find_col(df, options):
        for opt in options:
            if opt in df.columns: return opt
        return None

    for pt in ["BKB", "FFD", "TOTAL"]:
        def calc(list_b):
            sub_t = df_t[df_t['BULAN'].isin(list_b)] if pt == "TOTAL" else df_t[(df_t['BULAN'].isin(list_b)) & (df_t['PT'] == pt)]
            sub_b = df_bgt[df_bgt['BULAN'].isin(list_b)] if pt == "TOTAL" else df_bgt[(df_bgt['BULAN'].isin(list_b)) & (df_bgt['PT'] == pt)]
            
            if sub_t.empty or sub_b.empty: return 0,0,0,0,0,0
            
            # Deteksi nama kolom otomatis
            c_kg_a = find_col(sub_b, ['KG AKT.', 'KG AKT'])
            c_jjg_a = find_col(sub_b, ['JJG AKT.', 'JJG AKT'])
            c_kg_t = find_col(sub_t, ['KG BGT.', 'KG BGT', 'KG SNS.', 'KG SNS'])
            c_jjg_t = find_col(sub_t, ['JJG BGT.', 'JJG BGT', 'JJG SNS.', 'JJG SNS'])
            
            luas, pokok = sub_b['LUAS'].sum(), sub_b['POKOK'].sum()
            kg_a = sub_b[c_kg_a].sum() if c_kg_a else 0
            jjg_a = sub_b[c_jjg_a].sum() if c_jjg_a else 0
            kg_t = sub_t[c_kg_t].sum() if c_kg_t else 0
            jjg_t = sub_t[c_jjg_t].sum() if c_jjg_t else 0
            
            y_a = (kg_a/1000)/luas if luas > 0 else 0
            y_t = (kg_t/1000)/luas if luas > 0 else 0 # Asumsi Luas sama untuk Budget
            r_a = jjg_a/pokok if pokok > 0 else 0
            r_t = jjg_t/pokok if pokok > 0 else 0
            b_a = kg_a/jjg_a if jjg_a > 0 else 0
            b_t = kg_t/jjg_t if jjg_t > 0 else 0
            
            return (y_a/y_t*100) if y_t>0 else 0, (r_a/r_t*100) if r_t>0 else 0, (b_a/b_t*100) if b_t>0 else 0

        # Simpan hasil (Y1, Y2, R1, R2, B1, B2)
        y1, r1, b1 = calc(bi_l)
        y2, r2, b2 = calc(sd_l)
        results[pt] = (y1, y2, r1, r2, b1, b2)
    return results

data = get_metrics_for_all_pt(target_aktif, bi_m, sd_m)

# --- RENDERER ---
def render_bullet(df, title, y_axis_title, key):
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["PT"], y=df["Aktual"], marker_color="#28348A", width=0.35,
        text=[f"{p:,.1f}%" for p in df["Pct"]], textposition="inside"
    ))
    # Tambahkan garis target dll seperti kode Anda sebelumnya...
    st.plotly_chart(fig, use_container_width=True, key=key)

# Render
for m_idx, m_name, y_title in [(0, "Yield", "Ton/Ha"), (2, "RJP", "Janjang/Pokok"), (4, "BJR", "Kg/Janjang")]:
    st.markdown(f"### {m_name}")
    df_mtd = pd.DataFrame({
        "PT": ["PT BKB", "PT FFD", "TOTAL GRUP"],
        "Aktual": [data["BKB"][m_idx], data["FFD"][m_idx], data["TOTAL"][m_idx]],
        "Target": [100, 100, 100], # Ini untuk garis 100%
        "Pct": [data["BKB"][m_idx], data["FFD"][m_idx], data["TOTAL"][m_idx]]
    })
    col1, col2 = st.columns(2)
    with col1: render_bullet(df_mtd, f"{m_name} - BI", y_title, f"mtd_{m_name}")