"""Kontrol akses berbasis peran (Tabel 5.2/5.3) dan log audit berantai hash (KF-09)."""
import hashlib, json
from datetime import datetime

ROLES = ["Unit Operasi", "Pengadaan", "Gudang", "Hutang Usaha", "Manajer Keuangan",
         "Akuntansi Aset Tetap", "Audit Internal", "Administrator Sistem"]

PERMISSIONS = {
    "upload_pr":      {"Unit Operasi"},
    "upload_po":      {"Pengadaan"},
    "upload_rr":      {"Gudang"},
    "upload_invoice": {"Hutang Usaha"},
    "manage_kb":      {"Administrator Sistem", "Pengadaan"},
    "review":         {"Hutang Usaha"},
    "authorize":      {"Manajer Keuangan"},          # bot TIDAK punya hak ini
    "view_exceptions":{"Manajer Keuangan", "Audit Internal"},
    "view_audit":     {"Audit Internal", "Manajer Keuangan"},
    "view_capitalization": {"Akuntansi Aset Tetap", "Manajer Keuangan"},
}

def can(role: str, action: str) -> bool:
    return role in PERMISSIONS.get(action, set())

class AuditLog:
    """Log append-only; setiap entri memuat hash entri sebelumnya sehingga perubahan terdeteksi."""
    def __init__(self):
        self.entries = []

    def add(self, user_role, aksi, entitas, detail="", ts=None):
        prev = self.entries[-1]["hash"] if self.entries else "0" * 64
        e = {"id_log": len(self.entries) + 1, "waktu": ts or datetime.now().isoformat(timespec="seconds"),
             "peran": user_role, "aksi": aksi, "entitas": entitas, "detail": detail, "hash_sebelumnya": prev}
        e["hash"] = hashlib.sha256(json.dumps(e, sort_keys=True).encode()).hexdigest()
        self.entries.append(e)
        return e

    def verify(self) -> bool:
        prev = "0" * 64
        for e in self.entries:
            body = {k: v for k, v in e.items() if k != "hash"}
            if body["hash_sebelumnya"] != prev: return False
            if hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest() != e["hash"]: return False
            prev = e["hash"]
        return True

def mask(value: str) -> str:
    """Penyamaran atribut sensitif (mis. rekening) sebelum data dikirim ke model (subbab 5.3)."""
    v = str(value)
    return v if len(v) <= 4 else "*" * (len(v) - 4) + v[-4:]
