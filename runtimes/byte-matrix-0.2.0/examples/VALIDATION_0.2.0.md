# SMTYX 0.2.0 — hasil penyempurnaan dan uji rekonstruksi exact

Tanggal pengujian: **17 September 2026**. Workspace: **F:\SMITYX**.
**Hasil tantangan input ZIP → `.smtyx` → ZIP baru: PASS.**

## Hasil pengguna

| Objek | Lokasi | Ukuran byte |
|---|---|---:|
| Sumber asli | `F:\Smtyx Test\Input\SDCardFormatterv5_WinEN.zip` | 6.508.349 |
| Paket exact | `F:\Smtyx Test\Output\SDCardFormatterv5_WinEN.zip.exact.smtyx` | 12.042.392 |
| ZIP hasil decoder | `F:\Smtyx Test\Output\SDCardFormatterv5_WinEN.zip` | 6.508.349 |

Raw output **identik byte-per-byte** dengan sumber. SHA-256 keduanya:

```text
9add165771a821863636cae0d5d12d4e4f1b99a527cda68a2f6651d7192f0514
```

SHA-256 paket exact:

```text
f98d02dc7b7232389b99ca04bb8fc3d96617b76d961113c6b4a303c757a42099
```

Pemeriksaan CRC ZIP lulus untuk **2 entries**, total uncompressed **7.230.264 byte**.
Isi archive tidak diekstrak atau dijalankan. Hash sumber sebelum/sesudah tetap sama.
File metadata hasil percobaan lama tetap disimpan dan tidak ditimpa.

## Bukti tidak memakai copy sumber

Decoder dijalankan sebagai subprocess terpisah, hanya menerima `.smtyx` dan path output.
Python audit hook aktif menolak akses ke `F:\Smtyx Test\Input`, jaringan, serta
subprocess/command execution dari decoder. Decode berhasil tanpa percobaan akses
terlarang. Daftar open events terdapat pada `decoder-audit.json`.

Selain uji aktual, unit tests menghapus raw sumber dan registry temporary sebelum
decode, kemudian memeriksa byte yang dipulihkan. Tidak ada raw ZIP/base64/lampiran
sumber di container, tidak ada lookup file, dan tidak ada fallback copy/paste.
Rekonstruksi memakai masks cluster dan rank discriminator per MICRO.
Audit hook adalah kontrol Python pada jalur yang diuji, bukan klaim sandbox OS universal.

## Perubahan yang memungkinkan exactness

V1 menyimpan signature metadata. V2 menambahkan informasi yang sebelumnya hilang:

1. Mask cluster 4-bit **berurutan** untuk setiap byte.
2. Trit `0/1/2` untuk membedakan pair aktif `01/10/11`.
3. Rank basis-3 per MICRO, dengan panjang diketahui dari masks.
4. Record MICRO/BLOCK/PAGE/DOC, moments, histogram, SHA-256 raw, dan checksum container.

Decoder mengembalikan pair melalui inverse deterministik, memvalidasi seluruh hasil,
lalu mempublikasikan raw output. Output temporary dibersihkan pada error; target
existing tidak ditimpa. P0–P3 dan `[N,W]` tetap bukan representasi lossless universal.

Paket v2 ini **1,850299 kali** ukuran ZIP sumber. Hasil membuktikan pemulihan lossless,
bukan penghematan ukuran. Tidak ada klaim file 6,5 MB dipulihkan hanya dari dua angka.

## Matematika dan performa aktual

```text
SMALL = [6508349,79745661]
Hierarchy = 203386 MICRO / 50847 BLOCK / 1589 PAGE / 1 DOC
Layout = 32 byte / 4 MICRO per BLOCK / 32 BLOCK per PAGE
DOC = [6508349,829389614,2693826625972485,
       11682834168271139112313,57017932760627187340552641561]
```

| Langkah | Exit | Durasi detik |
|---|---:|---:|
| Encode exact dari raw ZIP | 0 | 8,052 |
| Decode dengan Input diblokir | 0 | 7,670 |
| Verify byte-per-byte dari inverse terhadap sumber | 0 | 7,336 |

Durasi adalah pengamatan run ini, bukan jaminan benchmark lintas perangkat.
Jalur exact streaming tidak terkena batas 100.000 node metadata v1.

## Tests dan distribusi

**44 tests lulus** (27 baseline + 17 exact), run terakhir **5,436 detik** pada Python
3.13.15. Cakupan: seluruh 256 byte, discriminator, canonical varints, empty/partial
dan multi-page, fixture freeze asli, custom layout, metadata compatibility, source
tanpa registry, korupsi setiap level, footer/checksum, record order/length, output
limit, exclusive publication/race, source mutation, dan CLI.

Wheel `smtyx_runtime-0.2.0-py3-none-any.whl` berhasil dibangun dan diinstal ke direktori
uji terpisah tanpa instalasi global. Dari paket terinstal, encode exact dan write
berhasil memulihkan fixture design-freeze 19.794 byte dengan SHA-256 yang sama:
`9fa2af4575cc33ea50218dd76ff5126868b0b9a59ed892fcdebd53f9545f5f45`.

Wheel: **29.392 byte**, SHA-256:
`b0d2f991615bbd5f199013b439d1087fad134d25079d6dfba5d7cbf9238f5788`.

## Baseline dan receipt

Seluruh log upgrade berada di:

```text
F:\SMITYX\log\exact-upgrade-20260917T1324392403069Z
```

Isi penting:

- `baseline-0.1.0-with-write.zip`: snapshot **48 file** baseline sebelum perubahan;
  seluruh entry telah dicocokkan hash terhadap file workspace saat snapshot.
- `baseline-manifest.json`: ukuran dan SHA-256 per file baseline.
- `01-encode-exact.*`, `02-decode-input-blocked.*`, `03-verify-byte-exact.*`:
  perintah aktual, waktu, exit, stdout, stderr.
- `decoder-audit.json`: kontrol dan open events decoder.
- `challenge-report.json`: hasil machine-readable.
- `tests-0.2.0.log`: hasil lengkap 44 tests.

Lisensi Apache-2.0 dan atribusi @luqmanwah dipertahankan. Profil binary baru
dijelaskan secara terbuka pada `FORMAT_EXACT.md`. V1 lama tetap dapat diinspect
sebagai metadata, tetapi raw recovery membutuhkan encode ulang dari sumber ke v2.

## Command berikutnya

Gunakan nama output baru bila file sudah ada:

```powershell
Set-Location F:\SMITYX
python -m smtyx encode "C:\Data\file.bin" --exact -o "C:\Data\file.exact.smtyx"
python -m smtyx write "C:\Data\file.exact.smtyx" -o "C:\Data\file.pulih.bin"
python -m smtyx verify "C:\Data\file.exact.smtyx" "C:\Data\file.bin"
```
