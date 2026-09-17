# SMTYX Technical Specification — raw-byte metadata profile v1

Spesifikasi berikut adalah kontrak metadata v1 yang dipertahankan. Runtime 0.2.0
menambahkan profil exact v2 pada `FORMAT_EXACT.md`: masks cluster berurutan dan
discriminator pair basis-3. Rumus SMALL, moments, dan hierarchy di bawah tetap sama.
Pernyataan keterbatasan rekonstruksi v1 tidak berlaku pada record exact lengkap v2;
P0–P3 saja tetap tidak merupakan lossless universal.

Status: implementasi terbatas versi 0.1.0 berdasarkan working design-freeze
17 September 2026 dan addendum percakapan SMALL/LARGE. Originator: **@luqmanwah**.
Istilah MUST / wajib pada dokumen ini berlaku untuk profil implementasi ini,
bukan pengesahan semua eksperimen dalam design-freeze.

## 1. Tujuan dan unit data

Sumber adalah sequence raw byte `X=[x1,...,xN]`, `xi ∈ {0,...,255}`.
N selalu **jumlah byte**, bukan jumlah glyph, karakter Unicode, kata, atau token model.
Ekstensi/nama file tidak menentukan algoritme. BOM, CRLF, NUL, byte UTF-8 multibyte,
invalid UTF-8, dan byte terkompresi dipertahankan sebagai input numerik apa adanya.
Tidak ada normalisasi Unicode/newline dan tidak ada parsing isi sumber.

Profil sumber lama berbasis Unicode/code-point di `smtyx-prime/` tetap merupakan
materi terpisah. Profil ini tidak mengubah definisinya dan tidak menafsirkan byte
sebagai code-point dari kamus tersebut.

## 2. Dua mode

### SMALL / MICROCOSMOS

SMALL menyediakan fingerprint `[N,W]`, histogram cluster, dan route opsional.
Ia mendukung candidate lookup atau penggunaan mapping objek/pola yang sudah dikenal.
`[N,W]` tidak mengidentifikasi objek secara unik. Hash SHA-256 dalam metadata membantu
memverifikasi kandidat yang benar ketika raw bytes tersedia.

Mode SMALL juga boleh menghasilkan fingerprint tanpa registry. Dalam keadaan itu,
hasil tidak mengklaim bahwa objek sudah dikenal atau bisa diambil kembali.
Sebuah macro-token adalah ID registry yang kedua pihak pahami; kesamaan fingerprint
tidak otomatis membentuk makna atau macro-token.

### LARGE / PRIME

LARGE membangun struktur `MICRO → BLOCK → PAGE → DOC` dengan math state pada
setiap node. `DOC` adalah nama root CONTAINER pada format v1 ini.
Struktur tersebut menyediakan koordinat rentang byte dan constraints matematis
untuk arah representasi reconstructive/exact.

Implementasi saat ini menyimpan signature, offset, panjang, dan urutan child,
tanpa discriminator/payload yang cukup untuk merekonstruksi semua raw bytes.
Karena itu setiap output menyatakan metadata-only. Menambahkan hierarchy tidak
dengan sendirinya membuktikan keunikan solusi.

Konsep pemilihan mode: known + shared registry dapat menggunakan SMALL; unknown
atau eksplorasi struktur menggunakan LARGE. CLI memilih eksplisit melalui `--mode`,
default LARGE; tidak ada heuristic known-object lookup otomatis. Setelah objek
tersedia dalam penyimpanan bersama, pengguna dapat mendaftarkan FILE ID dan memakai
SMALL pada pemanggilan selanjutnya.

Nama mode ini berbeda sumbu dengan v1 adaptive / v2 urgent-exact dalam freeze,
dan berbeda pula dari ukuran big/small model AI. Format version 1 adalah versi
serialisasi metadata, bukan deklarasi telah lengkapnya SMTYX v1 adaptive.

## 3. Reducer cluster terbaru

Untuk satu byte, urutan pasangan dari **MSB ke LSB**:

```text
b7b6 | b5b4 | b3b2 | b1b0
  q0 |   q1 |   q2 |   q3
```

`qj = (byte >> (6 - 2*j)) & 3`, untuk `j=0..3`.
Reducer `r(q)=0` jika `q=0`, selain itu `r(q)=1`.
`state = 8*r(q0) + 4*r(q1) + 2*r(q2) + r(q3)`.
**ClusterIndex = state + 1**, sehingga nilai berada pada 1–16.

| Pair | Reduced |
|---|---:|
| 00 | 0 |
| 01 | 1 |
| 10 | 1 |
| 11 | 1 |

Semua input adalah byte penuh, sehingga format `2|2|2|1` untuk bitstream 7-bit
tidak digunakan. Bit packing untuk sinyal arbitrary-length adalah ekstensi mendatang.

| State | Index | State | Index |
|---|---:|---|---:|
| 0000 | 1 | 1000 | 9 |
| 0001 | 2 | 1001 | 10 |
| 0010 | 3 | 1010 | 11 |
| 0011 | 4 | 1011 | 12 |
| 0100 | 5 | 1100 | 13 |
| 0101 | 6 | 1101 | 14 |
| 0110 | 7 | 1110 | 15 |
| 0111 | 8 | 1111 | 16 |

Contoh `ayam` (empat byte ASCII):

```text
0x61 = 01|10|00|01 → 1101 → 14
0x79 = 01|11|10|01 → 1111 → 16
0x61 = 01|10|00|01 → 1101 → 14
0x6d = 01|10|11|01 → 1111 → 16
```

Maka `[N,W]=[4,60]`, `C14=2`, `C16=2`, cluster lain nol.

## 4. SMALL fingerprint dan histogram

`Ck = jumlah byte dengan ClusterIndex=k`, untuk `k=1..16`.

```text
N = sum(Ck)
W = sum(k*Ck) = sum(ClusterIndex(xi))
SMALL = [N,W]
N <= W <= 16*N, untuk N > 0
```

File kosong: `[0,0]`, seluruh histogram nol.
Histogram disimpan terurut C01 sampai C16, termasuk nilai nol. Runtime tidak
menyimpan seluruh sequence cluster; urutan byte global memang tidak termuat dalam
histogram. Pertukaran posisi byte tidak mengubah `[N,W]` atau histogram.

Setiap state dengan `t` bit aktif mempunyai `3^t` byte asal. Misalnya cluster 16
berasal dari 81 byte berbeda. `0x01`, `0x02`, `0x03` semua menjadi cluster 2.
Fingerprint tidak cryptographic dan tidak dapat dipakai sebagai otorisasi atau
bukti keaslian. SHA-256 juga merupakan digest verifikasi, bukan raw payload.

## 5. LARGE signature

Pada setiap rentang node, posisi **dimulai lagi dari 1**:

```text
N  = banyak byte pada node
P0 = sum(xi)
P1 = sum(i * xi)
P2 = sum(i^2 * xi)
P3 = sum(i^3 * xi)
signature = [N,P0,P1,P2,P3]
```

Nilai `xi` adalah byte asli, **bukan cluster index** dan bukan ID numerik child.
P0 adalah jumlah nilai byte, sehingga berbeda dari W yang menjumlahkan cluster index.
Contoh `hello`: `[5,532,1617,5983,24615]`.
Contoh `hello world`: `[11,1116,6736,52204,453382]`.

Node induk merangkum concatenation byte dari child, sesuai contoh hasil file dalam
percakapan. Child identity/order disimpan eksplisit melalui daftar child.
Ini merupakan keputusan profil implementasi; skema lain yang memperlakukan identity
child sebagai simbol matematika baru memerlukan profil dan kamus identity tersendiri.

### Agregasi tanpa membaca ulang

Jika signature child adalah `Qk`, dan `s` jumlah byte child sebelumnya:

```text
N_parent = sum(N_child)
P0_parent += Q0
P1_parent += Q1 + s*Q0
P2_parent += Q2 + 2*s*Q1 + s^2*Q0
P3_parent += Q3 + 3*s*Q2 + 3*s^2*Q1 + s^3*Q0
```

Rumus umum `Pk_parent += sum(binomial(k,j)*s^(k-j)*Qj, j=0..k)`.
Parent tidak sekadar menjumlahkan positional moments tanpa rebasing.
Semua operasi menggunakan integer exact tanpa modulo, float, rounding, atau overflow
fixed-width. P3 fixture melebihi batas integer exact float64 (`2^53-1`).

### Bukti bahwa moments terbatas dapat collision

Sequence `[10,10,10,10,10]` dan `[11,6,16,6,11]` berbeda, tetapi N dan P0–P3 sama.
Selisih `[1,-4,6,-4,1]` memiliki moments derajat 0–3 nol. Contoh ini ada pada tests.
Multiset/order/discriminator tambahan perlu diuji untuk keunikan; solver masa depan
harus melaporkan UNIQUE / AMBIGUOUS / UNSAT berdasarkan bukti, bukan menebak bahasa.

## 6. Hierarchy, koordinat, dan batas chunk

| Level | Default | Identitas |
|---|---|---|
| MICRO | 32 byte | `MICRO:1`, `MICRO:2`, ... |
| BLOCK | 4 MICRO / maksimum 128 byte | `BLOCK:1`, ... |
| PAGE | 32 BLOCK / maksimum 4096 byte | `PAGE:1`, ... |
| DOC / CONTAINER | Seluruh PAGE | `DOC:1` |

ID satu-based bersifat lokal dalam satu `.smtyx`, bukan registry identity atau hash.
Offset nol-based absolut dalam file sumber. Rentang node adalah
`[offset, offset+N)`. Child disusun sesuai urutan sumber, contiguous, tanpa overlap.
Node parent dan child dapat memiliki N sama untuk file pendek; level tetap eksplisit.
Tidak ada semantic section detection atau penyesuaian chunk ke batas karakter.

Semua MICRO selain terakhir berukuran penuh. Prinsip yang sama berlaku bagi jumlah
child BLOCK/PAGE. Root kosong memiliki signature `[0,0,0,0,0]`, offset 0, children `[]`.
Tidak ada MICRO/BLOCK/PAGE kosong. Data nonempty selalu memakai empat level agar
koordinat dan validasi konsisten. `DOC` menampung satu file, bukan multi-file archive.

## 7. Route/index registry

| Code konseptual | Class | Contoh makna target |
|---:|---|---|
| 0 | VOCAB | Canonical action / macro-token `RUN_PROGRAM` |
| 1 | PATH | Path lokal |
| 2 | LINK | URL / resource link |
| 3 | FILE | Objek file yang tersedia di receiver |
| 4 | SOP | Nama dan versi prosedur |
| 5 | TOOL | Nama/descriptor tool |
| 6 | MODEL | Nama model / agent |
| 7 | STATE | Referensi snapshot state |

ID wire konseptual `3 bit class + 61 bit index` mengakomodasi delapan class.
Profil JSON memakai `CLASS:index`; belum ada binary 64-bit serializer.
Index 1 sampai `2^61-1`; nol dicadangkan. Alias OBJECT/AGENT boleh dibahas konseptual,
tetapi CLI v1 menerima class literal FILE/MODEL agar mapping tidak ambigu.

Namespace + revision + class + index menentukan lookup. Mapping bersifat immutable:
penambahan menghasilkan snapshot revision berikutnya pada file baru; route yang sudah
ada tidak dapat diganti. Konten/versi baru mendapat index baru.

FILE menyimpan SHA-256 saat didaftarkan. `encode --route FILE:n` menolak sumber
yang tidak cocok dengan digest entry. Untuk PATH/LINK/vocab/dll, route hanya metadata
referensi dan tidak membuktikan identitas raw file. `resolve` tidak membuka target,
menjalankan SOP/tool, menghubungi URL, atau mengembalikan payload. Target relatif
FILE saat pendaftaran diinterpretasi terhadap working directory; gunakan path absolut
untuk menghindari ambiguitas antar-mesin. Snapshot contoh lokal perlu disesuaikan saat dipindahkan.

Untuk pemulihan known object yang kelak diimplementasikan: resolve registry terpercaya,
ambil objek lengkap, verifikasi SHA-256 dan ukuran, lalu kembalikan objek. Fingerprint
cluster dipakai sebagai penyaring awal. Distribusi registry dan authenticity/signature
cryptographic registry belum termasuk profil ini.

## 8. Rekonstruksi dan fase berikutnya

LARGE menyediakan bagian matematis/struktur yang dapat dikembangkan dengan
coordinate multiset, discriminator pair T0/T1/T2, informasi order, shared base + delta,
atau constraints tambahan yang terbukti mencukupi. Tidak satu pun ditambahkan
secara diam-diam sebagai codec pengganti. Format mendatang harus menyatakan
reconstruction scheme, dependency/context, dan bukti round-trip secara eksplisit.

Koordinat nibble exact `byte=16*high+low` tetap sah; bila seluruh koordinat berurutan
disimpan maka raw bytes tersedia melalui representasi tersebut. Reducer OR cluster
menghilangkan informasi sehingga tidak memenuhi kondisi yang sama.

Base-100, family/residue simbol, Morse, RGB, semantic tokenizer, behavioral weight,
dan model adapters adalah bagian arah arsitektur. Format metadata ini tidak menerapkan
kompresi angka, media transport, enkripsi, pembelajaran, atau eksekusi agent.

## 9. Kriteria penerimaan

1. Semua 256 nilai byte cocok dengan aturan pair reducer.
2. SMALL memenuhi jumlah histogram dan weighted sum.
3. Setiap signature node sama dengan perhitungan langsung rentang raw byte.
4. Output `.smtyx` dapat diload, divalidasi, diinspect, dan didecode menjadi metadata.
5. Encode / inspect / decode tidak mengubah sumber.
6. Verify mendeteksi sumber berubah walaupun fingerprint SMALL collision.
7. Struktur/versi/precision/route tidak valid ditolak dengan error.
8. Fixture asli menghasilkan nilai dan jumlah node sesuai percakapan.
