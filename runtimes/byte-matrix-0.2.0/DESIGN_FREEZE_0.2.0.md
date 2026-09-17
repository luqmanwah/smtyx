# SMTYX — design dan runtime freeze 0.2.0

**Status: DIKUNCI sebagai baseline oleh pengguna pada 17 September 2026.**
Workspace: `F:\SMITYX`. Originator / initial designer: **@luqmanwah**.
Lisensi implementasi: **Apache-2.0**.

Freeze mencakup desain implementasi dan runtime yang benar-benar berjalan saat ini,
bukan pengesahan semua aspirasi semantic/AI runtime pada percakapan awal.
Snapshot ada di `releases/0.2.0/`. Perubahan berikutnya harus memperoleh versi baru
dan tetap mempertahankan snapshot ini; tidak boleh diam-diam mengganti format 0.2.0.

## 1. Yang dikunci

| Komponen | Kontrak baseline |
|---|---|
| Input | Raw bytes file biasa, tanpa menafsirkan ekstensi/isi |
| Reducer | Byte → empat pair MSB ke LSB; 00→0, 01/10/11→1; index=state+1 |
| SMALL / MICROCOSMOS | `[N,W]`, histogram cluster 1–16, SHA-256, route opsional |
| LARGE / PRIME | MICRO → BLOCK → PAGE → DOC dengan `[N,P0,P1,P2,P3]` pada setiap node |
| Moments | `Pk=sum(i^k*xi)`; posisi mulai 1 di setiap node; parent memakai rebasing |
| Metadata v1 | UTF-8 JSON `SMTYX-METADATA`, profile `raw-byte-pair-or-msb-v1` |
| Exact v2 | Binary `SMTYX-EXACT`, profile `cluster-ternary-msb-v1` |
| Exactness | Urutan masks + rank basis-3 untuk discriminator pair, bukan moments saja |
| Registry | VOCAB/PATH/LINK/FILE/SOP/TOOL/MODEL/STATE, namespace + revision + index |
| Output | Create-only; raw v2 dipublikasikan setelah validasi lengkap |

Versi package runtime adalah **0.2.0**. Nomor format **v1** dan **v2** berbeda dari
versi package dan berbeda dari konsep adaptive-v1/urgent-v2 pada freeze percakapan.
Profil metadata v1 mempertahankan literal provenance writer 0.1.0 demi kompatibilitas
kontraknya; exact v2 menyatakan implementation 0.2.0. Ini bukan dua runtime aktif.

## 2. Kemampuan yang benar-benar dapat dijalankan

| Kemampuan | Command | Hasil / batas |
|---|---|---|
| Fingerprint ringan | `encode file --mode small` | N/W + histogram + digest; tidak membawa raw payload |
| Hierarchy metadata | `encode file` | V1 MICRO/BLOCK/PAGE/DOC; tidak dapat raw recovery |
| Encode exact | `encode file --exact` | V2 lengkap untuk raw reconstruction mandiri |
| Melihat representasi | `inspect file.smtyx` | Validasi dan ringkasan; v2 memeriksa semua record |
| Decode metadata | `decode metadata-v1.smtyx` | JSON, ke stdout atau `-o` |
| Memulihkan raw file | `write exact-v2.smtyx -o hasil` | Bytes inverse dari container; sumber/registry tidak dibaca |
| Alternatif raw decode | `decode exact-v2.smtyx -o hasil` | Sama dengan jalur raw writer v2 |
| Verifikasi | `verify file.smtyx sumber` | V1 metadata+hash; v2 inverse byte-per-byte+checksums |
| Export ringkasan | `write exact-v2.smtyx --metadata -o summary.json` | Ringkasan saja, tidak dapat digunakan untuk raw recovery |
| Daftar mapping | `registry add ...` | Snapshot immutable; FILE menyimpan hash sumber |
| Lookup mapping | `registry resolve registry.json CLASS:index` | Mengembalikan descriptor, tidak menjalankan target |

Ekstensi seperti PDF, ZIP, DOCX, JPG, MP4, EXE, dan file binary tanpa ekstensi dapat
diproses dengan algoritme raw-byte yang sama bila file biasa tersebut dapat dibaca
dan memenuhi batas resource. Ini tidak berarti isi masing-masing format sudah
dianalisis secara semantik. Bukti uji aktual mencakup ZIP, Markdown, dan fixture binary.

## 3. Alur pakai yang sudah berjalan

```powershell
Set-Location F:\SMITYX
python -m smtyx --version
python -m smtyx encode "C:\Data\input.bin" --exact -o "C:\Data\input.exact.smtyx"
python -m smtyx inspect "C:\Data\input.exact.smtyx"
python -m smtyx write "C:\Data\input.exact.smtyx" -o "C:\Data\hasil.bin"
python -m smtyx verify "C:\Data\input.exact.smtyx" "C:\Data\input.bin"
```

Path contoh harus diganti dengan input nyata; folder output harus sudah ada dan
nama output harus belum dipakai. Tanpa `--exact`, encoder tetap menghasilkan v1
metadata-only untuk kompatibilitas. File metadata v1 lama tidak bisa menjadi exact
secara otomatis; encoder perlu membaca raw sumber lagi untuk membuat v2 lengkap.

Prasyarat runtime: Python **3.10+**; diuji pada Windows/Python **3.13.15**.
Tidak membutuhkan internet, GPU, model AI, API key, atau dependency runtime pihak
ketiga. Instalasi wheel opsional; `python -m smtyx` dari workspace dapat langsung dipakai.
Build wheel memakai dependency build setuptools, terpisah dari kebutuhan runtime.

## 4. Bukti yang sudah ada

ZIP pengguna berhasil dipulihkan:

```text
Input  : F:\Smtyx Test\Input\SDCardFormatterv5_WinEN.zip
Output : F:\Smtyx Test\Output\SDCardFormatterv5_WinEN.zip
Bytes  : 6,508,349 (sama)
SHA256 : 9add165771a821863636cae0d5d12d4e4f1b99a527cda68a2f6651d7192f0514
```

- Kesamaan **byte-per-byte**, SHA-256, dan CRC ZIP lulus.
- Source tetap sama sebelum/sesudah pengujian.
- Decoder menerima paket `.smtyx`, dengan akses folder Input diblokir oleh audit
  hook Python; tidak ada percobaan akses terlarang. Ini bukan klaim sandbox OS universal.
- Tests juga menghapus sumber/registry temporary sebelum decode dan membuktikan
  pemulihan mandiri dari container.
- **44 tests** pada baseline, termasuk 256 nilai byte, collision, varints, malformed
  records, checksum/moment failures, source changes, publication race, dan CLI.
- Wheel 0.2.0 telah diinstal ke direktori terpisah dan memulihkan fixture Markdown
  19.794 byte dengan hash yang sama.

Bukti historis rinci: `log/exact-upgrade-20260917T1324392403069Z/`.
Receipt freeze ini disimpan pada `releases/0.2.0/` bersama hasil verifikasi saat freeze.

## 5. Batas yang harus tetap dinyatakan

**Lossless sudah berjalan; penghematan ukuran belum dijanjikan.** Pada uji ZIP,
container exact 12.042.392 byte atau 1,850299 kali input. Informasi lengkap disimpan
dalam masks/discriminator; N/W atau P0–P3 saja tidak cukup untuk memulihkan sumber.

V1 memiliki default batas 100.000 node dan 64 MiB JSON. V2 streaming:
MICRO 1–1024 byte, fanout 1–256, PAGE maksimum 1 MiB, record maksimum 64 KiB.
Default layout 32/4/32. Reader v2 membatasi raw hasil 8 GiB secara default, dapat
diubah lewat `--max-output-bytes`. Batas resource tidak merupakan hasil benchmark
atau jaminan produksi untuk seluruh ukuran/perangkat.

Raw output v2 menggunakan temporary + hardlink create-only sesudah validasi.
Filesystem tujuan harus mendukung hardlink; path existing ditolak. Proses dihentikan
paksa dapat meninggalkan temporary, tanpa menerbitkan raw final yang belum lolos.
Hash/checksum mendeteksi kerusakan; tidak mengautentikasi pengirim dan bukan enkripsi.

## 6. Belum menjadi fitur runtime

- Memahami isi dokumen, semantic search, semantic compression, atau memilih bagian
  PDF berdasarkan maksud pengguna.
- Tokenizer adaptif, belajar vocabulary/macro otomatis, GMN, behavioral weights.
- Memilih/menjalankan model AI, agent, tool, atau SOP berdasarkan route.
- Mengambil file otomatis melalui PATH/LINK/FILE registry, sinkronisasi remote.
- GUI, service/daemon, heartbeat, spectator, atau orkestrasi agent otomatis.
- Transport Morse/RGB/radio, enkripsi, digital signatures, dan physical controller.
- Folder/archive multi-file SMTYX, random-access selective decode, deduplication,
  atau jaminan file exact lebih kecil dari raw sumber.

Vocab/macro/SOP/tool/model saat ini adalah **mapping descriptor manual**. Registry
dapat menyimpan ID/name; keberadaan ID tidak berarti kemampuan tersebut dieksekusi.

## 7. Arti penguncian

Desain/kontrak dan file runtime baseline dibekukan sebagai snapshot dengan manifest
SHA-256. Snapshot, manifest, receipt, dan wheel dibuat read-only untuk mencegah
perubahan tidak sengaja. Read-only dan hash bukan perlindungan dari administrator
yang sengaja mengubah keduanya. Workspace aktif tetap dapat dipakai menjalankan CLI.

Pekerjaan setelah freeze adalah revisi versi baru atas permintaan pengguna, dengan
catatan perubahan dan tes sendiri. Baseline 0.2.0 dan bukti kegagalan/keberhasilan
sebelumnya tetap dipertahankan. Tidak ada remote state atau memory global yang ditulis.
