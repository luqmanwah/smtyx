# SMTYX-EXACT v2 — cluster masks + discriminator basis-3

Implementasi: **0.2.0**. Originator desain SMTYX: **@luqmanwah**. Apache-2.0.
Profil engineering baru: **cluster-ternary-msb-v1**. Profil ini memperluas SMALL/LARGE
dan gagasan pair discriminator pada percakapan; bukan klaim bahwa layout binary
berikut sudah ditetapkan pada freeze awal.

## 1. Mengapa format baru diperlukan

V1 mereduksi `00→0` dan `01/10/11→1`, lalu menyimpan signature/histogram. Informasi
pilihan pair dan urutan cluster per byte tidak lengkap. Writer tidak dapat menciptakan
kembali informasi tersebut. V2 menyimpan **mask cluster berurutan** dan **discriminator
pair** di setiap MICRO. N/W, histogram, P0–P3 dan hierarchy tetap dihitung seperti v1.

V2 tidak memuat ZIP/raw source sebagai attachment, base64, atau fallback copy path.
Tidak ada ZIP/zlib/LZMA/dedup codec tersembunyi. Seluruh raw bytes ditransformasikan
ke masks + rank dan dikembalikan melalui inverse matematika. Transformasi tetap
mempertahankan informasi lengkap; tidak ada janji bahwa informasi baru dapat
diringkas menjadi dua/lima angka kecil secara lossless.

Paket v1 yang sudah kehilangan informasi tidak dapat dinaikkan menjadi exact hanya
dengan mengganti header. Sumber asli harus di-encode ulang menggunakan `--exact`.

## 2. Transformasi per MICRO

Untuk setiap byte, ambil pair MSB ke LSB `q0,q1,q2,q3`, masing-masing 0–3.
Simpan `mask = 8*[q0>0] + 4*[q1>0] + 2*[q2>0] + [q3>0]`.
Cluster index tetap `mask+1` dalam SMALL; penyimpanan mask memakai 0–15.

Untuk pair aktif, definisikan discriminator:

| Pair | Mask bit | Trit |
|---|---:|---:|
| 00 | 0 | Tidak ada |
| 01 | 1 | 0 |
| 10 | 1 | 1 |
| 11 | 1 | 2 |

Urutan trit mengikuti urutan byte lalu urutan pair MSB ke LSB. Jika jumlah trit
aktif T dan tritnya `d0,...,d(T-1)`, definisikan:

```text
R = sum(dj * 3^(T-1-j))
0 <= R < 3^T
T = sum(popcount(mask_i))
```

Simpan R sebagai integer unsigned big-endian dengan lebar tetap
`ceil(bit_length(3^T - 1)/8)` byte. T=0 memakai panjang rank nol. Leading zero pada
rank diizinkan/wajib sampai lebar tetap terpenuhi; jumlah leading zero trit dipulihkan
dari T, sehingga byte pair 01 tidak hilang.

Mask disimpan dua per byte: mask byte pertama pada nibble tinggi, berikutnya pada
nibble rendah. Bila N MICRO ganjil, nibble rendah terakhir wajib nol sebagai padding.

Contoh raw bytes `[0x01,0x02,0x03]`:

```text
masks = [1,1,1] → packed masks = 0x11 0x10
trits = [0,1,2]
R = 0*9 + 1*3 + 2 = 5 → rank byte = 0x05
```

MICRO juga membawa `[N,P0,P1,P2,P3]` atas byte aslinya. Signature ini memvalidasi
hasil inverse; ia tidak menggantikan masks atau discriminator.

## 3. Bukti inverse

Dari mask, decoder mengetahui tepat pair mana bernilai nol dan jumlah pair aktif T.
Representasi basis-3 dengan panjang T yang diketahui memberi satu urutan trit unik
untuk setiap `R ∈ [0,3^T)`. Pada pair aktif, `q=trit+1`; pada pair tidak aktif, q=0.
Menyusun empat pair pada posisi semula menghasilkan tepat satu byte asal.
Urutan mask dan hierarchy mempertahankan urutan seluruh byte. Karena setiap langkah
reversible pada domain yang didefinisikan, komposisinya reversible untuk setiap
file finite yang memenuhi batas format/runtime.

Implementasi memakai tabel inverse 16 state dengan `3^popcount(state)` kandidat,
diturunkan secara deterministik dari seluruh 256 byte. Tidak ada language guessing,
model, kamus file, jaringan, atau pencarian hash untuk menebak byte asal.

## 4. Framing container

Magic 12 byte:

```text
ASCII SMTYXEX2 + CR LF + 0x1A + LF
hex: 53 4D 54 59 58 45 58 32 0D 0A 1A 0A
```

Setiap record terdiri dari:

```text
tag:        1 byte ASCII
length:     uint32 little-endian, ukuran payload
payload:    tepat length byte
```

Length maksimum setiap record 65.536 byte. File tidak memiliki batas JSON 64 MiB
karena seluruh record diproses streaming. Tidak ada compression flag, extension
record tak dikenal, atau fallback interpretation pada v2.

Grammar:

```text
MAGIC
H
  untuk setiap PAGE:
    untuk setiap BLOCK:
      M ... M
      B
    P
D
F
END! + SHA256(container dari MAGIC sampai akhir payload F)
EOF
```

Indentasi grammar: B menutup setiap BLOCK; P menutup setiap PAGE. Hanya DOC tersedia
untuk sumber kosong. Jumlah dan urutan M/B/P diturunkan dari size header dan layout;
record hilang, tambahan, tertukar, serta trailing bytes ditolak.

## 5. Jenis record

| Tag | Payload |
|---|---|
| H | Header JSON UTF-8 |
| M | Signature MICRO + packed masks + rank |
| B | Signature BLOCK |
| P | Signature PAGE |
| D | Signature DOC |
| F | Footer JSON UTF-8 |

Signature binary adalah lima unsigned LEB128 canonical berurutan `[N,P0,P1,P2,P3]`.
Tujuh bit data per byte, bit tinggi menandakan continuation. Integer maksimum 64
byte varint / 448 bit; continuation berlebih dan overlong encoding ditolak.
Tidak ada signed integer, floating point, atau modulo. Nilai uint32 framing dan
rank memakai endianness yang berbeda secara eksplisit seperti di atas.

N record M wajib sama dengan panjang MICRO yang diharapkan. Setelah lima varint,
mask memakai `ceil(N/2)` byte. T dihitung dari masks, sehingga panjang rank dapat
ditentukan tanpa length terpisah. Payload tidak boleh memiliki sisa tambahan.
B/P/D hanya berisi lima varint, tanpa trailing payload.

ID node implisit urutan global setiap jenis: MICRO:1, BLOCK:1, PAGE:1, DOC:1.
Offset absolut dan edges dapat diturunkan dari layout/urutan record. Rumus parent
merebase moments berdasarkan jumlah byte child sebelumnya, sama dengan metadata v1.

### H — header

Header mempunyai fields tepat:

- `format`: `SMTYX-EXACT`; `version`: integer 2; `profile`: `cluster-ternary-msb-v1`.
- `mode`: `LARGE`.
- `layout`: micro_bytes, micros_per_block, blocks_per_page; integer positif.
- `source`: name (basename saja), size_bytes (canonical decimal string).
- `route`: null atau snapshot route v1 yang valid.
- `provenance`: originator `@luqmanwah`, design_reference dan freeze_date sama dengan
  v1; implementation `smtyx-python/0.2.0`.

MICRO 1–1024 byte; fanout masing-masing 1–256; kapasitas PAGE maksimum 1 MiB.
Default tetap 32/4/32. Source size nonnegative dan kurang dari 2^63 byte. Header
tidak menyimpan raw source path untuk retrieval. Reader membatasi raw output ke
8 GiB secara default, dapat disesuaikan `--max-output-bytes`.

### F — footer

Footer memuat fields tepat `sha256`, `small`, `node_counts`, `root_signature`.
SHA-256 dihitung atas raw byte asli / hasil inverse, lowercase hex.
SMALL memakai fingerprint dan histogram string decimal sama dengan v1.
Node counts JSON integers MICRO/BLOCK/PAGE/DOC. Root signature lima string decimal.
Reader menghitung ulang seluruh nilai dari inverse, lalu membandingkan secara exact.
FILE route digest harus cocok dengan reconstructed digest. Tidak ada lookup target.

Header/footer JSON menolak duplicate keys, NaN, Infinity, format/profile tidak dikenal.
Writer menghasilkan JSON ASCII escaped dengan keys sorted dan tanpa whitespace
tambahan. Pembaca membolehkan whitespace/urutan key lain, tetapi framing checksum
selalu meliputi byte serialized yang benar-benar tersimpan.

Trailer 36 byte adalah `END!` + raw SHA-256 digest 32 byte. Checksum ini mendeteksi
kerusakan storage/transfer, termasuk header/footer. Ia tidak mengautentikasi pengirim.
Sesudah trailer wajib EOF.

## 6. API/CLI dan publication

```powershell
python -m smtyx encode "input.zip" --exact -o "input.exact.smtyx"
python -m smtyx inspect "input.exact.smtyx"
python -m smtyx write "input.exact.smtyx" -o "output.zip"
python -m smtyx decode "input.exact.smtyx" -o "output-lain.zip"
python -m smtyx verify "input.exact.smtyx" "input.zip"
python -m smtyx write "input.exact.smtyx" --metadata -o "summary.json"
```

`--exact` wajib LARGE. Tanpa flag tersebut, perilaku encoder v1 tetap berlaku.
`--max-nodes` nondefault ditolak pada exact karena reader/writer exact streaming.
Inspect exact, termasuk `--json`, menghasilkan ringkasan sesudah memvalidasi seluruh
record; tidak memuat seluruh daftar node di RAM. Export ringkasan JSON bukan paket
exact. Decode exact mewajibkan `-o`; raw bytes tidak dicetak ke stdout.

Encoder dan decoder exact menulis temporary di folder output, memverifikasi
seluruh operasi, flush/fsync, lalu membuat target dengan hardlink create-only.
Temporary dihapus setelah publikasi atau error. Filesystem tujuan harus mendukung
hardlink (diuji pada workspace Windows ini); tidak ada fallback overwrite. Target
existing, symlink, dan hardlink existing ditolak. Proses dihentikan paksa dapat
meninggalkan `.smtyx-*.partial`, tetapi tidak menerbitkan file final yang belum lolos.
Jaminan ini tidak mencakup durability direktori setelah power loss.

Decoder v2 hanya memerlukan `.smtyx`. Tests memulihkan fixture temporary sesudah
raw sumber dan registry dihapus. Uji ZIP pengguna menggunakan Python audit hook yang
menolak Input/network/subprocess selama decoder; ini bukti kontrol pada jalur Python
yang diuji, bukan klaim sandbox OS universal.

## 7. Ukuran dan penerimaan

Mask berbiaya 4 bit per byte. Rank berbiaya sekitar `T*log2(3)` bit per MICRO,
ditambah rounding, signature dan framing. Karena itu exactness tidak menjamin
kompresi; data random/ZIP umumnya membesar dengan profil ini.

Uji aktual 17 September 2026:

```text
Input ZIP       = 6,508,349 bytes
Exact .smtyx    = 12,042,392 bytes (1.850299x input)
Recovered ZIP   = 6,508,349 bytes
SHA256 input/output = 9add165771a821863636cae0d5d12d4e4f1b99a527cda68a2f6651d7192f0514
Byte-for-byte   = PASS
ZIP CRC         = PASS (2 members; no extraction/execution)
SMALL           = [6508349,79745661]
Hierarchy       = 203386 MICRO / 50847 BLOCK / 1589 PAGE / 1 DOC
```

Baseline v1 dan paket lamanya tetap disimpan. Keberhasilan v2 tidak mengubah fakta
bahwa fingerprint/histogram/moments v1 saja tidak cukup untuk exact reconstruction.
