import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os

# --- 0. CUSTOM STYLE (CSS) ---
st.markdown("""
<style>
    .exec-title {
        text-align: center;
        font-size: 34px;
        font-weight: 800;
        background: linear-gradient(90deg, #1B5E9E, #00B4A6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        padding: 4px 0 0 0;
        margin-bottom: 0px;
    }
    .exec-subtitle {
        text-align: center;
        font-size: 15px;
        color: #6B7280;
        margin-top: -6px;
        margin-bottom: 14px;
    }
    .pt-banner {
        border-radius: 14px;
        padding: 14px 22px;
        margin: 18px 0 16px 0;
        color: white;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    }
    .kpi-card {
        border-radius: 14px;
        padding: 16px 10px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        color: white;
        margin-bottom: 6px;
    }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        opacity: 0.92;
        letter-spacing: 0.3px;
    }
    .kpi-value {
        font-size: 27px;
        font-weight: 800;
        margin-top: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='exec-title'>🏛️ EXECUTIVE SUMMARY - PERFORMA PRODUKSI SITE SATUI</div>", unsafe_allow_html=True)
st.markdown("<div class='exec-subtitle'>Ringkasan kinerja produksi, curah hujan, dan pencapaian target — PT BKB & PT FFD</div>", unsafe_allow_html=True)

# --- 1. KONSTANTA & NAMA FILE ---
FILE_BGT = "Rekap26.csv"
FILE_SNS = "Rekap26_Sns.csv"
FILE_CH = "Rkp_ch_hh.csv"

URUTAN_BULAN_STD = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT', 'SEP', 'OKT', 'NOV', 'DES']
MAPPING_LABEL = {'JAN': 'Jan', 'FEB': 'Feb', 'MAR': 'Mar', 'APR': 'Apr', 'MEI': 'Mei', 'JUN': 'Jun',
                  'JUL': 'Jul', 'AGT': 'Agt', 'SEP': 'Sep', 'OKT': 'Okt', 'NOV': 'Nov', 'DES': 'Des'}
LABEL_BULAN_X = [MAPPING_LABEL[b] for b in URUTAN_BULAN_STD]

# Palet warna vivid & konsisten untuk semua grafik
WARNA_AKTUAL = "#1565C0"    # Biru vivid
WARNA_TARGET = "#FB8C00"    # Oranye vivid
WARNA_HUJAN = "#00ACC1"     # Teal/cyan vivid
WARNA_HUJAN_FILL = "rgba(0,172,193,0.20)"


# Pemetaan Kebun -> PT. "FFD" ditandai eksplisit dari nama kebun, sisanya
# (BKB Inti/Plasma, SC Inti/Plasma, Setarap, dst) otomatis masuk grup BKB.
def map_kebun_to_pt(nama_kebun):
    nama_kebun = str(nama_kebun).strip().upper()
    return "FFD" if "FFD" in nama_kebun else "BKB"


# --- 2. LOAD DATA (Budget & Sensus) ---
@st.cache_data(ttl=600)
def load_summary_data():
    df_b = pd.read_csv(FILE_BGT, sep=";", decimal=",", engine="python")
    df_b.columns = df_b.columns.str.strip().str.upper()
    df_s = pd.read_csv(FILE_SNS, sep=";", decimal=",", engine="python")
    df_s.columns = df_s.columns.str.strip().str.upper()
    for df in [df_b, df_s]:
        if 'BULAN' in df.columns:
            df['BULAN'] = df['BULAN'].astype(str).str.strip().str.upper()
        # Kolom 'PT' tidak selalu ada di file export Excel -> selalu diturunkan
        # ulang dari kolom 'KEBUN' agar tahan terhadap perubahan format file bulanan.
        if 'KEBUN' in df.columns:
            df['PT'] = df['KEBUN'].apply(map_kebun_to_pt)
    return df_b, df_s


# --- 3. LOAD DATA CURAH HUJAN ---
@st.cache_data(ttl=600)
def load_rain_data():
    if not os.path.exists(FILE_CH):
        return pd.DataFrame()
    df_ch = pd.read_csv(FILE_CH, sep=";", decimal=",", engine="python")
    df_ch.columns = df_ch.columns.str.strip().str.upper()
    df_ch['BULAN'] = df_ch['BULAN'].astype(str).str.strip().str.upper()
    df_ch['KEBUN'] = df_ch['KEBUN'].astype(str).str.strip().str.upper()
    df_ch['PT'] = df_ch['KEBUN'].apply(map_kebun_to_pt)
    df_ch['CURAH_HUJAN'] = pd.to_numeric(df_ch['CURAH_HUJAN'], errors='coerce')
    return df_ch


if not os.path.exists(FILE_BGT) or not os.path.exists(FILE_SNS):
    st.error("⚠️ File Rekap26.csv / Rekap26_Sns.csv tidak ditemukan!")
    st.stop()

df_bgt, df_sns = load_summary_data()
df_ch_all = load_rain_data()

# --- 4. FILTER GLOBAL (mengikuti pilihan di halaman utama app.py) ---
pilihan_bulan = st.session_state.get("pilihan_bulan", "MEI")
target_aktif = st.session_state.get("global_target_type_picker", "Budget")

df_target = df_bgt if target_aktif == "Budget" else df_sns
label_target = "Budget" if target_aktif == "Budget" else "Sensus"
KOL_KG_TARGET = "KG BGT." if target_aktif == "Budget" else "KG SNS."
KOL_JJG_TARGET = "JJG BGT." if target_aktif == "Budget" else "JJG SNS."

# Tentukan daftar bulan YTD (s.d. bulan/CAWU/Semester terpilih) untuk KPI & doughnut
if pilihan_bulan == "CAWU I":
    sd_m = ['JAN', 'FEB', 'MAR', 'APR']
elif pilihan_bulan == "CAWU II":
    sd_m = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGT']
elif pilihan_bulan in ("CAWU III", "SEMESTER II"):
    sd_m = URUTAN_BULAN_STD.copy()
elif pilihan_bulan == "SEMESTER I":
    sd_m = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN']
else:
    b = str(pilihan_bulan).upper()
    idx = URUTAN_BULAN_STD.index(b) if b in URUTAN_BULAN_STD else 4
    sd_m = URUTAN_BULAN_STD[:idx + 1]

# Tahun aktif curah hujan = tahun terbaru yang tersedia di file histori
TAHUN_AKTIF = int(df_ch_all['TAHUN'].max()) if not df_ch_all.empty else None


# --- 5. FUNGSI AGREGASI DATA PER PT ---
def hitung_data_pt(pt_kode):
    df_b_pt = df_bgt[df_bgt['PT'] == pt_kode]
    df_t_pt = df_target[df_target['PT'] == pt_kode]

    agg_b = df_b_pt.groupby('BULAN').agg(
        KG_AKT=('KG AKT.', 'sum'),
        JJG_AKT=('JJG AKT.', 'sum')
    ).reindex(URUTAN_BULAN_STD).fillna(0)

    agg_t = df_t_pt.groupby('BULAN').agg(
        KG_TGT=(KOL_KG_TARGET, 'sum'),
        JJG_TGT=(KOL_JJG_TARGET, 'sum')
    ).reindex(URUTAN_BULAN_STD).fillna(0)

    df_hasil = pd.concat([agg_b, agg_t], axis=1)
    df_hasil['TON_AKT'] = df_hasil['KG_AKT'] / 1000
    df_hasil['TON_TGT'] = df_hasil['KG_TGT'] / 1000
    df_hasil['BJR_AKT'] = np.where(df_hasil['JJG_AKT'] > 0, df_hasil['KG_AKT'] / df_hasil['JJG_AKT'], 0)
    df_hasil['BJR_TGT'] = np.where(df_hasil['JJG_TGT'] > 0, df_hasil['KG_TGT'] / df_hasil['JJG_TGT'], 0)

    # Curah hujan: rata-rata seluruh kebun yang tergabung dalam grup PT ini
    if not df_ch_all.empty:
        df_ch_pt = df_ch_all[(df_ch_all['PT'] == pt_kode) & (df_ch_all['TAHUN'] == TAHUN_AKTIF)]
        ch_bulanan = df_ch_pt.groupby('BULAN')['CURAH_HUJAN'].mean().reindex(URUTAN_BULAN_STD)
    else:
        ch_bulanan = pd.Series([np.nan] * 12, index=URUTAN_BULAN_STD)

    # Pencapaian YTD (Aktual vs Target) s.d bulan/periode terpilih
    kg_akt_ytd = df_hasil.loc[sd_m, 'KG_AKT'].sum()
    kg_tgt_ytd = df_hasil.loc[sd_m, 'KG_TGT'].sum()
    pct_capaian = (kg_akt_ytd / kg_tgt_ytd * 100) if kg_tgt_ytd > 0 else 0
    ch_rata_ytd = ch_bulanan.loc[sd_m].mean()

    return df_hasil, ch_bulanan, pct_capaian, kg_akt_ytd / 1000, kg_tgt_ytd / 1000, ch_rata_ytd


# --- 6. FUNGSI RENDER KARTU KPI ---
def render_kpi_card(label, value, c1, c2):
    st.markdown(f"""
    <div class="kpi-card" style="background: linear-gradient(135deg, {c1}, {c2});">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


# --- 7. FUNGSI RENDER GRAFIK (font & ukuran proporsional) ---
LAYOUT_UMUM = dict(
    height=380,
    margin=dict(l=45, r=25, t=55, b=90),
    hovermode="x unified",
    font=dict(size=13, color="white"),
    title_font=dict(size=17, color="white"),
    xaxis=dict(tickfont=dict(size=12, color="white")),
    plot_bgcolor="#000000",
    paper_bgcolor="#000000",
)


def render_line_dua_seri(df, kolom_akt, kolom_tgt, judul, y_title, format_label):
    label_akt = [format_label(v) for v in df[kolom_akt]]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=LABEL_BULAN_X, y=df[kolom_akt], mode='lines+markers+text', name="Aktual",
        line=dict(color=WARNA_AKTUAL, width=2, shape='spline'),
        marker=dict(size=9, color=WARNA_AKTUAL, line=dict(color='white', width=1.5)),
        text=label_akt, textposition="top center", textfont=dict(size=10, color="white")
    ))
    fig.add_trace(go.Scatter(
        x=LABEL_BULAN_X, y=df[kolom_tgt], mode='lines+markers', name=label_target,
        line=dict(color=WARNA_TARGET, width=2, shape='spline', dash='dash'),
        marker=dict(size=9, color=WARNA_TARGET, symbol='diamond', line=dict(color='white', width=1.5))
    ))
    fig.update_layout(
        title=judul,
        yaxis=dict(title=dict(text=y_title, font=dict(size=13, color="white")), tickfont=dict(size=12, color="white"), gridcolor="#333333"),
        legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="left", x=0, font=dict(size=12, color="white")),
        **LAYOUT_UMUM
    )
    return fig


def render_line_hujan(seri_ch, judul):
    label_ch = [f"{v:,.0f}" if pd.notna(v) else "" for v in seri_ch.values]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=LABEL_BULAN_X, y=seri_ch.values, mode='lines+markers+text', name="Curah Hujan",
        line=dict(color=WARNA_HUJAN, width=2, shape='spline'),
        marker=dict(size=9, color=WARNA_HUJAN, line=dict(color='white', width=1.5)),
        fill='tozeroy', fillcolor=WARNA_HUJAN_FILL,
        text=label_ch, textposition="top center", textfont=dict(size=10, color="white")
    ))
    fig.update_layout(
        title=judul,
        yaxis=dict(title=dict(text="mm", font=dict(size=13, color="white")), tickfont=dict(size=12, color="white"), gridcolor="#333333"),
        showlegend=False,
        **LAYOUT_UMUM
    )
    return fig


def render_doughnut(pct, judul):
    pct_tampil = min(max(pct, 0), 100)
    sisa = 100 - pct_tampil
    if pct >= 100:
        warna_capai = "#00C853"
    elif pct >= 90:
        warna_capai = "#FFC400"
    else:
        warna_capai = "#FF3D57"
    fig = go.Figure(data=[go.Pie(
        values=[pct_tampil, sisa], hole=0.68, sort=False, direction='clockwise',
        marker=dict(colors=[warna_capai, "#2A2A2A"], line=dict(color='#000000', width=3)),
        textinfo='none', hoverinfo='skip', showlegend=False
    )])
    fig.add_annotation(text=f"<b>{pct:.1f}%</b>", x=0.5, y=0.53, font=dict(size=32, color=warna_capai), showarrow=False)
    fig.add_annotation(text="Pencapaian", x=0.5, y=0.40, font=dict(size=12, color="#CCCCCC"), showarrow=False)
    fig.update_layout(title=judul, height=380, margin=dict(l=25, r=25, t=55, b=25),
                       title_font=dict(size=17, color="white"),
                       plot_bgcolor="#000000", paper_bgcolor="#000000")
    return fig


# --- 8. RENDER SELURUH HALAMAN, DIPISAH PER PT ---
TEMA_PT = {
    "BKB": {"label": "🌴 PT BKB", "gradient": "linear-gradient(90deg, #1B5E9E, #42A5F5)"},
    "FFD": {"label": "🌴 PT FFD", "gradient": "linear-gradient(90deg, #00695C, #26A69A)"},
}

for pt_kode, tema in TEMA_PT.items():
    st.markdown(f"<div class='pt-banner' style='background:{tema['gradient']};'>{tema['label']}</div>", unsafe_allow_html=True)

    df_hasil, ch_bulanan, pct_capaian, total_akt, total_tgt, ch_rata = hitung_data_pt(pt_kode)

    # --- Kartu KPI ringkas ---
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card(f"Total Aktual YTD s.d {pilihan_bulan}", f"{total_akt:,.0f} Ton", "#1565C0", "#5E92F3")
    with k2:
        render_kpi_card(f"Total {label_target} YTD", f"{total_tgt:,.0f} Ton", "#FB8C00", "#FFB74D")
    with k3:
        warna_pct = "#00C853" if pct_capaian >= 100 else ("#FFC400" if pct_capaian >= 90 else "#FF3D57")
        render_kpi_card("Pencapaian YTD", f"{pct_capaian:.1f}%", warna_pct, warna_pct)
    with k4:
        nilai_ch = f"{ch_rata:,.0f} mm" if pd.notna(ch_rata) else "N/A"
        render_kpi_card("Rata-rata Curah Hujan YTD", nilai_ch, "#00ACC1", "#4DD0E1")

    st.markdown("<div style='margin-top:6px;'></div>", unsafe_allow_html=True)

    # --- Grafik ---
    col1, col2 = st.columns(2)
    with col1:
        fig_yield = render_line_dua_seri(
            df_hasil, 'TON_AKT', 'TON_TGT',
            f"📈 Trend Yield Bulanan Jan - Des (Ton) vs {label_target}", "Ton",
            format_label=lambda v: f"{v:,.0f}" if v > 0 else ""
        )
        st.plotly_chart(fig_yield, use_container_width=True, key=f"chart_ton_{pt_kode}")
    with col2:
        fig_bjr = render_line_dua_seri(
            df_hasil, 'BJR_AKT', 'BJR_TGT',
            f"⚖️ Trend BJR Bulanan Jan - Des (Kg/Janjang) vs {label_target}", "Kg/Janjang",
            format_label=lambda v: f"{v:,.2f}" if v > 0 else ""
        )
        st.plotly_chart(fig_bjr, use_container_width=True, key=f"chart_bjr_{pt_kode}")

    col3, col4 = st.columns(2)
    with col3:
        fig_ch = render_line_hujan(ch_bulanan, f"🌧️ Trend Curah Hujan Bulanan (mm) - Tahun {TAHUN_AKTIF}")
        st.plotly_chart(fig_ch, use_container_width=True, key=f"chart_ch_{pt_kode}")
    with col4:
        fig_pct = render_doughnut(pct_capaian, f"🎯 Pencapaian Aktual vs {label_target} (s.d {pilihan_bulan})")
        st.plotly_chart(fig_pct, use_container_width=True, key=f"chart_pct_{pt_kode}")

    st.markdown("<hr style='margin-top:10px; margin-bottom:10px; border: 1px solid #EFEFF2;'>", unsafe_allow_html=True)