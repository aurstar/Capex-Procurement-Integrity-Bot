"""Mesin validasi tiga dokumen dan analisis risiko (proses DFD 2.0 dan 3.0).
Prototipe ini deterministik: tahap OCR/LLM disimulasikan oleh data hasil ekstraksi (lihat samples.py),
sedangkan pencocokan, pemeriksaan kebijakan, dan skor risiko dijalankan oleh kode ini."""
import re
from datetime import date
from difflib import SequenceMatcher
import kb

BOBOT = {  # kontribusi ke skor risiko (0..1)
    "harga_selisih": 0.35, "harga_toleransi": 0.05, "di_atas_daftar_harga": 0.25,
    "kuantitas": 0.30, "dokumen_tanpa_pasangan": 0.50, "invoice_ganda": 0.60,
    "urutan_tanggal": 0.35, "invoice_sebelum_penerimaan": 0.25, "keyakinan_rendah": 0.30,
    "pola_vendor": 0.15, "identitas": 0.30, "kapitalisasi": 0.30,
}
BLOKIR_ERP = {"dokumen_tanpa_pasangan", "invoice_ganda", "kapitalisasi", "keyakinan_rendah"}
STOP = {"hydraulic", "unit", "alat", "berat", "by", "baru", "new"}

def _tokens(s):
    s = re.sub(r"(\d+)\s*(ton|t)\b", r"\1t", s.lower())
    return {t for t in re.split(r"[^a-z0-9]+", s) if t and t not in STOP}

def similarity(a, b):
    ta, tb = _tokens(a), _tokens(b)
    return len(ta & tb) / len(ta | tb) if ta | tb else 0.0

def _d(s): return date.fromisoformat(s)

def find_item(po_item, items):
    """Cari pasangan item PO pada dokumen lain: nomor seri, lalu kode, lalu kemiripan makna deskripsi."""
    for it in items:
        if po_item.get("serial") and it.get("serial") == po_item["serial"]: return it, "nomor seri"
    for it in items:
        if it.get("kode") == po_item.get("kode"): return it, "kode item"
    best, score = None, 0.0
    for it in items:
        sc = similarity(po_item["deskripsi"], it["deskripsi"])
        if sc > score: best, score = it, sc
    return (best, "kesetaraan makna deskripsi (%.0f%%)" % (score * 100)) if score >= 0.5 else (None, None)

def validate(tx):
    po, rr, inv, cap = tx["po"], tx.get("rr"), tx["inv"], tx.get("cap")
    F = []  # temuan
    def add(kat, uraian, ref=""):
        F.append({"kategori": kat, "uraian": uraian, "rujukan": ref, "bobot": BOBOT[kat]})

    # --- keyakinan ekstraksi (ambang batas)
    for nm, doc in (("PO", po), ("Receiving report", rr), ("Invoice", inv)):
        if doc:
            low = {f: c for f, c in doc.get("confidence", {}).items() if c < kb.AMBANG_KEYAKINAN}
            if low:
                add("keyakinan_rendah", "%s: field %s berkeyakinan rendah (%s); diteruskan ke pemeriksaan manusia, tidak diproses otomatis."
                    % (nm, ", ".join(low), ", ".join("%.2f" % c for c in low.values())), "Ambang keyakinan %.2f" % kb.AMBANG_KEYAKINAN)

    # --- dokumen tanpa pasangan
    if rr is None:
        add("dokumen_tanpa_pasangan", "Invoice %s tidak memiliki receiving report untuk PO %s." % (inv["no"], po["no"]), "Pencocokan tiga dokumen (KF-03)")
    if inv.get("po_no") != po["no"] or (rr and rr.get("po_no") != po["no"]):
        add("identitas", "Nomor PO pada dokumen tidak konsisten.", "PO %s" % po["no"])
    vendors = {po["vendor"], inv["vendor"]} | ({rr["vendor"]} if rr else set())
    if len(vendors) > 1:
        add("identitas", "Nama vendor berbeda antar dokumen: %s." % ", ".join(sorted(vendors)), "PO %s" % po["no"])

    # --- kuantitas dan harga per item
    detail = []
    for pi in po["items"]:
        r_it, r_m = find_item(pi, rr["items"]) if rr else (None, None)
        i_it, i_m = find_item(pi, inv["items"])
        row = {"item": pi["deskripsi"], "qty_po": pi["qty"], "qty_rr": r_it["qty_diterima"] if r_it else None,
               "qty_inv": i_it["qty"] if i_it else None, "harga_po": pi["harga"], "harga_inv": i_it["harga"] if i_it else None,
               "metode_cocok": i_m or "-"}
        detail.append(row)
        if rr and r_it and r_it["qty_diterima"] != pi["qty"]:
            add("kuantitas", "%s: kuantitas PO %s, diterima %s (selisih %s)." % (pi["deskripsi"], pi["qty"], r_it["qty_diterima"], pi["qty"] - r_it["qty_diterima"]), "PO %s vs RR %s" % (po["no"], rr["no"]))
        if i_it and rr and r_it and i_it["qty"] != r_it["qty_diterima"]:
            add("kuantitas", "%s: ditagih %s, diterima %s." % (pi["deskripsi"], i_it["qty"], r_it["qty_diterima"]), "RR %s vs INV %s" % (rr["no"], inv["no"]))
        if i_it:
            sel = (i_it["harga"] - pi["harga"]) / pi["harga"] * 100
            if abs(sel) > kb.TOLERANSI_HARGA_PCT:
                add("harga_selisih", "%s: harga invoice Rp%s vs PO Rp%s (%+.1f%%)." % (pi["deskripsi"], f"{i_it['harga']:,}", f"{pi['harga']:,}", sel), "PO %s vs INV %s" % (po["no"], inv["no"]))
            elif sel != 0:
                add("harga_toleransi", "%s: selisih harga %+.2f%% masih dalam toleransi." % (pi["deskripsi"], sel), "Toleransi %.1f%%" % kb.TOLERANSI_HARGA_PCT)
            pl = kb.PRICE_LIST.get(pi.get("kode"))
            if pl and i_it["harga"] > pl["harga"] * (1 + kb.TOLERANSI_HARGA_PCT / 100):
                add("di_atas_daftar_harga", "%s: harga invoice melebihi daftar harga disepakati Rp%s." % (pi["deskripsi"], f"{pl['harga']:,}"), pl["ref"])
        else:
            add("identitas", "Item '%s' pada PO tidak ditemukan pada invoice." % pi["deskripsi"], "INV %s" % inv["no"])

    # --- urutan tanggal
    if rr and _d(rr["tanggal"]) < _d(po["tanggal"]):
        add("urutan_tanggal", "Receiving report (%s) mendahului PO (%s)." % (rr["tanggal"], po["tanggal"]), "KF-04")
    if rr and _d(inv["tanggal"]) < _d(rr["tanggal"]):
        add("invoice_sebelum_penerimaan", "Invoice (%s) tiba sebelum receiving report (%s)." % (inv["tanggal"], rr["tanggal"]), "KF-04")
    if _d(inv["tanggal"]) < _d(po["tanggal"]):
        add("urutan_tanggal", "Invoice (%s) mendahului PO (%s)." % (inv["tanggal"], po["tanggal"]), "KF-04")

    # --- invoice ganda dan pola vendor (KF-05)
    for h in kb.INVOICE_HISTORY:
        if h["no"] == inv["no"] and h["jumlah"] == inv["jumlah"]:
            add("invoice_ganda", "Invoice %s (Rp%s) sudah pernah diproses pada %s." % (inv["no"], f"{inv['jumlah']:,}", h["tanggal"]), "Riwayat invoice")
    if kb.VENDOR_PO_HISTORY[-5:].count(po["vendor"]) + 1 >= kb.AMBANG_VENDOR_BERULANG:
        add("pola_vendor", "Vendor %s dipilih berulang pada PO-PO terakhir." % po["vendor"], "Riwayat PO vendor")

    # --- kewajaran data kapitalisasi (KF-11)
    if cap:
        pol = kb.CAP_POLICY[cap["kategori"]]
        if not pol["umur_min"] <= cap["umur_manfaat"] <= pol["umur_max"]:
            add("kapitalisasi", "Umur manfaat %s tahun di luar kebijakan (%s-%s tahun)." % (cap["umur_manfaat"], pol["umur_min"], pol["umur_max"]), pol["ref"])
        rp = cap["nilai_residu"] / cap["nilai_perolehan"] * 100
        if rp > pol["residu_maks_pct"]:
            add("kapitalisasi", "Nilai residu %.0f%% melebihi batas kebijakan %s%%." % (rp, pol["residu_maks_pct"]), pol["ref"])
        if rr and _d(cap["tanggal_siap_pakai"]) < _d(rr["tanggal"]):
            add("kapitalisasi", "Tanggal siap pakai (%s) mendahului tanggal penerimaan (%s)." % (cap["tanggal_siap_pakai"], rr["tanggal"]), pol["ref"])

    # --- skor, routing, status
    kats = {f["kategori"] for f in F}
    skor = round(min(1.0, sum(BOBOT[k] for k in kats)), 2)   # satu bobot per kategori temuan
    tingkat = "Rendah" if skor < 0.30 else "Menengah" if skor < 0.60 else "Tinggi"
    if kats & {"dokumen_tanpa_pasangan", "invoice_ganda"}: tingkat = "Tinggi"
    if "keyakinan_rendah" in kats and tingkat == "Rendah": tingkat = "Menengah"
    material = kats - {"harga_toleransi"}
    status = "Cocok" if not kats else ("Selisih dalam toleransi" if not material else "Tidak cocok")
    routing = {"Rendah": "Telaah ringkas Hutang Usaha", "Menengah": "Telaah rinci Hutang Usaha",
               "Tinggi": "Eskalasi ke Manajer Keuangan dan Audit Internal"}[tingkat]
    alasan = "Seluruh pemeriksaan lolos; tidak ada temuan." if not F else " ".join("(%d) %s" % (i + 1, f["uraian"]) for i, f in enumerate(F))
    return {"status_kecocokan": status, "skor_risiko": skor, "tingkat": tingkat, "routing": routing,
            "temuan": F, "detail_item": detail, "alasan": alasan,
            "rujukan_dokumen": sorted({f["rujukan"] for f in F if f["rujukan"]}),
            "tahan_pembayaran": bool(material), "blokir_erp": bool(kats & BLOKIR_ERP),
            "perlu_periksa_manusia": "keyakinan_rendah" in kats}
