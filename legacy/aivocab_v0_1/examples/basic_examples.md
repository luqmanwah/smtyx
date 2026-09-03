# Vocab_Agent v0.1 — Basic Examples

## 1) Dokumen + error handling

Human:
`Baca PDF, cari error, perbaiki, lalu verifikasi.`

Symbolic:
`READ PDF SEARCH ERROR FIX VERIFY END`

Numeric:
`001 056 003 079 011 013 100`

Canonical:
`{"actions":["READ","SEARCH","FIX","VERIFY"],"object":"PDF","target":"ERROR","end":true}`

## 2) Coding

Human:
`Analisis kode, validasi, lalu laporan hasilnya.`

Symbolic:
`ANALYZE CODE VALIDATE REPORT END`

Numeric:
`017 058 014 050 100`

Canonical:
`{"actions":["ANALYZE","VALIDATE","REPORT"],"object":"CODE","end":true}`

## 3) Vision

Human:
`Baca gambar ini lalu verifikasi kontennya.`

Symbolic:
`READ IMAGE ANALYZE VERIFY END`

Numeric:
`001 052 017 013 100`

Canonical:
`{"actions":["READ","ANALYZE","VERIFY"],"object":"IMAGE","end":true}`

## 4) Web + routing

Human:
`Cari web untuk peringatan lalu kirim ke agent model.`

Symbolic:
`SEARCH WEB WARNING ROUTE AGENT END`

Numeric:
`003 061 080 038 068 100`

Canonical:
`{"actions":["SEARCH","ROUTE"],"object":"WEB","target":"WARNING","destination":"AGENT","end":true}`

## 5) Calculator

Human:
`Hitung data lalu bandingkan hasilnya.`

Symbolic:
`CALCULATE DATA COMPARE RESULT END`

Numeric:
`015 059 016 094 100`

Canonical:
`{"actions":["CALCULATE","COMPARE"],"object":"DATA","target":"RESULT","end":true}`

## 6) State / control

Human:
`Mulai pekerjaan, jalan ke web, lalu tunda, lanjutkan lagi, selesai.`

Symbolic:
`START WEB WAIT RESUME FINISH END`

Numeric:
`031 061 033 029 032 100`

Canonical:
`{"actions":["START","WAIT","RESUME","FINISH"],"object":"WEB","end":true}`
