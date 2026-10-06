import re
from collections import Counter
from google_play_scraper import Sort, reviews
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from wordcloud import WordCloud

# ================== KONFIGURASI HALAMAN & CUSTOM CSS DARK MODE ==================
st.set_page_config(
    page_title="MyPertamina Sentiment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    /* Paksa Tema Gelap Modern */
    .stApp {
        background-color: #0b0e14 !important;
        color: #e6edf3 !important;
    }
    
    /* Header Container */
    .main-header {
        background: linear-gradient(90deg, #0d1117 0%, #161b22 100%);
        padding: 22px 28px;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 25px;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #58a6ff;
        margin: 0;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #8b949e;
        margin-top: 6px;
    }
    
    /* Card KPI */
    .card-kpi {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Card 5W1H */
    .card-5w1h {
        background-color: #161b22;
        border-left: 5px solid #58a6ff;
        border-radius: 8px;
        padding: 18px;
        margin-bottom: 14px;
        border-top: 1px solid #30363d;
        border-right: 1px solid #30363d;
        border-bottom: 1px solid #30363d;
    }
    .badge-5w1h {
        background-color: #1f6feb;
        color: #ffffff;
        padding: 4px 10px;
        border-radius: 4px;
        font-weight: bold;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 8px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ================== SIDEBAR NAVIGASI & SCRAPPER ==================
with st.sidebar:
    st.caption("BBDM 26D - FK UNDIP")
    st.markdown("## 📊 MyPertamina\n### Sentiment")
    st.markdown("---")

    st.markdown("### 🧭 NAVIGASI")
    halaman = st.radio(
        "Pilih Halaman:",
        [
            "📊 Ringkasan & KPI",
            "📈 Visualisasi Data",
            "📋 Tabel Ulasan",
            "🔍 Analisis 5W1H & Temuan",
            "💡 Rekomendasi & Keterbatasan",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### ⚙️ PENGATURAN SCRAPPER")
    app_id = st.text_input(
        "App ID Play Store",
        value="com.dafturn.mypertamina",
        help="Contoh: com.dafturn.mypertamina atau id.mypertamina.app",
    )
    jumlah = st.slider("Jumlah Ulasan Ditarik", 50, 500, 150, 10)
    btn_scrape = st.button("🚀 Tarik & Analisis Data", type="primary", use_container_width=True)

    st.markdown("---")
    st.markdown("### ℹ️ INFO PENELITIAN")
    st.caption(
        "Studi Sentimen Ulasan Pengguna MyPertamina pada Google Play Store (Periode Dinamis)."
    )


# ================== FUNGSI SENTIMEN & PENGOLAHAN DATA ==================
def tentukan_sentimen(skor):
    if skor >= 4:
        return "Positif"
    elif skor == 3:
        return "Netral"
    else:
        return "Negatif"


@st.cache_data(ttl=600)
def load_data(app_id_param, count_param):
    hasil = reviews(
        app_id_param.strip(),
        lang="id",
        country="id",
        sort=Sort.NEWEST,
        count=count_param,
    )
    data = hasil[0] if isinstance(hasil, tuple) else hasil
    if not data:
        return None
    df = pd.DataFrame(data)
    df["at"] = pd.to_datetime(df["at"])
    df["sentiment"] = df["score"].apply(tentukan_sentimen)
    return df


if "df_data" not in st.session_state:
    st.session_state.df_data = None

if btn_scrape or st.session_state.df_data is None:
    with st.spinner("Sedang menarik data ulasan terbaru dari Play Store..."):
        try:
            st.session_state.df_data = load_data(app_id, jumlah)
        except Exception as e:
            st.error(f"Gagal mengambil data dari Google Play Store: {e}")

df = st.session_state.df_data

# ================== HALAMAN UTAMA ==================
if df is None:
    st.warning("⚠️ Data ulasan tidak ditemukan. Pastikan App ID tepat dan koneksi internet stabil.")
else:
    # ------------------ 1. RINGKASAN & KPI ------------------
    if halaman == "📊 Ringkasan & KPI":
        st.markdown(
            f"""
            <div class="main-header">
                <h1 class="main-title">📊 Ringkasan & Indikator Kinerja Utama (KPI)</h1>
                <div class="sub-title">Ringkasan performa ulasan dan persepsi publik aplikasi <b>{app_id}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        total_ulasan = len(df)
        rata_rating = df["score"].mean()
        sentiment_counts = df["sentiment"].value_counts()
        sentiment_mayoritas = sentiment_counts.idxmax()
        pct_negatif = (df["sentiment"] == "Negatif").mean() * 100
        pct_positif = (df["sentiment"] == "Positif").mean() * 100

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Sampel Ulasan", f"{total_ulasan} Data")
        k2.metric("Rata-Rata Rating", f"{rata_rating:.2f} / 5.0")
        k3.metric("Sentimen Dominan", sentiment_mayoritas)
        k4.metric("Tingkat Keluhan (Negatif)", f"{pct_negatif:.1f}%")

        st.divider()
        st.subheader("📌 Ringkasan Eksekutif")
        st.info(
            f"Berdasarkan penarikan **{total_ulasan} ulasan terbaru**, aplikasi mendapatkan skor rerata **{rata_rating:.2f}** dari 5.0. "
            f"Sebanyak **{pct_positif:.1f}%** ulasan ber-sentimen Positif, sementara **{pct_negatif:.1f}%** menyampaikan keluhan (Negatif). "
            f"Sentimen dominan publik saat ini berada pada kategori **{sentiment_mayoritas}**."
        )

        st.subheader("📉 Gambaran Tren Ulasan Harian")
        df_daily = df.groupby(df["at"].dt.date)["score"].agg(["count", "mean"]).reset_index()
        fig_trend = px.line(
            df_daily,
            x="at",
            y="count",
            title="Frekuensi Ulasan Pengguna Per Hari",
            labels={"at": "Tanggal", "count": "Jumlah Ulasan"},
            template="plotly_dark",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    # ------------------ 2. VISUALISASI DATA ------------------
    elif halaman == "📈 Visualisasi Data":
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-title">📈 Visualisasi Data Sentimen & Teks</h1>
                <div class="sub-title">Grafik interaktif, sebaran rating, dan analisis kata kunci terbanyak (Word Cloud)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Distribusi Sentimen")
            ringkasan = df["sentiment"].value_counts().reindex(["Positif", "Netral", "Negatif"]).fillna(0)
            fig_pie = px.pie(
                values=ringkasan.values,
                names=ringkasan.index,
                hole=0.4,
                color=ringkasan.index,
                color_discrete_map={"Positif": "#238636", "Netral": "#8b949e", "Negatif": "#da3633"},
                template="plotly_dark",
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            st.subheader("⭐ Distribusi Rating (1-5 Bintang)")
            rating_counts = df["score"].value_counts().sort_index().reset_index()
            rating_counts.columns = ["Rating", "Jumlah"]
            fig_bar = px.bar(
                rating_counts,
                x="Rating",
                y="Jumlah",
                color="Rating",
                color_continuous_scale="Reds_r",
                template="plotly_dark",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()
        st.subheader("☁️ Word Cloud (Kata Paling Sering Muncul)")
        stopwords = set(
            [
                "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
                "saya", "aplikasi", "app", "ada", "tidak", "tak", "gak", "nggak",
                "sudah", "belum", "juga", "karena", "kalo", "kalau", "sangat",
                "bisa", "atau", "jadi", "pada", "lebih", "saat", "akan", "banyak",
                "tolong", "bintang", "nya", "mau", "biar", "lagi", "selalu"
            ]
        )
        semua_teks = " ".join(df["content"].dropna().astype(str)).lower()
        kata_kata = re.sub(r"[^a-zA-Z\s]", " ", semua_teks)

        if kata_kata.strip():
            wordcloud = WordCloud(
                width=1000,
                height=400,
                background_color="#0d1117",
                stopwords=stopwords,
                colormap="Blues",
            ).generate(kata_kata)

            fig_wc, ax_wc = plt.subplots(figsize=(10, 4))
            fig_wc.patch.set_facecolor("#0d1117")
            ax_wc.imshow(wordcloud, interpolation="bilinear")
            ax_wc.axis("off")
            st.pyplot(fig_wc)
            plt.close(fig_wc)

    # ------------------ 3. TABEL ULASAN ------------------
    elif halaman == "📋 Tabel Ulasan":
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-title">📋 Dataset Ulasan Pengguna</h1>
                <div class="sub-title">Filter, cari, dan unduh data mentah ulasan pengguna Google Play Store</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_filter1, c_filter2 = st.columns([1, 2])
        with c_filter1:
            pilihan_sentimen = st.multiselect(
                "Filter Sentimen:",
                ["Positif", "Netral", "Negatif"],
                default=["Positif", "Netral", "Negatif"],
            )
        with c_filter2:
            search_query = st.text_input("🔍 Cari Kata Kunci:", placeholder="Contoh: login, error, qr, verifikasi")

        df_filtered = df[df["sentiment"].isin(pilihan_sentimen)]
        if search_query:
            df_filtered = df_filtered[df_filtered["content"].str.contains(search_query, case=False, na=False)]

        st.dataframe(
            df_filtered[["userName", "content", "score", "sentiment", "at"]],
            use_container_width=True,
            height=450,
        )

        csv_data = df_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Dataset Filtered (CSV)",
            data=csv_data,
            file_name=f"dataset_ulasan_{app_id}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # ------------------ 4. ANALISIS 5W1H & TEMUAN ------------------
    elif halaman == "🔍 Analisis 5W1H & Temuan":
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-title">🔍 Analisis 5W + 1H & Temuan Utama</h1>
                <div class="sub-title">Ekstraksi wawasan otomatis berdasarkan pengolahan kata dan statistik sentimen</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        stopwords = {
            "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
            "saya", "aplikasi", "app", "ada", "tidak", "tak", "gak", "nggak",
            "sudah", "belum", "juga", "karena", "kalo", "kalau", "sangat",
            "bisa", "atau", "jadi", "pada", "lebih", "saat", "akan", "banyak",
            "tolong", "bintang", "nya", "biar", "mau"
        }
        semua_teks = " ".join(df["content"].dropna().astype(str)).lower()
        kata_kata = re.sub(r"[^a-zA-Z\s]", " ", semua_teks).split()
        kata_filter = [k for k in kata_kata if len(k) > 3 and k not in stopwords]
        top5 = Counter(kata_filter).most_common(5)
        what = ", ".join([f"<b>'{k}'</b> ({v}x)" for k, v in top5]) if top5 else "Tidak cukup kata unik"

        tgl_awal = df["at"].min().strftime("%d %B %Y")
        tgl_akhir = df["at"].max().strftime("%d %B %Y")

        persen = df["sentiment"].value_counts(normalize=True) * 100
        pct_pos = persen.get("Positif", 0)
        pct_net = persen.get("Netral", 0)
        pct_neg = persen.get("Negatif", 0)

        if pct_neg >= 50:
            why = "Pengguna mendominasi keluhan pada masalah operasional seperti error sistem, kendala verifikasi akun, kegagalan transaksi, atau lambatnya pemrosesan."
            how = f"Status kinerja memerlukan <b>PERBAIKAN KRITIS</b> ({pct_pos:.1f}% Positif, {pct_net:.1f}% Netral, {pct_neg:.1f}% Negatif)."
        else:
            why = "Pengguna merespons positif kemudahan akses layanan dan fitur utama aplikasi."
            how = f"Status kinerja berada dalam tingkat <b>STABIL / CUKUP BAIK</b> ({pct_pos:.1f}% Positif, {pct_net:.1f}% Netral, {pct_neg:.1f}% Negatif)."

        items_5w1h = [
            ("WHAT (Topik Utama)", f"Kata kunci terbanyak yang menjadi pusat perbincangan: {what}."),
            ("WHO (Objek Responden)", f"Responden ulasan adalah pengguna aktif aplikasi <b>{app_id}</b>."),
            ("WHERE (Lokasi/Sumber Data)", "Data diperoleh secara transparan dari platform publik <b>Google Play Store</b>."),
            ("WHEN (Rentang Waktu)", f"Data mencakup ulasan dari <b>{tgl_awal}</b> sampai <b>{tgl_akhir}</b>."),
            ("WHY (Faktor Penyebab)", why),
            ("HOW (Evaluasi Status)", how),
        ]

        for title, desc in items_5w1h:
            st.markdown(
                f"""
                <div class="card-5w1h">
                    <span class="badge-5w1h">{title}</span>
                    <div style="color: #c9d1d9; font-size: 0.95rem;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ------------------ 5. REKOMENDASI & KETERBATASAN ------------------
    elif halaman == "💡 Rekomendasi & Keterbatasan":
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-title">💡 Rekomendasi Strategic & Keterbatasan Studi</h1>
                <div class="sub-title">Langkah perbaikan sistem dan batasan metodologi penarikan data</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_rec, col_lim = st.columns(2)
        with col_rec:
            st.subheader("🚀 Rekomendasi Perbaikan")
            st.markdown(
                """
                - **Optimasi Server & API Response:** Memperkuat infrastruktur backend untuk menangani beban trafik tinggi saat jam operasional.
                - **Penyederhanaan Alur Verifikasi (UX):** Mengurangi tahapan rumit saat pendaftaran akun dan verifikasi plat kendaraan/QR Code.
                - **Manajemen Ulasan Aktif (Customer Care):** Merespons ulasan bintang 1 & 2 di Play Store secara cepat untuk memberikan troubleshooting langsung.
                - **Pemberitahuan Maintenance Transparan:** Memberikan info pemeliharaan sistem di dalam aplikasi agar pengguna tidak salah paham.
                """
            )

        with col_lim:
            st.subheader("⚠️ Keterbatasan Penelitian")
            st.markdown(
                """
                - **Ukuran Sampel Scraped:** Penarikan terbatas pada kuota sampel ulasan terbaru yang tersedia melalui API Google Play Store.
                - **Pembersihan Teks (Stopwords):** Pengolahan kata menggunakan filter berbasis aturan baku yang mungkin melewatkan kata-kata gaul atau typo.
                - **Deteksi Sarcasm:** Sentimen diklasifikasikan berdasar rating bintang, sehingga kalimat sarkasme mungkin tidak sepenuhnya terdeteksi dari teks murni.
                """
            )