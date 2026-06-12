import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- 1. CONFIG & DATA LOADING ---
st.markdown("# 🏛️ Executive Summary - Performa Produksi Site Satui")
st.markdown("---")

FILE_BGT = "Rekap26.csv"
FILE_SNS = "Rekap26_Sns.csv"

@st.cache_data(ttl=600)
def load_summary_data():
    # Gunakan encoding utf-8-sig untuk mengatasi masalah bom/karakter tersembunyi
    df_b = pd.read_csv(FILE_BGT, sep=";", decimal=",", engine="python", encoding="utf-8-sig")
    df_s = pd.read_csv(FILE_SNS, sep=";", decimal=",", engine="python", encoding="utf-8-sig")
    
    for df in [df_b, df_s]:
        df.columns = df.columns.str.strip().str.upper()
        if 'BULAN' in df.columns: df['BULAN'] = df['BULAN'].astype(str).str.strip().str.upper()
        if 'PT' in df.columns: df['PT'] = df['PT'].astype(str).str.strip().str.upper()
    return df_b, df_s

df_bgt, df_sns = load_summary_data()
URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']

# --- 2. FILTER PERIODE ---
pilihan_bulan = st.session_state.get("pilihan_bulan", "MEI")
target_aktif = st.session_state.get("global_target_type_picker", "Budget")

b = str(pilihan_bulan).upper()
idx = URUTAN_BULAN_STD.index(b) if b in URUTAN_BULAN_STD else 4
bi_m, sd_m = [URUTAN_BULAN_STD[idx]], URUTAN_BULAN_STD[:idx+1]

# --- 3. ENGINE KALKULASI (DENGAN PENGECEKAN KOLOM) ---
def get_metrics_for_all_pt(target_type, bi_l, sd_l):
    df_t = df_bgt if target_type == "Budget" else df_sns
    results = {}
    
    # Debug: Print kolom untuk memastikan nama yang benar
    # st.write(f"Kolom Budget: {df_bgt.columns.tolist()}") 
    
    for pt in ["BKB", "FFD", "TOTAL"]:
        def calc(list_b):
            sub_t = df_t[df_t['BULAN'].isin(list_b)] if pt == "TOTAL" else df_t[(df_t['BULAN'].isin(list_b)) & (df_t['PT'] == pt)]
            sub_b = df_bgt[df_bgt['BULAN'].isin(list_b)] if pt == "TOTAL" else df_bgt[(df_bgt['BULAN'].isin(list_b)) & (df_bgt['PT'] == pt)]
            if sub_t.empty or sub_b.empty: return 0,0,0,0,0,0
            
            # Pengecekan kolom yang lebih aman
            col_kg_a = 'KG AKT.' if 'KG AKT.' in sub_b.columns else 'KG AKT'
            col_jjg_a = 'JJG AKT.' if 'JJG AKT.' in sub_b.columns else 'JJG AKT'
            col_kg_t = 'KG BGT.' if 'KG BGT.' in sub_t.columns else 'KG BGT'
            col_jjg_t = 'JJG BGT.' if 'JJG BGT.' in sub_t.columns else 'JJG BGT'
            
            # Jika Sensus, sesuaikan kolom
            if target_type == "Sensus":
                col_kg_t = 'KG SNS.' if 'KG SNS.' in sub_t.columns else 'KG SNS'
                col_jjg_t = 'JJG SNS.' if 'JJG SNS.' in sub_t.columns else 'JJG SNS'

            luas = sub_b['LUAS'].sum()
            pokok = sub_b['POKOK'].sum()
            kg_a = sub_b[col_kg_a].sum()
            jjg_a = sub_b[col_jjg_a].sum()
            kg_t = sub_t[col_kg_t].sum()
            jjg_t = sub_t[col_jjg_t].sum()
            
            y_a, y_t = (kg_a/1000)/luas if luas>0 else 0, (kg_t/1000)/(sub_t['LUAS'].sum() if target_type=="Sensus" else luas)
            r_a, r_t = jjg_a/pokok if pokok>0 else 0, jjg_t/(sub_t['POKOK'].sum() if target_type=="Sensus" else pokok)
            b_a, b_t = kg_a/jjg_a if jjg_a>0 else 0, kg_t/jjg_t if jjg_t>0 else 0
            return y_a, y_t, r_a, r_t, b_a, b_t

        y1, yt1, r1, rt1, b1, bt1 = calc(bi_l)
        y2, yt2, r2, rt2, b2, bt2 = calc(sd_l)
        results[pt] = (y1, yt1, r1, rt1, b1, bt1, y2, yt2, r2, rt2, b2, bt2)
    return results

# Lanjutkan dengan memanggil data dan rendering seperti sebelumnya...
# ...