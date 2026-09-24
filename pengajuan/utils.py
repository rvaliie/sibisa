def mask_nik(nik: str) -> str:
    """Tampilkan NIK sebagian saja untuk daftar/ringkasan (privasi),
    NIK penuh hanya ditampilkan di halaman detail yang memang butuh
    verifikasi manual oleh validator."""
    if not nik or len(nik) < 10:
        return "*" * len(nik or "")
    return f"{nik[:6]}{'*' * 6}{nik[-4:]}"
