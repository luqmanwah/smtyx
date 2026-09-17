# SMTYX — SMALL / MICROCOSMOS dan LARGE / PRIME

Runtime lokal versi **0.2.0**, mendukung **SMTYX-METADATA v1** dan **SMTYX-EXACT v2**.
Originator / initial designer: **@luqmanwah**. Lisensi implementasi: **Apache-2.0**.

Runtime menerima file dengan ekstensi apa pun, membaca **raw bytes**, menghitung
matriks/fingerprint, lalu menulis metadata `.smtyx`. Sumber dibuka read-only.
CLI tidak menerjemahkan teks, mengekstrak PDF, membuka Office, atau menjalankan target route.

| Mode | Isi | Penggunaan |
|---|---|---|
| SMALL / MICROCOSMOS | `[N,W]`, histogram 16 cluster, SHA-256, route opsional | Candidate lookup, known-object reference, vocab / macro-token |
| LARGE / PRIME | Seluruh SMALL + `MICRO → BLOCK → PAGE → DOC` dengan `[N,P0,P1,P2,P3]` per node | Metadata v1, atau rekonstruksi exact v2 dengan `--exact` |

**Dua format yang berbeda:** tanpa `--exact`, encoder menghasilkan metadata v1 yang
tidak dapat memulihkan raw file. Dengan `--exact`, encoder menghasilkan format v2
yang menyimpan urutan cluster dan discriminator pair berbasis bilangan basis-3.
`write` / `decode -o` dapat memulihkan raw bytes dari v2 tanpa sumber asli atau registry.
Exactness berasal dari informasi tambahan tersebut, bukan dari P0–P3 saja.
Paket exact tidak menjamin ukuran lebih kecil. Lihat `FORMAT_EXACT.md`.

## Mulai langsung

Prasyarat: Python **3.10+**. Tidak ada dependensi runtime pihak ketiga, API key,
model AI, atau koneksi internet yang diperlukan.

```powershell
Set-Location F:\SMITYX
python -m smtyx --help
python -m smtyx encode "C:\Data\dokumen.pdf" --exact
python -m smtyx inspect "C:\Data\dokumen.pdf.smtyx"
python -m smtyx write "C:\Data\dokumen.pdf.smtyx" -o "C:\Data\dokumen.pulih.pdf"
python -m smtyx verify "C:\Data\dokumen.pdf.smtyx" "C:\Data\dokumen.pdf"
```

Default output adalah nama sumber ditambah `.smtyx`. Folder tujuan harus sudah ada.
Raw output v2 dipublikasikan sesudah seluruh record, moments, checksum container,
dan SHA-256 raw bytes lolos; kegagalan tidak meninggalkan file final parsial.
Semua output baru menolak overwrite, termasuk ketika output sama dengan sumber,
symlink/hardlink yang sudah ada, registry lama, atau metadata hasil sebelumnya.
Gunakan nama output baru untuk percobaan ulang.

Instalasi CLI opsional ke environment pilihan Anda:

```powershell
python -m pip install -e .
smtyx --version
```

Perintah `python -m smtyx` tidak memerlukan instalasi tersebut dan cukup dijalankan
dari `F:\SMITYX`. Build paket memakai setuptools; instalasi dapat memerlukan
akses paket build jika belum tersedia.

## Contoh dari design-freeze asli

Fixture berasal dari attachment percakapan dan disalin byte-for-byte. Jalankan
dengan nama baru agar tidak menimpa contoh yang sudah disediakan:

```powershell
python -m smtyx encode tests\fixtures\SMTYX_Design_Freeze_Chat_2026-09-17.md -o examples\my-freeze.large.smtyx
python -m smtyx encode tests\fixtures\SMTYX_Design_Freeze_Chat_2026-09-17.md --mode small -o examples\my-freeze.small.smtyx
python -m smtyx inspect examples\my-freeze.large.smtyx
python -m smtyx inspect examples\my-freeze.large.smtyx --json
python -m smtyx decode examples\my-freeze.large.smtyx -o examples\my-freeze.metadata.json
python -m smtyx verify examples\my-freeze.large.smtyx tests\fixtures\SMTYX_Design_Freeze_Chat_2026-09-17.md
python -m unittest discover -s tests -v
```

Hasil fixture yang diuji:

```text
SMALL = [19794,236147]
LARGE root = [19794,1652792,16462431679,220036759485589,3302292262678241467]
MICRO=619, BLOCK=155, PAGE=5, DOC=1
SHA256=9fa2af4575cc33ea50218dd76ff5126868b0b9a59ed892fcdebd53f9545f5f45
```

Contoh pada bagian fixture ini tetap memakai metadata v1 untuk kompatibilitas.
Angka matriks pada JSON disimpan sebagai **string desimal** supaya P3 dan integer
lain tidak kehilangan presisi ketika melewati aplikasi yang menggunakan float64.
Inspect memvalidasi struktur; `verify` menghitung ulang isi dari sumber eksternal.

## Registry dan objek yang sudah dikenal

Snapshot registry membawa namespace dan revision. Satu ID hanya bermakna dalam
registry yang sama. Contoh membuat known-file route:

```powershell
python -m smtyx registry add --output examples\my-registry.v1.json --namespace local --kind FILE --index 37 --target "F:\SMITYX\tests\fixtures\SMTYX_Design_Freeze_Chat_2026-09-17.md"
python -m smtyx registry resolve examples\my-registry.v1.json FILE:37
python -m smtyx encode tests\fixtures\SMTYX_Design_Freeze_Chat_2026-09-17.md --mode small --registry examples\my-registry.v1.json --route FILE:37 -o examples\my-known-file.smtyx
python -m smtyx registry add --base examples\my-registry.v1.json --output examples\my-registry.v2.json --namespace local --kind VOCAB --index 21 --target RUN_PROGRAM
```

Jenis yang tersedia: `VOCAB`, `PATH`, `LINK`, `FILE`, `SOP`, `TOOL`, `MODEL`, `STATE`.
Macro-token dapat didaftarkan sebagai `VOCAB:418 → FIND_NPWP_EXACT` atau sebagai
SOP bernama. Registry ini menyimpan mapping yang diberikan pengguna; pembelajaran
alias, pemilihan model, eksekusi tool, dan pengambilan file dari route belum diterapkan.
`resolve` hanya mengembalikan deskripsi. Untuk FILE, SHA-256 saat pendaftaran
harus cocok dengan sumber ketika route dilekatkan ke `.smtyx`.

## Ukuran file dan penggunaan memori

Default: MICRO 32 byte, BLOCK 4 MICRO, PAGE 32 BLOCK (=4096 byte).
Chunk terakhir dapat pendek; file kosong memiliki DOC kosong tanpa child.
Tidak ada padding. Untuk input besar, tingkatkan ukuran MICRO:

```powershell
python -m smtyx encode "C:\Data\besar.bin" --micro-bytes 4096 -o "C:\Data\besar.v1.smtyx"
```

Untuk v1, `--micros-per-block`, `--blocks-per-page`, dan `--max-nodes` tersedia.
Default maksimum 100.000 node; input/output JSON dibatasi 64 MiB. Kapasitas PAGE
maksimum 16 MiB. SMALL membaca streaming 64 KiB tanpa hierarchy. LARGE menghitung
per MICRO, lalu menyimpan semua node metadata di memori. Batas adalah keputusan
implementasi, bukan batas matematis. Jika batas terlampaui, perintah gagal dengan
pesan jelas sebelum output final dibuat. File biasa harus dapat dibaca dan stabil;
direktori, pipe/device, atau file terkunci tidak dianggap input file yang didukung.

JSON hierarkis bisa lebih besar daripada sumber. Ukuran dua angka `[N,W]` tidak
sama dengan ukuran keseluruhan `.smtyx`; runtime ini belum merupakan codec kompresi.

V2 exact memakai record binary streaming: tidak menampung seluruh hierarchy di RAM
dan tidak terkena batas 100.000 node/64 MiB JSON. MICRO 1–1024 byte (default 32),
fanout BLOCK/PAGE 1–256, kapasitas PAGE maksimum 1 MiB. Reader exact membatasi
ukuran raw hasil ke 8 GiB secara default; `--max-output-bytes` dapat dinaikkan.
`--max-nodes` hanya berlaku pada v1. Setiap record v2 maksimum 64 KiB.

Uji ZIP pengguna: **6.508.349 byte → 12.042.392 byte exact `.smtyx` → 6.508.349 byte**.
Raw output identik byte-per-byte, SHA-256 sama, dan CRC ZIP lulus. File tersedia di
`F:\Smtyx Test\Output`; bukti lengkap ada di `log/exact-upgrade-20260917T1324392403069Z/`.
Discriminator menyimpan informasi lengkap yang hilang pada reducer; hasil ini tidak
membuktikan kompresi universal atau pemulihan dari fingerprint pendek saja.

## Dokumen dan layout workspace

- `SPEC.md`: rumus, cluster, mode, hierarchy, registry, dan batas matematis.
- `FORMAT.md`: kontrak JSON `.smtyx` / registry, validasi, versi, serta contoh.
- `FORMAT_EXACT.md`: record binary v2, discriminator, bukti inverse, dan exact CLI.
- `ARCHITECTURE.md`: komponen implementasi, aliran data, dan pemetaan design-freeze.
- `PROVENANCE.md`: sumber desain, fixture, keputusan profil, lisensi/atribusi.
- `tests/`: tes matematika, file, format, registry, dan CLI.
- `examples/`: hasil nyata fixture serta contoh registry.
- `log/`: receipt pengujian dan baseline sebelum upgrade; tidak diperlukan decoder.

Exit code CLI: **0** berhasil, **2** untuk argumen/input/validasi/I/O yang gagal.
Hasil sukses dikirim sebagai JSON ke stdout; error ringkas ke stderr.

## Tambahan fitur write

Perintah `write` menulis metadata tervalidasi ke lokasi output secara eksplisit:

```powershell
python -m smtyx write examples\design-freeze.large.smtyx --metadata -o "C:\Data\output.smtyx"
```

Tanpa `--metadata`, perintah memulihkan raw bytes untuk v2 exact; v1 metadata tetap
mengembalikan exit 2 `RAW_RECONSTRUCTION_UNAVAILABLE`. Export metadata v1 menerima
`.smtyx` / `.json`; export ringkasan v2 hanya `.json` karena ringkasan tersebut
tidak membawa record exact. Writer tidak membuka sumber asli atau mengambil raw
payload melalui route. Lihat `WRITE.md`.
