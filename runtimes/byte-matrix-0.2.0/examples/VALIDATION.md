# Hasil verifikasi SMTYX 0.1.0

Tanggal: **17 September 2026**. Lingkungan: Windows, Python **3.13.15**.
Workspace implementasi: **F:\SMITYX**.

## Status penerimaan

**PASS — runtime metadata, dokumentasi, registry, dan tests selesai untuk scope ini.**

`python -m unittest discover -s tests -v` menjalankan **20 tests**, seluruhnya lulus
(run terakhir 3,366 detik). Pengujian mencakup 256 kemungkinan byte, golden vectors,
moment rebasing, collision matematis, empty/partial/multi-page input, custom layout,
invalid UTF-8, source mutation detection, create-only output termasuk hardlink,
precision, malformed/tampered metadata, bounds, delapan class registry, stale FILE
entry, deterministic serialization, dokumentasi JSON, dan CLI end-to-end.

## Fixture primer dan perlindungan sumber

Attachment asli percakapan berhasil diakses, sehingga fixture sintetis tidak dipakai.
Nama: `SMTYX_Design_Freeze_Chat_2026-09-17.md`.
Panjang raw bytes: **19.794**.

SHA-256 sumber sebelum pekerjaan, sumber asli sesudah pengujian, dan salinan fixture
sesudah pengujian sama:

```text
9fa2af4575cc33ea50218dd76ff5126868b0b9a59ed892fcdebd53f9545f5f45
```

Materi lama dalam `smtyx-prime/` tidak diedit; runtime ditempatkan terpisah di root.
Attribution **@luqmanwah**, NOTICE, dan lisensi **Apache-2.0** disertakan.

## Hasil perhitungan aktual

```text
SMALL [N,W] = [19794,236147]

C01=0      C02=0      C03=0      C04=1495
C05=2100   C06=503    C07=292    C08=1308
C09=69     C10=416    C11=278    C12=1140
C13=1035   C14=3377   C15=2607   C16=5174

DOC signature =
[19794,1652792,16462431679,220036759485589,3302292262678241467]

MICRO=619, BLOCK=155, PAGE=5, DOC=1
Total nodes=780
Default layout=32 bytes / 4 MICRO per BLOCK / 32 BLOCK per PAGE
```

Semua angka tersebut cocok dengan perhitungan yang dilaporkan dalam percakapan.
Tes juga membandingkan setiap node terhadap formula langsung rentang raw byte.

## File contoh yang tersedia

| File | Byte | Hasil |
|---|---:|---|
| `design-freeze.small.smtyx` | 923 | SMALL tanpa route |
| `design-freeze.large.smtyx` | 213472 | SMALL + hierarchy lengkap |
| `design-freeze.metadata.json` | 213472 | Decode metadata LARGE |
| `design-freeze.known.smtyx` | 1204 | SMALL + FILE:37 snapshot |
| `registry.v1.json` | 347 | FILE:37, namespace local |
| `registry.v2.json` | 469 | Snapshot v1 + VOCAB:21 |

Ukuran `.smtyx` adalah ukuran seluruh JSON. SMALL tidak mengandung raw payload;
pengurangan ukuran tidak membuktikan lossless compression. LARGE JSON lebih besar
daripada sumber karena menyimpan metadata tiap node secara readable.

`verify` terhadap LARGE, SMALL, dan SMALL+route menghasilkan `verified:true`.
`inspect` fixture LARGE berhasil. Hasil decode JSON identik byte-for-byte dengan
file LARGE pada writer ini, dengan SHA-256 kedua file:

```text
116ccc34767a5175ec2e4f12ceba6f98f11e79a2b82b2741ae1286616b0a2a4b
```

## Build dan instalasi terpisah

Wheel `smtyx_runtime-0.1.0-py3-none-any.whl` berhasil dibangun dengan build isolation.
Percobaan awal tanpa build isolation mendapati setuptools belum tersedia pada Python
host; build isolation menyediakan dependency build di environment sementara.
Runtime tetap tidak membutuhkan dependency pihak ketiga.

Wheel diinstal ke direktori pengujian terpisah, tanpa instalasi global. Import runtime
dari direktori instalasi tersebut kemudian memverifikasi contoh LARGE terhadap fixture
dan menghasilkan `verified:true`. Ukuran wheel: **21.908 byte**.

SHA-256 wheel:

```text
0e63a5f48b40c24d21df706c68fb1834253cabb1d601c648dce10864dd4761fa
```

## Batas hasil yang telah dibuktikan

Decode saat ini mengembalikan **metadata**. Raw reconstruction, universal lossless
compression, automatic shared-file retrieval, semantic tokenizer, model routing,
SOP/tool execution, transport binary/Morse/RGB, dan neural learning belum diterapkan.
P0–P3 tetap signature/constraints; test collision menegaskan batas tersebut.
Structural validation bukan autentikasi pengirim metadata atau bukti keunikan solver.

Untuk mulai menggunakan CLI, dari `F:\SMITYX`:

```powershell
python -m smtyx encode "C:\Data\input.bin" -o "C:\Data\input.smtyx"
python -m smtyx inspect "C:\Data\input.smtyx"
python -m smtyx decode "C:\Data\input.smtyx" -o "C:\Data\metadata.json"
python -m smtyx verify "C:\Data\input.smtyx" "C:\Data\input.bin"
```
