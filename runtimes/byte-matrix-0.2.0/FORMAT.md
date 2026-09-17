# Format `.smtyx` — SMTYX-METADATA v1

Dokumen ini tetap menetapkan format **metadata v1**, yang dipertahankan pada runtime
0.2.0 untuk kompatibilitas. Format binary exact v2 berada di `FORMAT_EXACT.md`.
Reader membedakan keduanya dari magic bytes; ekstensi `.smtyx` saja tidak cukup.

Format saat ini adalah satu dokumen **UTF-8 JSON**, tanpa BOM, dengan ekstensi
`.smtyx`. Nama format `SMTYX-METADATA` membedakannya dari codec/payload masa depan.
Tidak ada header binary, raw bytes, base64 sumber, cluster sequence, ataupun lampiran
file tersembunyi. Writer memakai indentation 2 spasi, ASCII escaping, dan LF akhir.
Reader tidak mensyaratkan whitespace/urutan key yang sama.

## 1. Aturan tipe dan presisi

- N, W, C01–C16, P0–P3, offset, size_bytes, dan index registry: string desimal
  canonical nonnegative, tanpa `+`, exponent, whitespace, atau nol depan kecuali `"0"`.
- Integer matematis maksimum 128 digit per field pada reader implementasi ini.
- Version, layout, revision: JSON integer. Boolean tidak diterima sebagai integer.
- Flags: JSON boolean literal. `null` hanya dipakai di lokasi yang didefinisikan.
- SHA-256: 64 digit hex lowercase. String tersebut adalah digest raw source.
- Semua key wajib hadir; unknown key ditolak pada profil v1 untuk mencegah silent downgrade.
- Duplicate key, NaN, Infinity, invalid UTF-8, version/profile tak dikenal ditolak.
- Maksimum dokumen JSON 64 MiB untuk baca/tulis; tidak ada ekstensi ZIP/gzip otomatis.

JavaScript boleh membaca dokumen dengan JSON.parse karena angka besar adalah string,
tetapi perhitungan harus memakai BigInt, bukan Number. Integer Python bersifat exact.
Nama source dan route target adalah string data, bukan perintah atau output path decoder.

## 2. Fields utama

| Field | Tipe | Ketentuan |
|---|---|---|
| format | string | `SMTYX-METADATA` |
| version | integer | `1` |
| profile | string | `raw-byte-pair-or-msb-v1` |
| mode | string | `SMALL` atau `LARGE` |
| source | object | `name`, `size_bytes`, `sha256` |
| small | object | `fingerprint`, `histogram` |
| large | object/null | hierarchy untuk LARGE; null untuk SMALL |
| route | object/null | snapshot reference entry; null jika tidak diberikan |
| reconstruction | object | `metadata_only=true`, `raw_decode_supported=false` |
| provenance | object | literal profil implementasi di contoh berikut |

`source.name` adalah basename sumber saat encode; tidak menentukan path pada decode.
Perintah verify membolehkan file identik dengan nama berbeda. SHA-256 tidak mengautentikasi
pengirim metadata: validasi terhadap sumber terpercaya tetap dibutuhkan.

Contoh literal lengkap untuk file kosong dengan hash SHA-256 standar:

```json
{
  "format": "SMTYX-METADATA",
  "version": 1,
  "profile": "raw-byte-pair-or-msb-v1",
  "mode": "SMALL",
  "source": {
    "name": "empty.bin",
    "size_bytes": "0",
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "small": {
    "fingerprint": ["0", "0"],
    "histogram": ["0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0", "0"]
  },
  "large": null,
  "route": null,
  "reconstruction": {
    "metadata_only": true,
    "raw_decode_supported": false
  },
  "provenance": {
    "originator": "@luqmanwah",
    "design_reference": "chatgpt:6a99b94e-9758-83ec-8246-c2290888ad53",
    "freeze_date": "2026-09-17",
    "implementation": "smtyx-python/0.1.0"
  }
}
```

Provenance saat ini merupakan literal profil runtime. Mengganti originator, reference,
tanggal, atau implementation memerlukan profil reader yang diperbarui; runtime 0.1.0
ini tidak menerima producer bebas. Provenance menyatakan atribusi desain, bukan tanda
tangan digital. Nomor package sebenarnya 0.1.0; version format tetap 1.

## 3. SMALL

`fingerprint` tepat dua elemen string `[N,W]`. `histogram` tepat 16 elemen
`[C01,C02,...,C16]`. Reader memeriksa:

```text
source.size_bytes == N == sum(histogram)
W == sum((index+1)*histogram[index])
```

Jika mode LARGE, fields SMALL tetap wajib dan dihitung dalam pembacaan sumber yang sama.
Signature root LARGE memiliki N yang sama. C01–C16 tidak disimpan per node pada v1.

## 4. LARGE hierarchy

```json
{
  "layout": {"micro_bytes": 32, "micros_per_block": 4, "blocks_per_page": 32},
  "root": "DOC:1",
  "nodes": [
    {"id": "MICRO:1", "kind": "MICRO", "offset": "0", "signature": ["5","532","1617","5983","24615"], "children": []},
    {"id": "BLOCK:1", "kind": "BLOCK", "offset": "0", "signature": ["5","532","1617","5983","24615"], "children": ["MICRO:1"]},
    {"id": "PAGE:1", "kind": "PAGE", "offset": "0", "signature": ["5","532","1617","5983","24615"], "children": ["BLOCK:1"]},
    {"id": "DOC:1", "kind": "DOC", "offset": "0", "signature": ["5","532","1617","5983","24615"], "children": ["PAGE:1"]}
  ]
}
```

Contoh object `large` di atas untuk `hello`, bukan seluruh `.smtyx`.
Urutan array node: seluruh MICRO, seluruh BLOCK, seluruh PAGE, DOC; dalam setiap
level, urutan naik mengikuti offset. ID unik, berurutan mulai 1, dengan prefix kind.
DOC selalu `DOC:1`. Offset absolut nol-based, posisi moments relatif satu-based.
Signature tepat lima string integer `[N,P0,P1,P2,P3]`.

Reader membangun kembali susunan parent yang diharapkan dari MICRO dan layout,
lalu membandingkan IDs, offsets, panjang, signatures, dan edges secara exact.
Dengan demikian gap, overlap, reordered children, duplicate node, unreachable node,
cycle, dangling reference, parent salah, dan root tambahan ditolak.

Semua moments harus nonnegative, nondecreasing untuk derajat meningkat, dan
`Pk <= 255*sum(i^k, i=1..N)`. Validasi ini memeriksa bounds serta konsistensi,
bukan bukti bahwa semua MICRO constraints mempunyai solusi atau hanya satu solusi.
Hubungan histogram dengan detail byte MICRO tidak dapat dibuktikan dari metadata
sendiri. Perintah verify menyelesaikannya melalui perhitungan ulang sumber eksternal.

Layout menerima integer 1–65536 per field; hasil perkalian ketiganya maksimum
16.777.216 byte. Default encode membatasi total 100.000 node (dapat dinaikkan).
Reader tetap dibatasi ukuran file JSON 64 MiB. Kedua batas berbeda dan didokumentasi
agar file metadata hasil writer dapat dibaca kembali oleh reader yang sama.

File kosong LARGE memakai layout biasa dan hanya node:

```json
{"id":"DOC:1","kind":"DOC","offset":"0","signature":["0","0","0","0","0"],"children":[]}
```

## 5. Route snapshot pada `.smtyx`

```json
{
  "namespace": "local",
  "revision": 1,
  "entry": {"class": "VOCAB", "index": "21", "target": "RUN_PROGRAM", "sha256": null}
}
```

Snapshot ini memungkinkan inspect tanpa registry eksternal dan merekam mapping saat
encode. Ia bukan salinan seluruh registry. FILE entry wajib membawa digest SHA-256
yang sama dengan `source.sha256`; class lain memiliki `sha256:null`.
Tidak ada field yang memerintahkan decoder mengeksekusi target.

Namespace mengikuti `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. Revision integer
1–2.147.483.647; index string decimal canonical 1–2^61-1. Target string nonempty.

## 6. Format registry pendamping

```json
{
  "format": "SMTYX-REGISTRY",
  "version": 1,
  "namespace": "local",
  "revision": 1,
  "entries": {
    "VOCAB:21": {"class": "VOCAB", "index": "21", "target": "RUN_PROGRAM", "sha256": null}
  }
}
```

Registry memakai UTF-8 JSON biasa (umumnya `.json`). `CLASS:index` harus sesuai
entry class/index; unknown class, key duplicate, dan index tak valid ditolak.
`registry add --base lama --output baru` mempertahankan seluruh entries lama,
menambah satu entry, dan menaikkan revision. Namespace harus cocok dengan base.
Tidak ada overwrite ataupun penggantian ID. Pengguna mengelola file snapshot dan
distribusinya; tidak ada database/daemon global atau remote write.

## 7. CLI dan arti decode

- `encode`: membuka sumber `rb`, membentuk dan memvalidasi document, lalu membuat
  output baru secara exclusive. Sumber tidak diinterpretasi atau ditulis ulang.
- `inspect`: membaca `.smtyx`, memvalidasi struktur, mengembalikan ringkasan.
  `--json` mengembalikan seluruh metadata.
- `decode`: membaca dan memvalidasi `.smtyx`, mengembalikan document JSON yang sama
  secara semantik, melalui stdout atau `-o metadata.json`.
- `verify`: membaca sumber eksternal, membandingkan size, SHA-256, SMALL dan semua
  LARGE nodes. Sukses mengembalikan `verified:true` dengan scope yang eksplisit.
- `registry resolve`: lookup snapshot, mengembalikan reference entry saja.
- `write --metadata`: menulis metadata tervalidasi ke file baru `.smtyx` atau `.json`.
  Hasil sukses menyatakan `output_kind:metadata` dan `raw_file_reconstructed:false`.
  `write` tanpa flag meminta raw file dan ditolak dengan exit 2
  `RAW_RECONSTRUCTION_UNAVAILABLE` untuk profil ini; tidak membuat output.

Decode tidak menciptakan raw source, membuka path dari metadata, atau menggunakan
ekstensi/nama sumber sebagai instruksi. Penulisan metadata baru bersifat create-only.
JSON disiapkan sepenuhnya sebelum output dibuka; write error membersihkan output
parsial yang dibuat proses ini. Proses yang dihentikan paksa saat write masih dapat
meninggalkan file parsial; inspect akan menolaknya. Ini belum merupakan crash-atomic
transaction atau storage system dengan durability guarantee.

Source stat sebelum/sesudah baca (size, mtime_ns, inode) dibandingkan untuk mendeteksi
perubahan biasa selama pembacaan. Pemeriksaan ini tidak menyediakan snapshot lock
terhadap writer lain yang memulihkan metadata filesystem; untuk concurrent writer
gunakan salinan/snapshot stabil. SHA-256 merekam byte yang benar-benar dibaca.

## 8. Evolusi format

Perubahan rumus, endianness cluster, signature child-identity, discriminator exact,
binary packing, multi-file container, atau compressed payload membutuhkan versi/profile
baru yang eksplisit. Reader tidak menebak atau fallback diam-diam. JSON v1 tidak
menjamin kompresi maupun interoperabilitas dengan file berakhiran `.smtyx` dari profil lain.
