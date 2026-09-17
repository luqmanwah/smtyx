# Write — metadata v1 dan raw reconstruction v2

## Pembaruan setelah izin perluasan

Pengguna mengizinkan perluasan encoder, format, dan decoder, dengan baseline lama
dipertahankan. Runtime 0.2.0 kini menyediakan:

```powershell
python -m smtyx encode "input.zip" --exact -o "input.exact.smtyx"
python -m smtyx write "input.exact.smtyx" -o "hasil.zip"
python -m smtyx decode "input.exact.smtyx" -o "hasil-lain.zip"
python -m smtyx verify "input.exact.smtyx" "input.zip"
```

Writer v2 memulihkan data dari masks/discriminator di `.smtyx`, memeriksa seluruh
moments dan checksum, kemudian mempublikasikan output. Sumber/registry asli tidak
dibaca untuk merekonstruksi byte. Target existing ditolak; output parsial tidak
dipublikasikan jika validasi gagal. Tidak ada fallback copy sumber.

`write --metadata` pada v2 menghasilkan ringkasan `.json` saja; ringkasan ini tidak
merupakan paket exact dan tidak dapat dipakai sebagai pengganti input `.smtyx`.
Lihat `FORMAT_EXACT.md`. Bagian berikut menjelaskan perilaku **v1 metadata-only**
yang tetap dipertahankan; file v1 lama tidak mendapatkan discriminator secara otomatis.

Fitur ini ditambahkan setelah uji ZIP pengguna pada 17 September 2026.
Perubahan hanya meliputi modul writer, CLI dispatch, tests writer, dan dokumentasi.
Encoder, cluster reduction, signature, hierarchy, registry, serta format payload
tetap sama. Baseline sebelum perubahan dan log pengujian berada di `log/`.

## Penggunaan

```powershell
python -m smtyx write "input.smtyx" --metadata -o "output.smtyx"
python -m smtyx write "input.smtyx" --metadata -o "metadata.json"
```

Writer membaca dokumen `.smtyx`, menjalankan validator yang sudah ada, dan menulis
hasil serialisasi ke file baru secara exclusive. Output harus `.smtyx` atau `.json`
agar metadata tidak menyerupai file ZIP/PDF lain. Output existing tidak ditimpa.
Folder tujuan harus sudah tersedia. Hasil JSON melaporkan `output_kind:metadata`,
`raw_file_reconstructed:false`, dan `source_bytes_read:false`.

Penulisan metadata tersebut dapat bekerja saat sumber asli tidak tersedia; tests
menghapus sumber temporary sebelum pemanggilan writer untuk membuktikannya.
Tidak ada fallback membuka source.name, registry path, URL, shared file, atau
embedding source bytes. Tidak ada copy/paste input pengguna.

## Permintaan raw file

```powershell
python -m smtyx write "input.smtyx" -o "hasil.zip"
```

Perintah tersebut meminta rekonstruksi raw file. Pada SMTYX-METADATA v1, hasilnya
**exit 2: RAW_RECONSTRUCTION_UNAVAILABLE**, sebelum output dibuat.

Alasannya: `.smtyx` yang ada membawa `[N,W]`, histogram, `[N,P0,P1,P2,P3]`,
offset/child order, dan SHA-256. Format tidak membawa skema/discriminator/payload
yang mencukupi untuk raw reconstruction umum, dan tidak ada raw decoder di runtime.
Penambahan fungsi penulisan file saja tidak menyediakan byte yang hilang.

Karena itu keberhasilan `write --metadata` tidak boleh dilaporkan sebagai keberhasilan
meng-copy ZIP asli. Percobaan dengan paket v1 lama tetap gagal; percobaan baru dengan
paket v2 exact telah berhasil setelah encoder menyediakan discriminator yang lengkap.
