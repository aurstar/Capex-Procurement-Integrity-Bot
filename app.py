"""Capex & Procurement Integrity Bot - prototipe antarmuka (Streamlit).
Jalankan: streamlit run app.py
Empat layar mengikuti Bab VI subbab 6.3: Unggah, Hasil Validasi, Telaah dan Otorisasi, Laporan dan Jejak Audit."""
import json
import pandas as pd
import streamlit as st
import engine, samples, security

st.set_page_config(page_title="Capex & Procurement Integrity Bot", layout="wide")

# ---------- state
ss = st.session_state
ss.setdefault("log", security.AuditLog())
ss.setdefault("txs", [])      # daftar transaksi dan hasil validasinya
ss.setdefault("erp", [])      # antrean ERP: hanya transaksi yang telah diotorisasi manusia
log, txs = ss.log, ss.txs

def rp(x): return "Rp{:,.0f}".format(x).replace(",", ".") if x is not None else "-"

# ---------- sidebar: peran pengguna (RBAC)
st.sidebar.title("Integrity Bot")
role = st.sidebar.selectbox("Masuk sebagai peran", security.ROLES, index=security.ROLES.index("Hutang Usaha"))
st.sidebar.caption("Hak akses mengikuti matriks pemisahan tugas (Tabel 5.2). Bot hanya mengusulkan; otorisasi tetap oleh Manajer Keuangan.")
st.sidebar.info("Data perusahaan (PT Nusa Karya Pertambangan) dan hasil ekstraksi OCR/LLM pada prototipe ini adalah SIMULASI.")

def deny(action, entitas):
    log.add(role, "AKSES_DITOLAK", entitas, "aksi %s tidak diizinkan untuk peran %s" % (action, role))
    st.error("Akses ditolak: peran %s tidak berwenang untuk aksi ini. Kejadian dicatat di log audit." % role)

def pick(label, key):
    if not txs:
        st.info("Belum ada transaksi. Unggah dokumen pada tab pertama."); return None
    ids = [t["id"] for t in txs]
    return next(t for t in txs if t["id"] == st.selectbox(label, ids, key=key))

st.title("Capex & Procurement Integrity Bot")
tab1, tab2, tab3, tab4 = st.tabs(["1. Unggah Dokumen", "2. Hasil Validasi", "3. Telaah dan Otorisasi", "4. Laporan dan Jejak Audit"])

# ---------- layar 1: unggah
with tab1:
    st.subheader("Unggah dokumen PO, receiving report, dan invoice")
    st.caption("Pada prototipe, hasil OCR dan LLM disimulasikan. Pilih skenario uji (Tabel 6.1) atau unggah berkas JSON hasil ekstraksi dengan skema yang sama.")
    c1, c2 = st.columns(2)
    sk = c1.selectbox("Skenario sampel", list(samples.SKENARIO))
    up = c2.file_uploader("atau berkas JSON hasil ekstraksi", type=["json"])
    if st.button("Proses transaksi", type="primary"):
        if not security.can(role, "upload_invoice"):
            deny("upload_invoice", "transaksi")
        else:
            try:
                tx = json.load(up) if up else samples.SKENARIO[sk]()
                res = engine.validate(tx)
                tid = "TX-%03d" % (len(txs) + 1)
                txs.append({"id": tid, "sumber": up.name if up else sk, "tx": tx, "res": res, "status": "Menunggu telaah", "catatan": ""})
                log.add(role, "UNGGAH_DOKUMEN", tid, "PO %s, INV %s" % (tx["po"]["no"], tx["inv"]["no"]))
                log.add("Bot", "EKSTRAKSI_DAN_VALIDASI", tid, "status %s, skor %.2f, tingkat %s" % (res["status_kecocokan"], res["skor_risiko"], res["tingkat"]))
                st.success("%s diproses: %s, skor risiko %.2f (%s). %s." % (tid, res["status_kecocokan"], res["skor_risiko"], res["tingkat"], res["routing"]))
            except Exception as e:
                st.error("Dokumen gagal dibaca (%s). Kembalikan ke pengunggah dengan pesan yang jelas." % e)
    if txs:
        st.dataframe(pd.DataFrame([{"ID": t["id"], "Sumber": t["sumber"], "Status kecocokan": t["res"]["status_kecocokan"],
                                    "Skor": t["res"]["skor_risiko"], "Tingkat": t["res"]["tingkat"], "Status proses": t["status"]} for t in txs]),
                     use_container_width=True, hide_index=True)

# ---------- layar 2: hasil validasi
with tab2:
    t = pick("Pilih transaksi", "pick2")
    if t:
        r, tx = t["res"], t["tx"]
        m = st.columns(4)
        m[0].metric("Status kecocokan", r["status_kecocokan"]); m[1].metric("Skor risiko", "%.2f" % r["skor_risiko"])
        m[2].metric("Tingkat risiko", r["tingkat"]); m[3].metric("Pembayaran", "Ditahan" if r["tahan_pembayaran"] else "Dapat diproses setelah otorisasi")
        st.write("**Routing:** " + r["routing"])
        if r["perlu_periksa_manusia"]: st.warning("Ada field berkeyakinan rendah: periksa dokumen asli secara manual.")
        if r["blokir_erp"]: st.error("Transaksi ini tidak dapat diteruskan ke ERP sebelum temuan diselesaikan.")
        d1, d2, d3 = st.columns(3)
        d1.markdown("**PO** " + tx["po"]["no"]); d1.write("%s | %s" % (tx["po"]["vendor"], tx["po"]["tanggal"]))
        d2.markdown("**Receiving report** " + (tx["rr"]["no"] if tx.get("rr") else "(tidak ada)")); d2.write(tx["rr"]["tanggal"] if tx.get("rr") else "-")
        d3.markdown("**Invoice** " + tx["inv"]["no"]); d3.write("%s | %s" % (tx["inv"]["tanggal"], rp(tx["inv"]["jumlah"])))
        st.markdown("**Pencocokan per item**")
        st.dataframe(pd.DataFrame([{"Item": x["item"], "Qty PO": x["qty_po"], "Qty diterima": x["qty_rr"], "Qty invoice": x["qty_inv"],
                                    "Harga PO": rp(x["harga_po"]), "Harga invoice": rp(x["harga_inv"]), "Dicocokkan melalui": x["metode_cocok"]} for x in r["detail_item"]]),
                     use_container_width=True, hide_index=True)
        st.markdown("**Temuan, alasan, dan rujukan dokumen**")
        if not r["temuan"]: st.success(r["alasan"])
        for f in r["temuan"]:
            st.write("- [%s] %s  \n  _Rujukan: %s_" % (f["kategori"], f["uraian"], f["rujukan"] or "-"))

# ---------- layar 3: telaah dan otorisasi
with tab3:
    t = pick("Pilih transaksi", "pick3")
    if t:
        r = t["res"]
        st.write("**%s** | %s | skor %.2f (%s) | status proses: **%s**" % (t["id"], r["status_kecocokan"], r["skor_risiko"], r["tingkat"], t["status"]))
        if r["tingkat"] == "Tinggi": st.error("Eskalasi: transaksi berisiko tinggi diteruskan ke Manajer Keuangan dan Audit Internal.")
        st.text_area("Alasan dan temuan bot", r["alasan"], height=120, disabled=True, key="alasan_" + t["id"])
        catatan = st.text_area("Catatan telaah / alasan keputusan", t["catatan"], key="cat_" + t["id"])
        b1, b2, b3 = st.columns(3)
        if b1.button("Telaah selesai (Hutang Usaha)", key="rev_" + t["id"]):
            if not security.can(role, "review"): deny("review", t["id"])
            else:
                t["status"], t["catatan"] = "Ditelaah", catatan; log.add(role, "TELAAH", t["id"], catatan); st.rerun()
        if b2.button("Otorisasi pembayaran (Manajer Keuangan)", key="aut_" + t["id"], disabled=r["blokir_erp"]):
            if not security.can(role, "authorize"): deny("authorize", t["id"])
            else:
                t["status"], t["catatan"] = "Diotorisasi", catatan
                log.add(role, "OTORISASI", t["id"], catatan or "-")
                ss.erp.append({"ID": t["id"], "PO": t["tx"]["po"]["no"], "Invoice": t["tx"]["inv"]["no"], "Nilai": t["tx"]["inv"]["jumlah"]})
                log.add("Bot", "PENERUSAN_ERP", t["id"], "proses 5.0: data tervalidasi diserahkan ke ERP"); st.rerun()
        if b3.button("Tolak / kembalikan", key="tol_" + t["id"]):
            if not (security.can(role, "authorize") or security.can(role, "review")): deny("review", t["id"])
            else:
                t["status"], t["catatan"] = "Ditolak", catatan; log.add(role, "TOLAK", t["id"], catatan or "-"); st.rerun()
        if r["blokir_erp"]: st.caption("Tombol otorisasi dinonaktifkan: temuan pemblokir (dokumen tanpa pasangan, invoice ganda, kapitalisasi di luar kebijakan, atau keyakinan rendah) harus diselesaikan lebih dahulu.")

# ---------- layar 4: laporan eksepsi dan jejak audit
with tab4:
    if security.can(role, "view_exceptions"):
        st.subheader("Laporan eksepsi")
        flagged = [t for t in txs if t["res"]["temuan"]]
        st.dataframe(pd.DataFrame([{"ID": t["id"], "Skenario/sumber": t["sumber"], "Skor": t["res"]["skor_risiko"], "Tingkat": t["res"]["tingkat"],
                                    "Jumlah temuan": len(t["res"]["temuan"]), "Status proses": t["status"]} for t in flagged]) if flagged else pd.DataFrame(columns=["ID"]),
                     use_container_width=True, hide_index=True)
        c = st.columns(3)
        c[0].metric("Transaksi masuk", len(txs)); c[1].metric("Divalidasi", len(txs)); c[2].metric("Diteruskan ke ERP", len(ss.erp))
        st.caption("Rekonsiliasi keluaran: jumlah masuk dibandingkan dengan jumlah divalidasi dan diteruskan ke ERP.")
    else:
        st.info("Laporan eksepsi hanya tersedia bagi Manajer Keuangan dan Audit Internal.")
    if security.can(role, "view_capitalization"):
        st.subheader("Antrean ERP (data yang telah diotorisasi)")
        st.dataframe(pd.DataFrame(ss.erp) if ss.erp else pd.DataFrame(columns=["ID", "PO", "Invoice", "Nilai"]), use_container_width=True, hide_index=True)
    if security.can(role, "view_audit"):
        st.subheader("Log audit berantai hash")
        st.success("Integritas rantai log: VALID") if log.verify() else st.error("Integritas rantai log: TERGANGGU")
        st.dataframe(pd.DataFrame(log.entries) if log.entries else pd.DataFrame(columns=["id_log"]), use_container_width=True, hide_index=True)
    else:
        st.info("Log audit hanya dapat dibuka oleh Audit Internal dan Manajer Keuangan.")
