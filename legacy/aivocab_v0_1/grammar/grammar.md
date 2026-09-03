# Grammar Vocab_Agent v0.1

## Prinsip utama

- Parser memakai metadata vocabulary (`primary_class`, `secondary_class`) supaya tidak hanya tergantung posisi token.
- Grammar bisa dikembangkan tanpa mengubah ID 001-100.
- `END` (`100`) dipakai sebagai terminator.

## Bentuk token

Token input dibagi menjadi:

- `ACTION`: tindakan yang mengubah atau memproses.
- `OBJECT`: materi/target data yang diproses.
- `STATE`: status/status token.
- `CONTROL`: kontrol urutan alur.
- `META`: metadata tambahan seperti prioritas atau confidence.

## Grammar ringkas

```text
Instruction ::= Segment+ [END]
Segment      ::= ACTION [OBJECT] [STATE*] [TARGET_MARKER? STATE_OR_META*] [ACTION*] [meta_tail]
TARGET_MARKER ::= TARGET
```

Pada prakteknya parser membaca:

1. Aksi: urutan token berkelas `ACTION` (termasuk `STOP/START/WAIT/RETRY`).
2. Objek: token pertama berkelas `OBJECT`.
3. Target: token berkelas `STATE` yang bermakna hasil pencarian/error.
4. State: status tambahan (`READY`, `ACTIVE`, `DONE`, ...).
5. Destination: objek kedua (jika ada) setelah object primer.
6. Meta: `PRIORITY`, `CONFIDENCE`, `HIGH|MEDIUM|LOW|URGENT`.

## Konvensi contoh

- `READ PDF SEARCH ERROR FIX VERIFY END`
- `CREATE FILE REPORT ERROR END`
- `CALL MODEL ROUTE CODEX END`
- `CALCULATE DATA COMPARE RESULT END`

## Alasan desain

- Sequence tidak diputuskan hanya berdasar posisi.
- Setiap token dianalisis kelasnya dari `core_vocab.*`.
- Ketika kata tidak dikenal, parser tetap memberi error terstruktur.

## Bahasa pemrograman yang didukung

Vocab menambahkan token bahasa pemrograman pada ID `101`–`114`:
`PYTHON`, `JAVASCRIPT`, `TYPESCRIPT`, `JAVA`, `CSHARP`, `CPP`, `GO`, `RUST`, `PHP`, `SQL`, `R`, `KOTLIN`, `SWIFT`, `RUBY`.

Contoh parsing manusia:

`Jalankan script Python lalu verifikasi` → `RUN PYTHON VERIFY END`
