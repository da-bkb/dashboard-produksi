import streamlit as st
import pandas as pd
import os
import numpy as np
import plotly.graph_objects as go

# --- 1. KONFIGURASI HALAMAN UTAMA ---
st.set_page_config(
    page_title="Dashboard Produksi Kelapa Sawit",
    page_icon="🌴",
    layout="wide"
)

# --- 2. FUNGSI LOADING DATA KEDUA FILE REAL-TIME ---
@st.cache_data
def load_all_databases():
    # Load File Budget
    file_bgt = "Rekap26.csv"
    if os.path.exists(file_bgt):
        try:
            df_bgt = pd.read_csv(file_bgt, sep=";", decimal=",")
        except:
            df_bgt = pd.read_csv(file_bgt, sep=",", decimal=",")
    else:
        df_bgt = pd.DataFrame()

    # Load File Sensus
    file_sns = "Rekap26_Sns.csv"
    if os.path.exists(file_sns):
        try:
            df_sns = pd.read_csv(file_sns, sep=";", decimal=",")
        except:
            df_sns = pd.read_csv(file_sns, sep=",", decimal=",")
    else:
        df_sns = pd.DataFrame()

    # Bersihkan whitespace kolom dan standarisasi string 'Bulan'
    for df in [df_bgt, df_sns]:
        if not df.empty:
            df.columns = df.columns.str.strip()
            if 'Bulan' in df.columns:
                df['Bulan'] = df['Bulan'].astype(str).str.strip().str.upper()
            if 'Kebun' in df.columns:
                df['Kebun'] = df['Kebun'].astype(str).str.strip()
            if 'Afdeling' in df.columns:
                df['Afdeling'] = df['Afdeling'].astype(str).str.strip()
    
    return df_bgt, df_sns

df_bgt_raw, df_sns_raw = load_all_databases()

if df_bgt_raw.empty or df_sns_raw.empty:
    st.error("⚠️ File data 'Rekap26.csv' atau 'Rekap26_Sns.csv' tidak ditemukan di root folder!")
    st.stop()

# --- 3. FILTER GLOBAL UTAMA (DI ATAS) ---
st.markdown("<h1 style='text-align: center; color: #28348A;'>🌴 DASHBOARD PRODUKSI PT BKB & PT FFD</h1>", unsafe_allow_html=True)
st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    # Mengambil list bulan unik dari data Budget
    list_bulan = list(df_bgt_raw['Bulan'].unique()) if 'Bulan' in df_bgt_raw.columns else ['MEI']
    pilihan_bulan = st.selectbox(
        "📅 1. Pilih Bulan Analisis:", 
        list_bulan, 
        index=list_bulan.index("MEI") if "MEI" in list_bulan else 0,
        key="global_month_picker_main"
    )

with col2:
    # Urutan Tabs Persis Kemauan Bapak: Yield - RJP - BJR - Trend Kebun - Trend Afdeling
    menu_analisis = st.selectbox(
        "📊 2. Pilih Menu Analisis:",
        ["Yield", "RJP", "BJR", "Trend Kebun", "Trend Afdeling"],
        key="menu_dashboard_navigator_main"
    )

st.markdown("---")

# --- 4. ENGINE FILTER DATA KUMULATIF YEAR TO DATE (YTD) ---
URUTAN_BULAN_STANDAR = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STANDAR:
    idx_bulan = URUTAN_BULAN_STANDAR.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STANDAR[:idx_bulan + 1]
else:
    bulan_ytd = [pilihan_bulan_std]

# Slice dataframe mentah YTD
df_bgt_ytd = df_bgt_raw[df_bgt_raw['Bulan'].isin(bulan_ytd)].copy()
df_sns_ytd = df_sns_raw[df_sns_raw['Bulan'].isin(bulan_ytd)].copy()

# Masukkan ke session state agar dibaca sub-file tab jika dipanggil eksternal
st.session_state["df_raw"] = df_bgt_ytd  # Kompatibilitas file lama yang baca df_raw
st.session_state["pilihan_bulan"] = pilihan_bulan

# --- 5. FUNGSI EMBED/RENDER SHEET SUMMARY KOMPARASI PER KEBUN ---
def render_summary_sheet_view(mode_analisis):
    st.markdown(f"### 📋 Sheet Summary Analisa {mode_analisis} Per Kebun (YTD s/d {pilihan_bulan})")
    
    # Aggregation data Budget per Kebun
    # Khusus Luas dan Pokok diambil .first() per kombinasi Kebun-Afdeling agar kumulatif bulan tidak melipatgandakan luas lapangan
    luas_kebun = df_bgt_ytd.groupby(['Kebun', 'Afdeling'])['Luas'].first().reset_index().groupby('Kebun')['Luas'].sum()
    pokok_kebun = df_bgt_ytd.groupby(['Kebun', 'Afdeling'])['Pokok'].first().reset_index().groupby('Kebun')['Pokok'].sum()
    
    bgt_grp = df_bgt_ytd.groupby('Kebun').agg({
        'Kg Akt.': 'sum',
        'Kg Bgt.': 'sum',
        'Jjg Akt.': 'sum',
        'Jjg Bgt.': 'sum'
    })
    bgt_grp['Luas'] = luas_kebun
    bgt_grp['Pokok'] = pokok_kebun
    bgt_grp = bgt_grp.reset_index()

    # Aggregation data Sensus per Kebun
    sns_grp = df_sns_ytd.groupby('Kebun').agg({
        'Kg Sns.': 'sum',
        'Jjg Sns.': 'sum'
    }).reset_index()

    # Gabungkan data komparasi
    df_sum_kebun = pd.merge(bgt_grp, sns_grp, on='Kebun', how='left').fillna(0)

    # Kalkulasi rasio spesifik berdasarkan menu yang aktif
    if mode_analisis == "Yield":
        df_sum_kebun['Aktual'] = df_sum_kebun['Kg Akt.'] / df_sum_kebun['Luas'] / 1000
        df_sum_kebun['Target_Budget'] = df_sum_kebun['Kg Bgt.'] / df_sum_kebun['Luas'] / 1000
        df_sum_kebun['Target_Sensus'] = df_sum_kebun['Kg Sns.'] / df_sum_kebun['Luas'] / 1000
        fmt_unit = "Ton/Ha"
    elif mode_analisis == "RJP":
        df_sum_kebun['Aktual'] = df_sum_kebun['Jjg Akt.'] / df_sum_kebun['Pokok']
        df_sum_kebun['Target_Budget'] = df_sum_kebun['Jjg Bgt.'] / df_sum_kebun['Pokok']
        df_sum_kebun['Target_Sensus'] = df_sum_kebun['Jjg Sns.'] / df_sum_kebun['Pokok']
        fmt_unit = "Jjg/Pokok"
    else:  # BJR
        df_sum_kebun['Aktual'] = df_sum_kebun['Kg Akt.'] / df_sum_kebun['Jjg Akt.']
        df_sum_kebun['Target_Budget'] = df_sum_kebun['Kg Bgt.'] / df_sum_kebun['Jjg Bgt.']
        df_sum_kebun['Target_Sensus'] = df_sum_kebun['Kg Sns.'] / df_sum_kebun['Jjg Sns.']
        fmt_unit = "Kg"

    df_sum_kebun['Capaian_Bgt'] = (df_sum_kebun['Aktual'] / df_sum_kebun['Target_Budget'] * 100).fillna(0)
    df_sum_kebun['Capaian_Sns'] = (df_sum_kebun['Aktual'] / df_sum_kebun['Target_Sensus'] * 100).fillna(0)

    # Tampilkan Tabel ala Excel Summary Sheet dengan pewarnaan otomatis
    df_table_show = df_sum_kebun[['Kebun', 'Aktual', 'Target_Budget', 'Target_Sensus', 'Capaian_Bgt', 'Capaian_Sns']].copy()
    
    def format_color_pct(val):
        bg = '#FF0000' if val < 95 else ('#FFA500' if val < 105 else '#00B050')
        return f'background-color: {bg}; color: white; font-weight: bold;'

    st.dataframe(
        df_table_show.style.format({
            'Aktual': '{:,.2f}', 'Target_Budget': '{:,.2f}', 'Target_Sensus': '{:,.2f}',
            'Capaian_Bgt': '{:,.2f}%', 'Capaian_Sns': '{:,.2f}%'
        }).map(format_color_pct, subset=['Capaian_Bgt', 'Capaian_Sns']),
        use_container_width=True
    )

    # --- RENDER GRAPH GAP SUMMARY KEBUN ---
    st.markdown(f"#### 📉 Grafik Analisis Gap Kebun {mode_analisis} terhadap Target")
    ref_target = st.radio(f"Pilih Acuan Target ({mode_analisis}):", ["Terhadap BUDGET", "Terhadap SENSUS"], horizontal=True, key=f"rad_{mode_analisis}")
    tgt_col = 'Target_Budget' if ref_target == "Terhadap BUDGET" else 'Target_Sensus'

    fig_summary = go.Figure()
    # 1. Batang Aktual -> Warna Biru Tua (#28348A)
    fig_summary.add_trace(go.Bar(
        x=df_sum_kebun['Kebun'], y=df_sum_kebun['Aktual'],
        name=f'{mode_analisis} Aktual', marker_color='#28348A', width=0.35
    ))
    # Legenda Target Line -> Warna Hijau (#00B050)
    fig_summary.add_trace(go.Scatter(
        x=[None], y=[None], mode='lines',
        line=dict(color='#00B050', width=4), name=ref_target
    ))

    # Looping draw line hijau dan panah gap merah
    for idx, row in df_sum_kebun.iterrows():
        fig_summary.add_shape(
            type="line", x0=idx - 0.25, x1=idx + 0.25,
            y0=row[tgt_col], y1=row[tgt_col],
            line=dict(color="#00B050", width=4)
        )
        # Jika realisasi di bawah target -> Kasih panah gap merah jatuh kebawah (#FF0000)
        if row['Aktual'] < row[tgt_col]:
            fig_summary.add_annotation(
                x=idx, y=row[tgt_col], ax=idx, ay=row['Aktual'],
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2, arrowwidth=3, arrowcolor='#FF0000'
            )

    fig_summary.update_layout(
        template="plotly_white", margin=dict(l=40, r=40, t=40, b=40),
        yaxis_title=fmt_unit, legend=dict(orientation="h", y=1.1)
    )
    st.plotly_chart(fig_summary, use_container_width=True)
    st.markdown("---")

# --- 6. ROUTING EKSEKUSI TABS UTAMA ---
global_context = globals()

if menu_analisis == "Yield":
    render_summary_sheet_view("Yield")
    # Panggil filter internal afdeling dari sub-file aslinya di bawah summary kebun
    if os.path.exists("tabs/yield_perf.py"):
        exec(open("tabs/yield_perf.py").read(), global_context)

elif menu_analisis == "RJP":
    render_summary_sheet_view("RJP")
    if os.path.exists("tabs/janjang_pokok.py"):
        exec(open("tabs/janjang_pokok.py").read(), global_context)

elif menu_analisis == "BJR":
    render_summary_sheet_view("BJR")
    if os.path.exists("tabs/bjr_perf.py"):
        exec(open("tabs/bjr_perf.py").read(), global_context)

elif menu_analisis == "Trend Kebun":
    st.markdown(f"## 📈 Trend Performa Kebun (Januari - Mei)")
    # Langsung teruskan baca file visualisasi trend kebun yang sudah bapak miliki sebelumnya
    if os.path.exists("tabs/trend_kebun.py"):
        exec(open("tabs/trend_kebun.py").read(), global_context)
    else:
        st.info("Sub-file 'tabs/trend_kebun.py' tidak ditemukan. Silakan letakkan file trend kebun Bapak di folder tabs.")

elif menu_analisis == "Trend Afdeling":
    st.markdown(f"## 📉 Trend Performa Afdeling (Januari - Mei)")
    if os.path.exists("tabs/trend_afdeling.py"):
        exec(open("tabs/trend_afdeling.py").read(), global_context)
    else:
        st.info("Sub-file 'tabs/trend_afdeling.py' tidak ditemukan. Silakan letakkan file trend afdeling Bapak di folder tabs.")