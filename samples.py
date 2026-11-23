"""Data hasil ekstraksi yang disimulasikan (keluaran tahap OCR + LLM) untuk skenario U-01 s.d. U-10 (Tabel 6.1)."""
import copy

CONF_OK = {"no": 0.98, "vendor": 0.97, "qty": 0.96, "harga": 0.95, "tanggal": 0.97}
UNIT = {"kode": "EXC-PC200", "deskripsi": "Excavator 20 ton Komatsu PC200-8", "serial": "KMT-PC200-88421"}
KIT = {"kode": "FLT-HYD-KIT", "deskripsi": "Hydraulic filter kit", "serial": None}

def base():
    return {
        "po": {"no": "PO-2026-00101", "vendor": "PT Alfa Heavy Indo", "tanggal": "2026-03-02", "termin": "30 hari",
               "items": [dict(UNIT, qty=1, harga=2_450_000_000), dict(KIT, qty=10, harga=12_500_000)],
               "ppn": 283_250_000, "jumlah": 2_858_250_000, "confidence": dict(CONF_OK)},
        "rr": {"no": "RR-2026-00088", "po_no": "PO-2026-00101", "vendor": "PT Alfa Heavy Indo", "tanggal": "2026-03-20",
               "items": [dict(UNIT, qty_diterima=1), dict(KIT, qty_diterima=10)], "confidence": dict(CONF_OK)},
        "inv": {"no": "INV-ALF-7790", "po_no": "PO-2026-00101", "vendor": "PT Alfa Heavy Indo", "tanggal": "2026-03-25",
                "items": [dict(UNIT, qty=1, harga=2_450_000_000), dict(KIT, qty=10, harga=12_500_000)],
                "ppn": 283_250_000, "jumlah": 2_858_250_000, "confidence": dict(CONF_OK)},
        "cap": {"kategori": "alat_berat", "nilai_perolehan": 2_450_000_000, "tanggal_siap_pakai": "2026-03-28",
                "umur_manfaat": 8, "nilai_residu": 245_000_000},
    }

def u01(): return base()
def u02():
    t = base(); t["inv"]["items"][0]["harga"] = 2_580_000_000
    t["inv"]["jumlah"] = 2_580_000_000 + 125_000_000 + 297_550_000; t["inv"]["ppn"] = 297_550_000; return t
def u03():
    t = base(); t["rr"]["items"][1]["qty_diterima"] = 7; return t
def u04():
    t = base(); t["inv"]["no"] = "INV-ALF-7781"; return t   # sama dengan riwayat invoice
def u05():
    t = base(); t["rr"] = None; return t
def u06():
    t = base(); t["rr"]["tanggal"] = "2026-02-25"; t["cap"]["tanggal_siap_pakai"] = "2026-03-01"; return t
def u07():
    t = base()
    t["rr"]["items"][0].update(kode="KMT-EXC-20", deskripsi="Komatsu PC200 Excavator (20T)")
    t["inv"]["items"][0].update(kode="HE-0451", deskripsi="Hydraulic Excavator PC200-8 Komatsu", serial=None)
    return t
def u08():
    t = base(); t["inv"]["confidence"].update(harga=0.62, qty=0.71); return t
def u09():
    t = base(); t["cap"].update(umur_manfaat=25, nilai_residu=980_000_000); return t

SKENARIO = {
    "U-01 Transaksi normal": u01, "U-02 Selisih harga": u02, "U-03 Selisih kuantitas": u03,
    "U-04 Invoice ganda": u04, "U-05 Dokumen tanpa pasangan": u05, "U-06 Urutan tanggal tidak wajar": u06,
    "U-07 Deskripsi tidak seragam": u07, "U-08 Kualitas dokumen rendah": u08, "U-09 Data kapitalisasi tidak wajar": u09,
}
