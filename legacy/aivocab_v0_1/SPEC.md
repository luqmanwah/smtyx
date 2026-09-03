# Spesifikasi Teknis Vocab_Agent v0.1

## 1. Scope

Vocab_Agent v0.1 bertujuan membuat bahasa perantara stabil untuk pertukaran instruksi antar model/komponen:

- vocabulary inti 100 token dasar + ekstensi object bahasa pemrograman (ID 101+),
- grammar berbasis kelas token,
- canonical state,
- parser, encoder, decoder, validator,
- policy + aturan alat (`policy.py`, `bridge_config.json`),
- bridge orchestrator (`bridge.py`) dan execution adapter (`executor.py`),
- koleksi kasus interoperability.

Tidak mencakup:

- orchestrator bridge minimal (route/execute),
- UI,
- fine-tuning,
- vector embedding,
- tooling eksekusi otonom.

## 2. Vocabulary

- Token awal ID `001` sampai `100` bersifat tetap untuk v0.1.
- Ekstensi v0.1 ditambahkan mulai dari ID `101` (contoh bahasa pemrograman populer).
- Setiap token memiliki:
  - `id`
  - `name`
  - `primary_class`
  - `secondary_class` opsional
  - `description`
- Dokumen sumber:
  - `vocab/core_vocab.md`
  - `vocab/core_vocab.json`
  - `vocab/core_vocab.yaml`

## 3. Kelas

Token dikelompokkan minimal ke:

- `ACTION`
- `OBJECT`
- `STATE`
- `CONTROL`
- `META`

Satu token bisa memiliki `secondary_class`.

## 4. Canonical form

Canonical state berbasis JSON:

```json
{
  "version": "0.1",
  "actions": ["READ", "SEARCH", "FIX", "VERIFY"],
  "object": "PDF",
  "target": "ERROR",
  "state": "READY",
  "priority": "MEDIUM",
  "confidence": 0.95,
  "destination": "CODEX",
  "end": true
}
```

## 5. Grammar

Grammar dasar harus men-support:

- pola dasar `ACTION OBJECT STATE TARGET`,
- aksi berantai `ACTION ACTION ... ACTION`,
- terminator `END`.

Contoh:

- `READ PDF SEARCH ERROR FIX VERIFY END`

Parser tidak hanya mengandalkan posisi; peran token ditentukan dari metadata kelas vocab.

## 6. Parser

`src/parser.py` harus:

- membaca input symbolic (`READ PDF ...`) atau numeric (`001 ...`),
- memetakan token ke objek vocabulary,
- mengembalikan canonical state.

Output parser:
- daftar `actions`,
- `object` utama,
- `target` bila tersedia,
- `state`, `priority`, `destination`,
- nilai `confidence` bila dinyatakan,
- flag `end`,
- metadata parsing bila ada token tidak dikenal.

## 7. Encoder

Input:

```python
{
    "actions": ["READ", "SEARCH", "FIX", "VERIFY"],
    "object": "PDF",
    "target": "ERROR",
    "state": "READY",
    "priority": "MEDIUM"
}
```

Output:

- symbolic string,
- numeric string,
- default terminator `END` dan `100` disertakan.

## 8. Decoder

Input symbolic atau numeric diubah kembali ke canonical JSON.

## 9. Validator

Validasi mencakup:

- opcode tidak dikenal,
- duplikasi opcode yang tidak masuk akal,
- urutan token tidak valid,
- hilangnya aksi/object,
- hilangnya END bila grammar memerlukannya,
- confidence out of range,
- inkompatibilitas versi.

Output:

```json
{
  "valid": false,
  "errors": [
    {
      "code": "UNKNOWN_OPCODE",
      "value": "999"
    }
  ]
}
```

## 10. Interoperability

`examples/interoperability_cases.jsonl` berisi minimal 30 kasus.
Setiap kasus memuat:

- `human_instruction`
- `expected_canonical_state`
- `symbolic_vocab`
- `numeric_vocab`
- `expected_human_reconstruction`

## 11. Keberhasilan V1

- 100 token terdaftar di ketiga file vocab.
- grammar, parser, encoder, decoder, validator berfungsi.
- 30+ kasus interoperability tersedia.
- proyek tidak memakai dependency berat; Python stdlib cukup.
- bridge menghasilkan payload kontrol `semantic_state` dan `ack` dasar untuk setiap rute.

## 12. Bridge/Execution

- Bridge output memisahkan mode:
  - `mode=assistant`: operasi langsung (contoh `hitung satu tambah satu`).
  - `mode=tool`: kasus kompleks yang membutuhkan delegasi tool.
- `src/bridge.py` bertugas menghasilkan:
  - `canonical`
  - `symbolic`
  - `numeric`
  - daftar `tool_calls` (tool, action, command, argument).
- `src/executor.py` mengeksekusi dengan pengaman:
  - default `dry_run=True`,
  - deteksi konfirmasi eksplisit (`requires_confirmation`),
  - allowlist command untuk PowerShell,
  - status `deferred`, `executed`, `failed`, atau `blocked`.
