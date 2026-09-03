# Vocab_Agent v0.1

`Vocab_Agent` adalah bahasa perantara ringkas, terstruktur, dan model-agnostic untuk komunikasi antar-LLM dan tool.
Tujuannya: membuat pesan antar-komponen AI dapat dipertukarkan dengan bentuk yang mudah diparse, tidak bergantung vendor/model, dan tetap bisa dibaca manusia.

## Kenapa dibuat

Bahasa manusia alami sering ambigu dan terlalu panjang untuk protokol antar-model.
`Vocab_Agent` menyediakan:

- bentuk simbolik (kata kunci tetap),
- bentuk numerik (ID numerik tetap),
- dan bentuk canonical JSON terstruktur.

Semua bentuk ini mewakili makna yang sama di atas vocabulary dan grammar yang eksplisit.

## Perbedaan

- Human language: fleksibel, ambigu, natural.
- Vocab_Agent symbolic: stabil, singkat, deterministik.
- Vocab_Agent numeric: transport-safe, minim risiko variasi penulisan.
- Canonical JSON: struktur eksplisit untuk validasi otomatis.

## Bentuk symbolic

Contoh:

`READ PDF SEARCH ERROR FIX VERIFY END`

## Bentuk numeric

`001 056 003 079 011 013 100`

## Canonical state

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

## Grammar v0.1

Grammar dasar (disederhanakan):

- sequence utama menggunakan kumpulan kelas vocab (`ACTION`, `OBJECT`, `STATE`, `TARGET`, `CONTROL`, `META`),
- minimal pola `ACTION OBJECT STATE TARGET`,
- support rantai aksi: `ACTION ACTION ... ACTION`,
- terminator opsional tetapi disarankan: `END`.

Lihat detail lengkapnya di [`grammar/grammar.md`](F:/AIVOCAB/grammar/grammar.md).

## Parser

`src/parser.py`:

- mengenali token simbolik dan numerik,
- konversi ke canonical JSON,
- menghasilkan peran token berdasarkan metadata kelas,
- tidak bergantung urutan semata (menggunakan `primary_class` dan `secondary_class`).
- menerima kalimat manusia pakai fungsi `parse_human_instruction()` untuk map alias (termasuk nama bahasa pemrograman populer).

Contoh:

```python
from src import parser

parser.parse_human_instruction("Jalankan file Python ini lalu verifikasi error.")
```

## Encoder

`src/encoder.py`:

- mengubah canonical JSON menjadi symbolic (`str`),
- dan numeric (`str`),
- contoh:

```python
{
    "actions": ["READ", "SEARCH", "FIX", "VERIFY"],
    "object": "PDF",
    "target": "ERROR"
}
```

menjadi:

- symbolic: `READ PDF SEARCH ERROR FIX VERIFY END`
- numeric: `001 056 003 079 011 013 100`

## Decoder

`src/decoder.py`:

- menerima symbolic atau numeric,
- mengembalikan canonical JSON,
- bisa dipakai untuk roundtrip pada model berbeda.

## Validator

`src/validator.py` memeriksa:

- opcode tidak dikenal,
- opcode duplikat yang tidak masuk akal,
- sequence tidak valid,
- object / action hilang,
- ketiadaan `END` (jika mode require),
- nilai `confidence` di luar rentang,
- version compatibility.

Output validator berbentuk:

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

## Bridge/Orchestrator (Translator-to-Tool)

Modul `src/bridge.py` adalah lapisan kontrol untuk konsep kamu:
- parse prompt manusia / symbolic / numeric,
- validasi via `validator`,
- pilih `tool_call` dari aturan di `src/bridge_config.json`,
- kirim hasil ke eksekutor tool secara aman.
- setiap hasil `route()` memiliki `semantic_state` (state protocol), `ack`, dan `protocol_version` untuk observability.
- status semantic utama:
  - `FINAL`: respons asisten mandiri (contoh aritmatika),
  - `VERIFIED`: tool route siap dieksekusi (dengan kontrol),
  - `PARSED`: tool route menunggu konfirmasi.

Contoh:

```python
from src.bridge import VocabOrchestrator

router = VocabOrchestrator()
print(router.route("hitung satu tambah satu"))
# {'mode': 'assistant', 'answer': '2', ...}

payload = {"version":"0.1","actions":["RUN","VERIFY"],"object":"PYTHON","target":"ERROR","end":True}
print(router.route(payload)["input_mode"])
# 'canonical_dict'

print(router.route('{"version":"0.1","actions":["RUN","VERIFY"],"object":"PYTHON","target":"ERROR","end":true}')["input_mode"])
# 'canonical_json'

route = router.route("Tolong buka Windows Notepad")
# {'mode': 'tool', 'tool_calls': [...], 'requires_confirmation': True, ...}
print(route["protocol_version"])
print(route["semantic_state"]["status"])
print(route["ack"])

exec_result = router.execute(route, confirm=False, dry_run=True)
# status deferred (aman, tidak buka aplikasi nyata saat default dry-run=True)
```

Adaptor eksekusi ada di `src/executor.py` untuk menghubungkan command nyata sesuai kebijakan allowlist.

## Interoperability

`examples/interoperability_cases.jsonl` menyediakan minimal 30 kasus uji lintas-model.
Tujuannya agar banyak LLM bisa merekonstruksi makna yang sama dari bentuk numeric maupun symbolic dengan `core_vocab.json` yang sama.

## Versioning

- Versi ini adalah `Vocab_Agent v0.1`.
- ID `001`–`100` tidak boleh mengubah makna di versi ini.
- vocab baru ditambah mulai dari ID `101` (contoh: `PYTHON`, `JAVASCRIPT`, `RUBY`, dll).
- arti lama tidak boleh diam-diam diubah.

## Alur end-to-end

1. Human instruction:

`Baca PDF ini, cari error, perbaiki, lalu verifikasi.`

2. Hasil canonical:

```json
{
  "version": "0.1",
  "actions": ["READ", "SEARCH", "FIX", "VERIFY"],
  "object": "PDF",
  "target": "ERROR"
}
```

3. Symbolic:

`READ PDF SEARCH ERROR FIX VERIFY END`

4. Numeric:

`001 056 003 079 011 013 100`

5. Target model menerima simbolik/numeric, decode ke canonical, lalu decode balik ke bentuk manusia:

`Baca PDF, temukan error, perbaiki, dan verifikasi.`

## Eksekusi test

Tidak ada dependency berat; cukup Python standard library.
Jalankan:

```bash
python -m unittest tests.test_vocab_agent
```

Smoke test cepat:

```bash
python run_smoke.py
```

Real-check (scenario nyata):

```bash
python run_real_checks.py
```

Output `run_real_checks.py` menampilkan:

- hasil parser untuk kalimat manusia,
- routing `mode` (`assistant` / `tool`),
- status semantic protocol (`VERIFIED`/`PARSED`/`FINAL`),
- hasil dry-run eksekusi tool (selalu aman, tidak mengeksekusi command nyata).

Interoperability antar AI:

```bash
python run_ai_interop_check.py
```

`run_ai_interop_check.py` mensimulasikan:
- AI pertama meroute prompt ke protokol Vocab,
- AI kedua menerima `symbolic` dan `canonical` dari AI pertama,
- pengecekan konsistensi `mode` dan `status`,
- preview eksekusi tool tetap aman via `dry-run`.

Custom prompt dari CLI:

```bash
python run_ai_interop_check.py --input "convert sql to json"
```

Contoh uji direktori/path:

```bash
python run_ai_interop_check.py --input "Baca file F:\\AI" --expect-mode tool --expect-status VERIFIED --expect-confirmation false
python run_ai_interop_check.py --input "Buka folder F:\\AI" --expect-mode tool --expect-status VERIFIED --expect-confirmation false
```

Contoh kasus yang difilter dengan label:

```bash
python run_ai_interop_check.py --input "convert sql to json" --case-label "sql|convert"
```

Opsional (untuk strict check):

```bash
python run_ai_interop_check.py --input "Tolong buka Windows Notepad" --expect-mode tool --expect-status PARSED --expect-confirmation true
```

Contoh strict + stop cepat:

```bash
python run_ai_interop_check.py --strict --input "Tolong buka Windows Notepad" --expect-mode tool --expect-status PARSED --expect-confirmation true --max-failures 1
```

Mengirim payload JSON (langsung):

```bash
python run_ai_interop_check.py --input-json "{\"version\":\"0.1\",\"actions\":[\"RUN\",\"VERIFY\"],\"object\":\"PYTHON\",\"target\":\"ERROR\",\"end\":true}"
```

Batch dari file JSONL:

```bash
python run_ai_interop_check.py --jsonl custom_cases.jsonl
```

Batch dari file JSON (single object atau list):

```bash
python run_ai_interop_check.py --json custom_cases.json
```

Contoh isi `custom_cases.json`:

```json
[
  {"label":"run python","input":"Jalankan Python lalu verifikasi error.","expected_mode":"tool","expected_status":"VERIFIED"},
  {"label":"notepad","input":"Tolong buka Windows Notepad","expected_mode":"tool","expected_status":"PARSED","expect_confirmation":true}
]
```

Output JSON report (untuk CI / integrasi tool):

```bash
python run_ai_interop_check.py --input "hitung satu tambah satu" --format json --output interop_report.json
```

Format JSON juga bisa dibuat tanpa cek dry-run:

```bash
python run_ai_interop_check.py --format json --no-dry-run
```

Case filter untuk smoke check:

```bash
python run_ai_interop_check.py --jsonl custom_cases.jsonl --case-label "notepad|math" --skip-case-label "interop"
```

Note: untuk file `examples/interoperability_cases.jsonl`, `--case-label` akan cocok jika item punya `label` atau `human_instruction` (otomatis digunakan sebagai kandidat label).

Ringkasan opsi `run_ai_interop_check.py`:

- `--input` : prompt string custom (bisa dipakai beberapa kali)
- `--expect-mode` : validasi mode (`assistant`/`tool`) untuk input custom
- `--expect-status` : validasi status (`PARSED`/`VERIFIED`/`FINAL`) untuk input custom
- `--expect-confirmation` : validasi `requires_confirmation` (`true`/`false`) untuk input custom
- `--input-json` : payload custom JSON inline
- `--json` : file JSON berisi list atau objek kasus tunggal
- `--jsonl` : file JSONL per baris kasus
- `--case-label` : run hanya kasus dengan label yang match regex
- `--skip-case-label` : skip kasus dengan label yang match regex
- `--strict` : wajibkan ekspektasi `mode`, `status`, dan `expect_confirmation` pada setiap kasus
- `--max-failures` : stop cepat setelah jumlah fail mencapai batas ini
- `--format` : `text` atau `json`
- `--output` : path hasil JSON report
- `--no-dry-run` : skip preview eksekusi tool

Contoh isi `custom_cases.jsonl`:

```json
{"label":"run python verify", "input":"Jalankan Python lalu verifikasi error.", "expected_mode":"tool", "expected_status":"VERIFIED"}
{"label":"open notepad", "input":"Tolong buka Windows Notepad", "expected_mode":"tool", "expected_status":"PARSED", "expect_confirmation":true}
{"label":"math", "input":"026 013 101 079 100", "expected_mode":"tool", "expected_status":"VERIFIED"}
{"label":"canonical custom", "payload":{"version":"0.1","actions":["RUN","VERIFY"],"object":"PYTHON","target":"ERROR","end":true}, "expected_mode":"tool", "expected_status":"VERIFIED"}
```

Catatan JSONL:
- `input` / `payload` / `input_payload` boleh dipakai sebagai data input.
- `payload` yang langsung object juga bisa dipakai tanpa wrapper (tanpa `input`).
- `expected_mode` dan `expected_status` opsional bila tidak memakai argumen `--expect-*`.

Catatan keamanan:

- kasus sederhana (mis. `hitung satu tambah satu`) dijawab langsung oleh parser/aritmatika,
- kasus kompleks menghasilkan `mode=tool` untuk diteruskan ke adapter,
- perintah berisiko (`notepad`) ditandai `requires_confirmation=True`.
