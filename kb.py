"""Basis pengetahuan (D3) simulasi untuk PT Nusa Karya Pertambangan (NKP).
Seluruh angka adalah ASUMSI proyek, bukan data perusahaan nyata (lihat Bab I subbab 1.2)."""

PRICE_LIST = {  # kode_item -> {vendor: harga_disepakati}, rujukan dokumen sumber
    "EXC-PC200": {"vendor": "PT Alfa Heavy Indo", "harga": 2_450_000_000, "ref": "Daftar Harga HD-2026 no. 3; Kontrak NKP-K-014 pasal 4"},
    "FLT-HYD-KIT": {"vendor": "PT Alfa Heavy Indo", "harga": 12_500_000, "ref": "Daftar Harga HD-2026 no. 17; Kontrak NKP-K-014 lampiran B"},
}

# Kebijakan kapitalisasi dan penyusutan (asumsi)
CAP_POLICY = {
    "alat_berat": {"umur_min": 5, "umur_max": 10, "residu_maks_pct": 15,
                   "ref": "Kebijakan Kapitalisasi dan Penyusutan NKP no. KB-07, bagian 3"},
}

# Riwayat transaksi untuk deteksi invoice ganda dan pola vendor
INVOICE_HISTORY = [
    {"no": "INV-ALF-7781", "vendor": "PT Alfa Heavy Indo", "jumlah": 2_858_250_000, "tanggal": "2026-03-26"},
]
VENDOR_PO_HISTORY = ["PT Alfa Heavy Indo", "PT Borneo Mesin", "PT Cakra Teknik", "PT Borneo Mesin", "PT Alfa Heavy Indo"]

TOLERANSI_HARGA_PCT = 1.0      # selisih harga satuan yang masih dianggap wajar
AMBANG_KEYAKINAN = 0.80        # confidence threshold ekstraksi
AMBANG_VENDOR_BERULANG = 4     # PO ke vendor yang sama dari 5 PO terakhir
