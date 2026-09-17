# SMTYX — Design Freeze dari Percakapan
**Tanggal freeze:** 17 September 2026  
**Originator / initial designer:** @luqmanwah  
**Status:** Working canonical design / research freeze  
**Lisensi implementasi yang direncanakan:** Apache License 2.0  
**Prinsip utama:** *Think big, execute small; communicate state, not conversation.*

---

# 1. Ringkasan Eksekutif

SMTYX diposisikan sebagai **runtime interoperabilitas semantik** yang menghubungkan manusia, big/cloud model, mini/local model, agent, tool, CLI, IoT, sensor, perangkat low-bandwidth, dan controller deterministik.

SMTYX **bukan sekadar tokenizer, bukan sekadar encoding, bukan sekadar prompt format, dan bukan model AI baru**.

SMTYX adalah runtime yang:

1. menerima maksud / event / command;
2. mem-parsing ke bentuk kanonik;
3. mereduksi prompt panjang menjadi command minimum;
4. memilih model/tool/agent yang paling tepat;
5. mengirim hanya state/delta yang diperlukan;
6. melakukan verifikasi;
7. melakukan eskalasi dari small → big hanya jika dibutuhkan;
8. mengembalikan kontrol ke orchestrator lokal setelah masalah selesai.

Core SMTYX tetap **runtime-agnostic** dan **model-agnostic**.

---

# 2. Masalah yang Ingin Diselesaikan

## 2.1 Prompt overhead

Model kecil sering hanya perlu mengetahui:

```text
DARI MANA?
KERJAKAN APA?
OUTPUT APA?
BATASAN APA?
```

Contoh SMTYX:

```text
A>READ
A>SUM
A>FIND:NPWP
A>EDIT:NUMBERING
```

## 2.2 Big model terlalu sering dipakai

Target:

```text
KNOWN TASK
→ SMTYX
→ TOOL / MINI MODEL
→ DONE
```

Hanya jika:

```text
UNKNOWN
AMBIGUOUS
CONFLICT
NEW_PATTERN
COMPLEX_REASONING
TROUBLE
```

maka:

```text
SMTYX
→ BIG MODEL / CODEX
→ evaluate / troubleshoot / plan
→ return control
→ LOCAL ORCHESTRATOR
```

## 2.3 Komunikasi antar-AI terlalu verbose

SMTYX menormalisasi:

```text
Human/native expression
→ canonical semantic state
→ target-specific minimal prompt
```

## 2.4 Low-bandwidth / IoT

Target media:

```text
2G
LoRa
BLE
serial
radio
cahaya
audio/pulse
```

Pipeline:

```text
semantic coordinate
→ compact numeric packet
→ binary / pulse / Morse / color / frequency
```

---

# 3. Posisi SMTYX

> **SMTYX Runtime is an adaptive semantic normalization, routing, and execution layer that converts complex intent into compact canonical tasks across heterogeneous models, agents, tools, and constrained devices.**

Versi sederhana:

> **Big model berpikir. SMTYX menyederhanakan, merutekan, dan memvalidasi. Small model/tool/perangkat mengeksekusi.**

---

# 4. Prinsip Arsitektur

## 4.1 Use the smallest capable intelligence

```text
deterministic task → tool
simple task        → mini/local model
complex task       → big model
conflict           → big verifier
urgent/exact       → SMTYX v2
```

## 4.2 Context disimpan runtime

Contoh:

```text
REF A = F:\Project\akta.docx
```

Setelah itu:

```text
A>READ
A>SUM
A>FIND:NPWP
```

## 4.3 Communicate state, not conversation

Contoh:

```text
DOC|DONE|A>B|OK
```

## 4.4 Shared knowledge + delta

\[
FullObject = SharedBase + Delta
\]

---

# 5. SMTYX Runtime sebagai Kunci

```text
SMTYX Runtime
│
├── Parser
├── Semantic Normalizer
├── Matrix Engine
├── Vocab Registry
├── Schema Registry
├── Capability Registry
├── Behavioral Profiler
├── Prompt Compiler
├── Router
├── Validator
├── SOP Registry
├── Tool Registry
├── State Store
├── Transport Adapters
└── Model / Agent Adapters
```

Pipeline:

```text
INPUT
↓
PARSER
↓
NORMALIZER
↓
CANONICAL STATE / MATRIX
↓
CAPABILITY MATCH
↓
ROUTER
↓
TOOL / MINI MODEL / BIG MODEL / DEVICE
↓
RESULT
↓
VALIDATOR
↓
CANONICAL OUTPUT
```

---

# 6. SMTYX v1

SMTYX v1 = **adaptive / behavioral mode**.

Fungsi:

- mengenali kebiasaan model;
- mengenali kebiasaan manusia/prompter;
- memilih prompt minimum;
- menyimpan alias antar-model;
- belajar melalui pretest;
- mengurangi token;
- routing normal;
- big ↔ small handoff;
- local ↔ cloud handoff.

## 6.1 Behavioral weights

SMTYX tidak membaca bobot neural private model.

SMTYX membuat **behavioral weight**:

```text
short_command_ok      = 0.98
schema_compliance     = 0.94
json_compliance       = 0.96
tool_reliability      = 0.91
ambiguity_tolerance   = 0.63
retry_sensitivity     = 0.78
```

## 6.2 Adaptive prompt compiler

Canonical task:

```text
SOURCE=A
ACTION=FIND
TARGET=NPWP
OUTPUT=EXACT
```

Model A:

```text
FIND:NPWP
```

Model B:

```text
TASK=FIND
TARGET=NPWP
RETURN=VALUE_ONLY
```

---

# 7. SMTYX v2

SMTYX v2 hanya digunakan saat:

```text
URGENT
EXACT
CONFLICT
AMBIGUOUS
REPEATED_FAILURE
SECURITY_CRITICAL
LOW_CONFIDENCE
MISMATCH
```

v2 = **deterministic / mathematical / exact mode**.

Escalation:

```text
V1
↓
berhasil?
├── YES → DONE
└── NO
    ↓
    V2!
    ↓
    strict schema + constraint + proof
```

---

# 8. Model Matematis SMTYX

Untuk sequence byte:

\[
X=[x_1,x_2,\ldots,x_N]
\]

ditetapkan:

\[
N=	ext{jumlah byte}
\]

\[
P_0=\sum_i x_i
\]

\[
P_1=\sum_i i x_i
\]

\[
P_2=\sum_i i^2 x_i
\]

\[
P_3=\sum_i i^3 x_i
\]

Signature dasar:

\[
X_{sig}=[N,P_0,P_1,P_2,P_3]
\]

Arti:

```text
N  = jumlah byte/karakter
P0 = bobot isi tanpa posisi
P1 = positional moment level 1
P2 = positional moment level 2
P3 = positional moment level 3
```

## 8.1 Contoh "hello"

```text
N  = 5
P0 = 532
P1 = 1617
P2 = 5983
P3 = 24615
```

```text
[5,532,1617,5983,24615]
```

## 8.2 Contoh "hello world"

```text
N  = 11
P0 = 1116
P1 = 6736
P2 = 52204
P3 = 453382
```

```text
[11,1116,6736,52204,453382]
```

---

# 9. Batas Matematis

`[N,P0,P1,P2,P3]` **bukan representasi lossless universal**.

Ia adalah:

```text
signature
features
constraints
fingerprint
```

Exact reconstruction membutuhkan tambahan seperti:

- multiset karakter;
- coordinate set;
- P tambahan;
- order information;
- registry/reference;
- shared vocabulary;
- template/base + delta;
- chunk hierarchy.

---

# 10. Coordinate Byte: DEC / HEX / BINARY

Contoh:

```text
h
DEC    = 104
HEX    = 68
BINARY = 01101000
COORD  = (6,8)
```

Definisi:

\[
C(x)=(high\ nibble,low\ nibble)
\]

---

# 11. Matrix Token SMTYX

Satu byte dapat direpresentasikan sebagai:

```text
[DEC, HEX_HIGH, HEX_LOW, bit7, bit6, bit5, bit4, bit3, bit2, bit1, bit0]
```

Contoh `h`:

```text
[104,6,8,0,1,1,0,1,0,0,0]
```

---

# 12. Hierarki Data SMTYX

Keputusan:

```text
MICRO → BLOCK → PAGE → CONTAINER/DOC
```

Singkatan:

```text
M = MICRO
B = BLOCK
P = PAGE
C = CONTAINER / root
```

Setiap level memakai:

```text
[N,P0,P1,P2,P3]
```

Target awal:

```text
MICRO = ±16–32 byte
```

BLOCK = kumpulan MICRO.  
PAGE = kumpulan BLOCK.  
CONTAINER/DOC = kumpulan PAGE.

Prinsip:

> **Naik level hanya jika struktur objek memang memerlukannya.**

---

# 13. Recursive Mathematical Encoding

```text
BYTE
↓
M
↓
B
↓
P
↓
C
```

Setiap node:

```text
Node.math = [N,P0,P1,P2,P3]
```

---

# 14. Neural Concept

Eksperimen:

```text
M1 → n1
M2 → n2
M3 → n3
M4 → n4
        ↓
       B1
```

Keputusan penting:

> **Weight tidak boleh mengubah identitas matematis node.**

Pisahkan:

```text
Node.math   = deterministic
Node.weight = learned / behavioral
```

\[
Identity 
eq Weight
\]

Weight dipakai untuk:

- relevance;
- routing;
- attention;
- learned behavior;
- scoring.

Level weight:

```text
W_M
W_B
W_P
W_C
```

---

# 15. Contoh Paragraf

Input:

```text
Jam tiga pagi, kota kehilangan bayangannya. Hanya Nara yang melihat mereka berbaris menuju laut. Ia mengikuti jejak itu, lalu sadar: matahari dicuri seseorang yang belum lahir.
```

Global:

```text
[176,16348,1455279,171575415,22744318665]
```

MICRO:

```text
M1 = [32,2893,48470,1055954,25713434]
M2 = [32,2974,48322,1056534,26078662]
M3 = [32,3060,50396,1085720,26241062]
M4 = [32,2876,48053,1032449,25076861]
M5 = [32,3064,51319,1115445,27129211]
M6 = [16,1481,12463,135489,1649419]
```

BLOCK:

```text
B1 = [128,11803,762345,65084481,6250734819]
B2 = [48,4545,111174,3565110,128601318]
```

---

# 16. Numeric Chunk Layer

Nilai besar dipecah **basis-100** dari kanan.

Contoh B1:

```text
N  = 128
P0 = 11803
P1 = 762345
P2 = 65084481
P3 = 6250734819
```

Menjadi:

```text
N  = 1|28
P0 = 1|18|03
P1 = 76|23|45
P2 = 65|08|44|81
P3 = 62|50|73|48|19
```

Karena chunk hanya `0–99`, satu chunk cukup 7 bit.

---

# 17. Symbol Layer / Morse Bridge

Eksperimen:

```text
12|8          → L H
11|80|3       → K B C
76|23|45      → X W S
65|08|44|81   → M H R C
62|50|73|48|19→ J X U V S
```

Contoh symbolic stream:

```text
1LH-1KBC-XWS-MHRC-JXUVS
```

Tujuan huruf:

> **jembatan ke media pulse/Morse, bukan storage utama.**

Jika memakai modulo 26, huruf saja tidak reversible.

Exact coordinate:

\[
n=26q+r
\]

Contoh:

```text
80 → (3,B)
76 → (2,X)
45 → (1,S)
```

---

# 18. SMTYX Morse

Pipeline:

```text
SMTYX Math
↓
numeric chunks
↓
symbol
↓
Morse / pulse
↓
light / radio / audio / sensor
```

Target akhir:

> **frequency-optimized semantic/numeric prefix code**

Command sering → pulse lebih pendek.  
Command jarang → pulse lebih panjang.

---

# 19. Color / RGB Transport Experiment

Contoh palette eksperimen:

```text
#01014C
#413EEB
#1C1217
#0832EB
#0A032D
#2C49EB
#0A0011
#5130EB
#0A0102
```

Pipeline:

```text
matrix/math
↓
HEX bytes
↓
RGB
↓
light/color signal
↓
camera/sensor
↓
HEX
↓
SMTYX decoder
```

Status: **experimental transport encoding, bukan encryption**.

---

# 20. Terminator Hierarki

```text
EM = END MICRO
EB = END BLOCK
EP = END PAGE
```

Jika diperlukan:

```text
EC / ED = END CONTAINER / DOCUMENT
```

---

# 21. Encoding ≠ Encryption

Math/Morse/RGB/HEX bukan encryption.

Jika confidentiality diperlukan:

```text
SMTYX compact packet
↓
AES-GCM / ChaCha20-Poly1305
↓
ciphertext
↓
transport
```

---

# 22. SMTYX Semantic Tokenizer

Tokenizer SMTYX tidak sekadar memecah teks.

Target:

> **heterogeneous expressions → canonical semantic symbols**

Contoh:

```text
"jalankan program"
"buka aplikasi"
"run program"
"start process"
```

→

```text
RUN_PROGRAM
```

---

# 23. Adaptive Macro Tokenizer

Known pattern panjang harus dapat menjadi satu/few macro-token.

Contoh:

```text
USE FILE
+ FIND NPWP
+ RETURN EXACT
```

→

```text
<FIND_NPWP_EXACT>
```

atau:

```text
T418
```

Prinsip:

\[
LongSequence = KnownPattern + Delta
\]

Yang ditransmisikan:

\[
PatternID + Delta
\]

---

# 24. GMN — Guess Meaning Node

Pretest sebelum vocabulary stabil.

Contoh:

```text
GMN1 = RUN_PROGRAM
GMN2 = PROGRAM_INIT
GMN3 = EXEC_APP
GMN4 = START_PROCESS
```

Setelah consensus:

```text
GMN1
↓ PROMOTE
ID1 = RUN_PROGRAM
```

---

# 25. Human ↔ SMTYX ↔ AI Dialect

Canonical:

```text
ID1 = RUN_PROGRAM
```

Human aliases:

```text
jalankan program
buka aplikasi
run program
start aplikasi
```

Model dialects:

```text
Model A → PROGRAM_INIT
Model B → EXEC_APP
Model C → START_PROCESS
```

Pipeline:

```text
Human Expression
↓
Canonical Semantic ID
↓
Target Model Expression
```

---

# 26. One Day One Learn

Strategi bootstrap vocabulary hemat API:

```text
Hari 1 → RUN_PROGRAM
Hari 2 → READ_FILE
Hari 3 → FIND_VALUE
...
```

Pretest order:

```text
deterministic parser
↓
local model
↓
cache
↓
free / low-cost online model
↓
paid big model terakhir
```

---

# 27. Daily Task Runtime

Milestone awal:

```text
A>READ
A>SUM
A>FIND:"jangka waktu"
A>FIND:NPWP
A>EDIT:NUMBERING
A>VERIFY
A>PDF
```

---

# 28. CLI

```bash
smtyx ref A "F:\Project\akta.pdf"
smtyx A>SUM
smtyx A>FIND:NPWP
smtyx A>VERIFY
```

Target:

```text
1 command pendek → 1 task jelas
```

---

# 29. Tool-first Execution

Known deterministic task:

```text
A>PDF
→ DOCX_TO_PDF(A)
→ DONE
```

Unknown/complex:

```text
SMTYX
→ Codex/big planner
→ pilih tool
→ tool execute
→ model berhenti
```

---

# 30. Big ↔ Small

## Big → Small

```text
big reasoning
↓
SMTYX
↓
small canonical task
↓
mini model/tool
```

## Small → Big

```text
CONF low / CONFLICT
↓
SMTYX escalation
↓
big model
```

---

# 31. Cloud Model sebagai Evaluator/Troubleshooter

Cloud/Codex:

- evaluator;
- debugger;
- troubleshooter;
- planner;
- exception handler.

Setelah selesai:

```text
OK>LOCAL
```

---

# 32. Spectator

Spectator = read-only observer.

Boleh:

```text
WATCH
OBSERVE
STATUS
COMPARE
DONE
FAIL
STALE
ALERT
```

Tidak:

```text
EDIT
DELETE
EXECUTE
MODIFY
```

Flow:

```text
LOCAL ORCHESTRATOR
↓
TOOL / MINI MODEL
↓
SPECTATOR
↓
SMTYX EVENT
↓
GPT/CODEX UX
↓
USER
```

---

# 33. Offline Heartbeat

Local core:

```text
SMTYX Runtime
Heartbeat
Spectator
SOP Registry
Vocab Registry
Tool Registry
Mini Model
Local Orchestrator
```

Heartbeat tidak membutuhkan LLM.

---

# 34. IoT / Robot / Physical Systems

Big model tidak berada langsung di fast control loop.

```text
Sensor / Vision
↓
SMTYX
↓
bounded semantic command
↓
fixed safety controller
↓
actuator
```

Contoh command:

```text
LEFT
RIGHT
FORWARD
SLOW
STOP
HOLD
RETURN_HOME
```

---

# 35. Low-bandwidth Semantic Instruction

Natural language:

```text
Obstacle on right. Slow down and turn left.
```

Canonical:

```text
OBSTACLE
RIGHT
SLOW
LEFT
```

Lalu:

```text
semantic IDs
↓
bit packing
↓
radio / 2G / LoRa / light
```

---

# 36. SOP Registry

Known event:

```text
FIRE
HOME.KITCHEN
CRITICAL
```

→

```text
SOP:FIRE_HOME
```

Known SOP → deterministic action/UI.  
Unknown exception → big model.

---

# 37. Forex / Monitoring Example

```text
Market Data
↓
Big Analyst
↓
SMTYX compact state
↓
trend-mini / risk-mini / trade-mini
↓
validator
↓
trade agent
```

Trade output:

```text
BUY@...
SELL@...
WAIT
```

Default:

```text
BUY@ / SELL@ = PROPOSED
```

Eksekusi melewati validator.

---

# 38. Behavioral vs Authority Matrix

Pisahkan:

```text
BEHAVIOR_MATRIX
```

dari:

```text
AUTHORITY_MATRIX
```

Flow:

```text
PROPOSE
↓
VERIFY
↓
AUTHORIZE
↓
EXECUTE
```

---

# 39. Capability Discovery

```text
DESCRIBE CAPABILITIES
```

Contoh:

```text
READ_PDF
ANALYZE_DOC
EXEC_PY
VERIFY_DATA
```

---

# 40. Extensible Vocabulary

Gunakan namespace:

```text
core:analyze
core:verify
obj:document
geo:survey
legal:contract
cad:surface
vendor:...
```

Unknown:

```text
GET SCHEMA <namespace:item>
```

---

# 41. Human vs Internal vs Wire

## Human / Prompt Code
Readable dan singkat.

## Internal Runtime
Matrix/state numerik.

## Wire
Bit-packed / binary / pulse.

---

# 42. Hal yang Masih Eksperimental

Jangan dianggap production-final:

- exact reconstruction arbitrary long text dari P0–P3 saja;
- modulo-letter tanpa family;
- RGB/color production transport;
- Morse adaptive codebook final;
- neural weights per node;
- one-value W sebagai universal fingerprint;
- semantic compression tanpa shared knowledge.

---

# 43. Hukum Informasi

SMTYX tidak bisa losslessly mengubah informasi baru besar menjadi beberapa byte tanpa prior/shared information.

Penghematan besar muncul bila receiver sudah punya:

```text
vocabulary
template
SOP
registry
model
state
context
shared base
```

\[
LargeMeaning = SharedKnowledge + SmallDelta
\]

---

# 44. Final Layer Model

```text
L0  PHYSICAL / SIGNAL
L1  WIRE
L2  MATH / COORDINATE
L3  SEMANTIC TOKEN
L4  STATE / SOP
L5  RUNTIME
L6  INTELLIGENCE
L7  UX
```

Detail:

```text
L0: light / radio / 2G / LoRa / BLE / serial
L1: bit-packed / binary / Morse / color experiment
L2: DEC / HEX / BIN / N / P0-P3 / hierarchy
L3: vocab / ID / macro-token / namespace
L4: intent / action / object / state / policy
L5: parser / router / validator / registry / adapters
L6: tool / mini model / big model / Codex
L7: human language / UI / notification
```

---

# 45. Final Runtime Flow

```text
HUMAN / SENSOR / AI
        ↓
SMTYX PARSER
        ↓
SEMANTIC TOKENIZER
        ↓
CANONICAL STATE / MATRIX
        ↓
KNOWN?
   ┌────┴────┐
  YES        NO
   ↓          ↓
TOOL/MINI   BIG MODEL
   ↓          ↓
RESULT    NEW PATTERN/SOLUTION
   │          ↓
   └────→ SMTYX REGISTRY
              ↓
           REUSE NEXT TIME
```

---

# 46. Final Big-Small Principle

```text
BIG MODEL
= expensive intelligence / reasoning / exception

SMALL MODEL
= routine semantic execution

TOOL
= deterministic execution

SMTYX
= communication + normalization + state + routing

SPECTATOR
= observation

LOCAL ORCHESTRATOR
= continuity / heartbeat / control
```

---

# 47. Final Core Equation

\[
SMTYX =
Math +
SemanticVocabulary +
AdaptiveTokenizer +
Runtime +
Registry +
Router +
Validator
\]

Fungsi:

\[
ComplexIntent ightarrow MinimalExecutableState
\]

Transmisi:

\[
Meaning ightarrow Coordinate ightarrow CompactState ightarrow Signal
\]

Reconstruction berbasis knowledge bersama:

\[
KnownPattern + Delta ightarrow FullMeaning
\]

---

# 48. Final Design Decisions — Locked

1. **SMTYX Runtime adalah inti sistem.**
2. **Model matematis/coordinate tetap fundamental**, terutama untuk low-bandwidth, deterministic state, dan hierarchical representation.
3. **v1 = adaptive behavioral mode** untuk daily task, prompt compression, alias learning, human↔AI dialect, dan big↔small handoff.
4. **v2 = urgent/exact/deterministic mode**, bukan default.
5. `N/P0/P1/P2/P3` adalah **signature/features/constraints**, bukan universal lossless encoding.
6. Data besar memakai **MICRO → BLOCK → PAGE → CONTAINER/DOC**.
7. Semua node dapat memakai **rumus matematika yang sama secara rekursif**.
8. `Math state` harus deterministic; `Weight/learning state` harus dipisahkan.
9. **Adaptive Macro Tokenizer** adalah arah tokenizer SMTYX.
10. Vocabulary lahir melalui **GMN → pretest → consensus → promotion → ID**.
11. **One day one learn** dipakai sebagai bootstrap vocabulary hemat API.
12. CLI daily-task adalah milestone implementasi awal.
13. Task known langsung ke tool/mini-model; big model hanya untuk complex/unknown/error.
14. Cloud/Codex berfungsi sebagai evaluator/troubleshooter/planner dan mengembalikan kontrol ke lokal.
15. Spectator read-only dan mengirim event/state minimum ke UX.
16. Heartbeat harus dapat berjalan offline dengan resource kecil.
17. IoT/robot menerima bounded semantic command, bukan code mutation dari big model.
18. Morse/color/frequency adalah kandidat **transport layer**, bukan meaning layer.
19. Encryption memakai primitive kriptografi standar.
20. Core harus kecil, extensible, namespace-based, vendor/model agnostic.

---

# 49. Immediate Implementation Priority

```text
P0 — Runtime skeleton
P1 — CLI + REF + parser
P2 — Tool registry + deterministic execution
P3 — Local mini-model adapter
P4 — Behavioral profile + prompt compiler
P5 — GMN/pretest/vocab registry
P6 — Macro-token registry
P7 — Big↔small escalation/handoff
P8 — Spectator + heartbeat
P9 — Math hierarchy M/B/P/C
P10 — low-bandwidth wire experiments
P11 — Morse / color / frequency adapters
```

---

# 50. Canonical One-Line Summary

> **SMTYX is a local-first semantic runtime that learns how humans, models, agents, and devices communicate; converts complex intent into compact mathematical/semantic state; executes with the smallest capable resource; and escalates to larger intelligence only when required.**

---

# 51. Canonical Motto

```text
THINK BIG.
EXECUTE SMALL.
TRANSMIT ONLY WHAT CHANGED.
```

---

# 52. Status

Dokumen ini adalah **design-freeze dari percakapan**, bukan production specification final.

Bagian yang sudah dikunci menjadi baseline iterasi implementasi berikutnya.

Bagian experimental harus diuji dengan:

- deterministic tests;
- round-trip tests;
- collision tests;
- token-count comparison;
- bandwidth comparison;
- local-mini-model tests;
- cross-model interoperability tests;
- offline heartbeat tests;
- CLI daily-task benchmarks;
- low-bandwidth transport simulations.
