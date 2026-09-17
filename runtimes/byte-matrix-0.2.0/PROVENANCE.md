# Provenance dan keputusan implementasi

## Perluasan exact 0.2.0

Pada 17 September 2026, setelah hasil uji v1 metadata tidak dapat merekonstruksi ZIP,
pengguna secara eksplisit mengizinkan perluasan encoder, format, dan decoder dengan
baseline lama dipertahankan. Snapshot 48 file baseline sebelum upgrade telah
diarsipkan dan dicocokkan SHA-256 per entry pada
`log/exact-upgrade-20260917T1324392403069Z/baseline-0.1.0-with-write.zip`.

Implementasi v2 mempertahankan reducer dan rumus v1, lalu menambahkan urutan masks
dan discriminator pair basis-3. Profil `cluster-ternary-msb-v1` serta layout record
binary merupakan keputusan engineering baru yang transparan di `FORMAT_EXACT.md`.
Ini mengikuti opsi discriminator yang dibahas pada percakapan; tidak diklaim sebagai
format binary yang sudah final pada attachment freeze.

Uji ZIP nyata menghasilkan byte identik, SHA-256 sama, dan CRC ZIP lulus. Akses ke
folder Input diblokir melalui Python audit hook selama decode. Bukti ada dalam
`challenge-report.json`, `decoder-audit.json`, dan log subprocess pada folder upgrade.
Sumber input tetap utuh. Paket exact lebih besar dari raw ZIP dan tidak diklaim
sebagai kompresi universal. Detail berikut menyimpan provenance baseline v1.

## Sumber primer

- Percakapan: **Jumlah Ekstensi Dunia**, ID
  `6a99b94e-9758-83ec-8246-c2290888ad53`.
- Attachment: `SMTYX_Design_Freeze_Chat_2026-09-17.md`, diambil melalui pembacaan
  percakapan pada 17 September 2026.
- Originator / initial designer dalam attachment: **@luqmanwah**.
- Status attachment: **Working canonical design / research freeze**; bukan
  production specification final.
- Lisensi implementasi yang direncanakan attachment: **Apache License 2.0**.
- Instruksi pengguna saat ini: implementasi raw-byte `.smtyx`, SMALL/LARGE,
  hierarchy, route registry, inspect/decode metadata, dokumentasi dan tests.

Attachment asli tersedia lokal pada saat implementasi dan disalin byte-for-byte ke
`tests/fixtures/`. SHA-256:
`9fa2af4575cc33ea50218dd76ff5126868b0b9a59ed892fcdebd53f9545f5f45`.
Panjang: **19.794 byte**. Tidak dipakai fixture pengganti.

## Urutan keputusan

1. Freeze menetapkan P0–P3 berbasis raw byte dan posisi mulai 1, serta
   MICRO/BLOCK/PAGE/CONTAINER. Freeze menyatakan batas universal lossless.
2. Addendum percakapan menetapkan reduksi setiap pair `00→0`, `01/10/11→1`,
   state 4-bit dan index +1. Contoh `ayam` menghasilkan `[4,60]`.
3. Percakapan menghitung attachment menjadi `[19794,236147]` serta hierarchy
   619 MICRO / 155 BLOCK / 5 PAGE / 1 DOC pada layout 32/4/32.
4. Percakapan membedakan SMALL/MICROCOSMOS (known object / route) dan
   LARGE/PRIME (hierarchical/reconstructive direction).
5. Scope pengguna saat ini meminta decode **metadata**. Runtime tidak menambahkan
   codec lossless alternatif ataupun mengeklaim raw reconstruction telah selesai.

## Keputusan engineering pada profil ini

Nama format `SMTYX-METADATA`, JSON UTF-8, canonical decimal strings, IDs `MICRO:1`
dst, explicit four-level layout, local raw-byte moments di semua parent,
snapshot registry immutable, create-only output, dan resource bounds merupakan
keputusan implementasi **0.1.0**. Keputusan tersebut didokumentasi dan diuji, tetapi
tidak diatribusikan sebagai kutipan desain asli yang belum pernah ditetapkan pengguna.

Konteks historis bahwa matriks/coordinates tidak boleh digantikan diam-diam dengan
codec byte-deduplication digunakan sebagai panduan kehati-hatian. Sumber otoritatif
untuk rumus dan acceptance tetap attachment, addendum percakapan, dan permintaan kini.

## Materi workspace lama

`smtyx-prime/matrix-decoder-encoder.md` dan
`smtyx-prime/matrix-definition-code-complete.zip` telah ada sebelum pekerjaan ini.
Keduanya dipertahankan tanpa perubahan. Runtime baru ditempatkan pada root
`F:\SMITYX`, terpisah dari materi lama; archive lama tidak diekstrak atau diklaim
sebagai kode runtime baru. Tidak ada Git repository terdeteksi pada root proyek lama.

## Lisensi dan atribusi

Implementasi baru menggunakan **Apache-2.0**, sesuai permintaan dan arah lisensi
attachment. Teks lisensi lengkap terdapat pada `LICENSE`; atribusi desain terdapat
pada `NOTICE`, README, SPEC, metadata output, dan fixture provenance.
Teks LICENSE diambil dari [Apache Software Foundation](https://www.apache.org/licenses/LICENSE-2.0.txt).
Lisensi/atribusi materi lama tetap mengikuti sumbernya; pekerjaan ini tidak
mengganti atau menghapus notice yang mungkin terdapat di dalam archive lama.
