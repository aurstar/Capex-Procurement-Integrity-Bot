# Capex & Procurement Integrity Bot (prototipe)

Prototipe Bab VI laporan SIA: validasi tiga dokumen (PO, receiving report, invoice), analisis risiko,
telaah dan otorisasi manusia (human-in-the-loop), dan log audit berantai hash.

## Menjalankan
    pip install -r requirements.txt
    python test_engine.py        # 11 pengujian logika (skenario U-01 s.d. U-10)
    streamlit run app.py         # antarmuka 4 layar

## Struktur
| Berkas | Isi | Rujukan laporan |
|---|---|---|
| engine.py | pencocokan 3 dokumen, tanggal, invoice ganda, pola vendor, kapitalisasi, skor risiko | DFD 2.0 dan 3.0 |
| kb.py | basis pengetahuan simulasi (daftar harga, kebijakan, riwayat) | D3 |
| security.py | RBAC, log audit berantai hash, masking | Tabel 5.2, 5.3 |
| samples.py | data hasil ekstraksi simulasi untuk U-01 s.d. U-09 | Tabel 6.1 |
| prompts.py | system prompt, skema JSON, few-shot, kerangka pemanggilan LLM | subbab 6.2 |
| app.py | antarmuka Streamlit | subbab 6.3 |

## Batasan (jujur)
- OCR dan LLM **disimulasikan**: ekstraksi berasal dari samples.py. `prompts.extract_with_llm` hanya kerangka dan belum diuji.
- Kesetaraan makna deskripsi memakai kemiripan token sederhana, bukan model bahasa.
- Semua angka (harga, ambang, kebijakan) adalah asumsi proyek.
- Penyimpanan hanya di memori sesi (tanpa database); log hilang saat aplikasi ditutup.
- app.py sudah lolos uji asap dengan stub Streamlit, tetapi belum dijalankan di Streamlit sungguhan.

## Skenario dan hasil yang diharapkan
U-01 cocok/rendah | U-02 harga +5,3% tidak cocok/tinggi | U-03 kuantitas kurang 3 unit/menengah | U-04 invoice ganda/tinggi, ERP diblokir |
U-05 tanpa receiving report/tinggi, diblokir | U-06 RR mendahului PO/menengah | U-07 deskripsi berbeda tetap cocok |
U-08 keyakinan rendah/menengah, diblokir | U-09 umur manfaat 25 th di luar kebijakan, diblokir | U-10 uji akses: pilih peran selain Manajer Keuangan lalu coba otorisasi.
