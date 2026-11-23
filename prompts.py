"""Rancangan prompt (Bab VI subbab 6.2) dan kait opsional ke LLM sungguhan.
CATATAN: prototipe berjalan tanpa LLM (data ekstraksi disimulasikan di samples.py). Fungsi
extract_with_llm di bawah adalah kerangka integrasi dan BELUM diuji; perlu paket 'anthropic',
variabel lingkungan ANTHROPIC_API_KEY, dan CLAUDE_MODEL. Kirim hanya teks OCR yang sudah disamarkan (security.mask)."""
import json, os

SYSTEM_PROMPT = (
    "Anda adalah asisten validasi dokumen pengadaan. Tugas Anda mengekstraksi data dari PO, receiving report, "
    "dan invoice, lalu mencocokkannya. Gunakan hanya informasi dari dokumen dan konteks yang diberikan. "
    "Jika sebuah nilai tidak terdapat pada sumber, tulis null dan beri catatan. Untuk setiap ketidaksesuaian, "
    "sebutkan dokumen sumber dan lokasi temuan. Keluarkan hasil hanya dalam format JSON yang ditentukan."
)

OUTPUT_SCHEMA = {
    "jenis_dokumen": "PO | RR | INV", "no": "string", "po_no": "string|null", "vendor": "string", "tanggal": "YYYY-MM-DD",
    "items": [{"kode": "string|null", "deskripsi": "string", "serial": "string|null", "qty": "number", "harga": "number|null"}],
    "ppn": "number|null", "jumlah": "number|null",
    "confidence": {"<nama_field>": "0.00-1.00"}, "catatan": "string|null",
}

FEW_SHOT = [
    {"input": "PURCHASE ORDER No. PO-2026-00101 ... Excavator 20 ton Komatsu PC200-8 SN KMT-PC200-88421 qty 1 @ Rp2.450.000.000",
     "output": {"jenis_dokumen": "PO", "no": "PO-2026-00101", "vendor": "PT Alfa Heavy Indo", "tanggal": "2026-03-02",
                "items": [{"kode": None, "deskripsi": "Excavator 20 ton Komatsu PC200-8", "serial": "KMT-PC200-88421", "qty": 1, "harga": 2450000000}],
                "confidence": {"no": 0.98, "qty": 0.96, "harga": 0.95}, "catatan": None}},
]

def build_messages(ocr_text, rag_context):
    ctx = "\n".join("- %s" % c for c in rag_context)
    user = ("Konteks dari basis pengetahuan:\n%s\n\nSkema keluaran:\n%s\n\nContoh:\n%s\n\nDokumen yang diperiksa:\n%s"
            % (ctx, json.dumps(OUTPUT_SCHEMA, ensure_ascii=False), json.dumps(FEW_SHOT, ensure_ascii=False), ocr_text))
    return SYSTEM_PROMPT, [{"role": "user", "content": user}]

def extract_with_llm(ocr_text, rag_context):  # pragma: no cover - belum diuji
    import anthropic
    system, messages = build_messages(ocr_text, rag_context)
    client = anthropic.Anthropic()
    resp = client.messages.create(model=os.environ["CLAUDE_MODEL"], max_tokens=2000, system=system, messages=messages)
    return json.loads(resp.content[0].text)
