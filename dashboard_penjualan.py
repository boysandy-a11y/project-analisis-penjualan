# dashboard_penjualan.py
# Dashboard interaktif penjualan material bangunan Toko Duta Graha
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st

FILE = "Barang_Terjual_1_Tahun_Terakhir.xlsx"
NAMA_BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
              "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
NAMA_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

st.set_page_config(page_title="Dashboard Penjualan Toko Duta Graha", layout="wide")
sns.set_theme(style="whitegrid")
WARNA = "#3B6EA5"


@st.cache_data
def muat_data():
    df = pd.read_excel(FILE, sheet_name="Detail", dtype={"Kode Barang": str})
    df = df.rename(columns={"No Transaksi": "no_transaksi", "Tanggal": "tanggal",
                            "Jenis": "jenis", "Kode Barang": "kode_barang",
                            "Nama Barang": "nama_barang", "Satuan": "satuan",
                            "Jumlah": "jumlah", "Harga Satuan (Rp)": "harga_satuan",
                            "Total (Rp)": "total"})
    df["bulan"] = df["tanggal"].dt.to_period("M")
    df["hari"] = df["tanggal"].dt.dayofweek
    df["label_bulan"] = df["bulan"].apply(lambda p: f"{NAMA_BULAN[p.month - 1]} {str(p.year)[2:]}")
    return df


def rupiah(x):
    return "Rp" + f"{x:,.0f}".replace(",", ".")


df = muat_data()

st.title("Dashboard Penjualan Material Bangunan")
st.caption("Toko Duta Graha | Data penjualan asli, 24 November 2025 sampai 28 Oktober 2026")

# ---------- Filter (sidebar) ----------
st.sidebar.header("Filter")
tgl_min, tgl_max = df["tanggal"].dt.date.min(), df["tanggal"].dt.date.max()
rentang = st.sidebar.date_input("Rentang tanggal", (tgl_min, tgl_max),
                                min_value=tgl_min, max_value=tgl_max)
semua_jenis = sorted(df["jenis"].unique())
pilih_jenis = st.sidebar.multiselect("Jenis barang (kosong = semua)", semua_jenis)

data = df
if len(rentang) == 2:
    data = data[(data["tanggal"].dt.date >= rentang[0]) & (data["tanggal"].dt.date <= rentang[1])]
if pilih_jenis:
    data = data[data["jenis"].isin(pilih_jenis)]

if data.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

# ---------- Ringkasan ----------
trx = data.groupby("no_transaksi")["total"].sum()
k1, k2, k3, k4 = st.columns([2.2, 1.2, 1.8, 1.8])
k1.metric("Total penjualan", rupiah(data["total"].sum()))
k2.metric("Jumlah transaksi", f"{len(trx):,}".replace(",", "."))
k3.metric("Rata-rata per transaksi", rupiah(trx.mean()))
k4.metric("Median per transaksi", rupiah(trx.median()))

# ---------- Grafik (Matplotlib dan Seaborn, sama dengan grafik statis di laporan) ----------
kiri, kanan = st.columns(2)

with kiri:
    st.subheader("Total penjualan per jenis barang")
    top_n = st.slider("Jumlah jenis ditampilkan", 5, 20, 10)
    jenis = (data.groupby("jenis")["total"].sum().sort_values(ascending=False)
             .head(top_n) / 1e6)
    fig, ax = plt.subplots(figsize=(6, 0.38 * max(len(jenis), 3) + 1.2))
    sns.barplot(x=jenis.values, y=jenis.index, color=WARNA, ax=ax)
    ax.bar_label(ax.containers[0], fmt="%.0f", padding=3, fontsize=8)
    ax.set(xlabel="Total penjualan (juta Rp)", ylabel="")
    fig.tight_layout()
    st.pyplot(fig)

with kanan:
    st.subheader("Total penjualan bulanan")
    bln = data.groupby("bulan").agg(total=("total", "sum"), label=("label_bulan", "first"))
    fig, ax = plt.subplots(figsize=(6, 4.2))
    sns.lineplot(x=bln["label"].values, y=bln["total"].values / 1e6, marker="o",
                 color=WARNA, ax=ax)
    ax.set_ylim(bottom=0)
    ax.set(xlabel="Bulan", ylabel="Total penjualan (juta Rp)")
    plt.setp(ax.get_xticklabels(), rotation=45)
    fig.tight_layout()
    st.pyplot(fig)
    st.caption("November 2025 dan Oktober 2026 bukan bulan penuh.")

kiri2, kanan2 = st.columns(2)

with kiri2:
    st.subheader("Jumlah transaksi per hari")
    hr = data.groupby("hari")["no_transaksi"].nunique()
    hr.index = [NAMA_HARI[i] for i in hr.index]
    fig, ax = plt.subplots(figsize=(6, 3.4))
    sns.barplot(x=hr.values, y=hr.index, color=WARNA, ax=ax)
    ax.bar_label(ax.containers[0], fmt="%d", padding=3, fontsize=8)
    ax.set(xlabel="Jumlah transaksi", ylabel="")
    fig.tight_layout()
    st.pyplot(fig)

with kanan2:
    st.subheader("Sepuluh produk dengan nilai penjualan terbesar")
    produk = (data.groupby(["nama_barang", "satuan"])
              .agg(transaksi=("no_transaksi", "nunique"), total=("total", "sum"))
              .reset_index().sort_values("total", ascending=False).head(10))
    produk["produk"] = produk["nama_barang"].str.strip() + " (" + produk["satuan"] + ")"
    produk["total_penjualan"] = produk["total"].apply(rupiah)
    st.dataframe(produk[["produk", "transaksi", "total_penjualan"]],
                 hide_index=True, width="stretch")

with st.expander("Lihat data mentah (100 baris pertama)"):
    st.dataframe(data[["no_transaksi", "tanggal", "jenis", "nama_barang", "satuan",
                       "jumlah", "harga_satuan", "total"]].head(100),
                 hide_index=True, width="stretch")
