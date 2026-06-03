# --- PROSES DATA AKUMULASI (YEAR TO DATE - YTD) ---
URUTAN_BULAN_STANDAR = ['JAN', 'FEB', 'MAR', 'APR', 'MEI', 'JUN', 'JUL', 'AGS', 'SEP', 'OKT', 'NOV', 'DES']

# Standarisasi Input Agustus jika dari widget tertulis AGUSTUS
pilihan_bulan_std = "AGS" if pilihan_bulan in ["AGUSTUS", "AGS"] else pilihan_bulan

if pilihan_bulan_std in URUTAN_BULAN_STANDAR:
    idx_bulan = URUTAN_BULAN_STANDAR.index(pilihan_bulan_std)
    bulan_ytd = URUTAN_BULAN_STANDAR[:idx_bulan + 1]
else:
    list_bulan_raw = list(df_raw['Bulan'].unique())
    if pilihan_bulan_std in list_bulan_raw:
        idx_bulan = list_bulan_raw.index(pilihan_bulan_std)
        bulan_ytd = list_bulan_raw[:idx_bulan + 1]
    else:
        bulan_ytd = [pilihan_bulan_std]

# Filter data YTD menggunakan list bulan standar yang sudah lolos verifikasi
df_ytd = df_raw[df_raw['Bulan'].isin(bulan_ytd)].copy()

# Afdeling ytd group
df_afd_ytd_grp = df_ytd.groupby('Afdeling').agg({
    'Kg Akt.': 'sum',
    'Kg Bgt.': 'sum',
    'Luas': 'first'
}).reset_index()

df_afd_ytd_grp['Yield_Akt'] = df_afd_ytd_grp['Kg Akt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Bgt'] = df_afd_ytd_grp['Kg Bgt.'] / df_afd_ytd_grp['Luas'] / 1000
df_afd_ytd_grp['Yield_Pct'] = (df_afd_ytd_grp['Yield_Akt'] / df_afd_ytd_grp['Yield_Bgt'] * 100).fillna(0)