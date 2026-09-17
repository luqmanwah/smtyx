# Contoh yang dihasilkan runtime

Tambahan runtime 0.2.0: `design-freeze.exact.smtyx` adalah paket exact v2;
`design-freeze.exact-summary.json` adalah ringkasannya. Perintah raw `write` pada
paket exact memulihkan fixture tanpa sumber asli. Contoh berikut tetap v1 metadata.

- `design-freeze.large.smtyx`: SMALL fingerprint dan hierarchy lengkap attachment.
- `design-freeze.small.smtyx`: SMALL fingerprint + histogram tanpa hierarchy.
- `design-freeze.metadata.json`: hasil decode metadata LARGE.
- `design-freeze.known.smtyx`: SMALL dengan snapshot route FILE:37.
- `registry.v1.json`: namespace local, FILE:37 terikat SHA-256 fixture.
- `registry.v2.json`: snapshot v1 ditambah VOCAB:21 → RUN_PROGRAM.
- `VALIDATION.md`: bukti uji, ukuran, hash, dan batas implementasi.

Registry FILE contoh menggunakan path workspace lokal F:\SMITYX. Bila menyalin
contoh ke komputer lain, daftarkan target lokal baru pada snapshot baru.
`resolve` hanya menampilkan entry; tidak mengambil file atau menjalankan target.

Untuk mengulang proses, gunakan nama baru seperti perintah `my-*` pada README root.
