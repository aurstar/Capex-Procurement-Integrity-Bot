"""Pengujian input-output (Tabel 6.1). Jalankan: python test_engine.py"""
import samples, engine, security

def run(fn): return engine.validate(fn())
def kats(r): return {f["kategori"] for f in r["temuan"]}

def test_u01():
    r = run(samples.u01); assert r["status_kecocokan"] == "Cocok" and r["skor_risiko"] == 0 and r["tingkat"] == "Rendah" and not r["temuan"]
def test_u02():
    r = run(samples.u02); assert r["status_kecocokan"] == "Tidak cocok" and {"harga_selisih", "di_atas_daftar_harga"} <= kats(r) and r["tingkat"] == "Tinggi"
def test_u03():
    r = run(samples.u03); assert "kuantitas" in kats(r) and r["tahan_pembayaran"] and r["tingkat"] == "Menengah"
    assert any("selisih 3" in f["uraian"] for f in r["temuan"])
def test_u04():
    r = run(samples.u04); assert "invoice_ganda" in kats(r) and r["tingkat"] == "Tinggi" and r["blokir_erp"]
def test_u05():
    r = run(samples.u05); assert "dokumen_tanpa_pasangan" in kats(r) and r["blokir_erp"] and r["tingkat"] == "Tinggi"
def test_u06():
    r = run(samples.u06); assert "urutan_tanggal" in kats(r) and r["skor_risiko"] > 0
def test_u07():
    r = run(samples.u07); assert r["status_kecocokan"] == "Cocok" and not r["temuan"]
    assert any("kesetaraan makna" in row["metode_cocok"] for row in r["detail_item"])
def test_u08():
    r = run(samples.u08); assert "keyakinan_rendah" in kats(r) and r["perlu_periksa_manusia"] and r["tingkat"] != "Rendah"
def test_u09():
    r = run(samples.u09); assert "kapitalisasi" in kats(r) and r["blokir_erp"]
def test_u10():
    assert security.can("Manajer Keuangan", "authorize")
    for role in security.ROLES:
        if role != "Manajer Keuangan": assert not security.can(role, "authorize")
    assert not security.can("Hutang Usaha", "view_audit")
    log = security.AuditLog(); log.add("Hutang Usaha", "AKSES_DITOLAK", "authorize", "uji U-10"); log.add("Manajer Keuangan", "OTORISASI", "PO-1")
    assert log.verify()
    log.entries[0]["detail"] = "diubah"; assert not log.verify()
def test_mask(): assert security.mask("1234567890") == "******7890"

if __name__ == "__main__":
    n = 0
    for k, v in sorted(globals().items()):
        if k.startswith("test_"): v(); n += 1; print("lulus", k)
    print("%d pengujian lulus" % n)
