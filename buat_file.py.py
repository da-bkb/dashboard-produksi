import os

# Tentukan folder utama proyek
base_dir = os.path.dirname(os.path.abspath(__file__))
tabs_dir = os.path.join(base_dir, "tabs")

# Buat folder 'tabs' jika belum ada
if not os.path.exists(tabs_dir):
    os.makedirs(tabs_dir)
    print("-> Folder 'tabs' berhasil dibuat.")

# Daftar file yang wajib ada beserta isinya
files_to_create = {
    "yield_perf.py": "import streamlit as st\nst.title('🌱 Yield Performa (Ton/ha)')\nst.info('Halaman ini siap diisi logika Yield.')",
    "janjang_pokok.py": "import streamlit as st\nst.title('🌴 Janjang / Pokok (J/P)')\nst.info('Halaman ini siap diisi logika J/P.')",
    "bjr_perf.py": "import streamlit as st\nst.title('⚖️ Berat Janjang Rata-rata (BJR)')\nst.info('Halaman ini siap diisi logika BJR.')",
    "trend_bln.py": "import streamlit as st\nst.title('📊 Trend Bulanan Kebun')\nst.info('Halaman ini siap diisi grafik Trend Bulanan.')",
    "trend_afd.py": "import streamlit as st\nst.title('📉 Trend Afdeling')\nst.info('Halaman ini siap diisi analisis Trend Afdeling.')"
}

# Mulai membuat file secara bersih langsung dari script
for file_name, content in files_to_create.items():
    file_path = os.path.join(tabs_dir, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"-> File '{file_name}' berhasil dibuat di folder tabs.")

print("\n[SUKSES] Semua file tab kosongan sudah aman. Silakan jalankan kembali streamlit run app.py!")