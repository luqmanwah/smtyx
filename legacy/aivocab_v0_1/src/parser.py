from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "0.1"


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VOCAB_PATH = ROOT_DIR / "vocab" / "core_vocab.json"

TARGET_STATE_TOKENS = {
    "ERROR",
    "WARNING",
    "FOUND",
    "MISSING",
    "INVALID",
    "VALID",
    "RESULT",
    "SAFE",
    "UNSAFE",
    "UNKNOWN",
    "FAILED",
    "DONE",
}

STATE_TOKENS = {
    "READY",
    "ACTIVE",
    "IDLE",
    "BUSY",
    "DONE",
    "FAILED",
    "ERROR",
    "WARNING",
    "FOUND",
    "MISSING",
    "VALID",
    "INVALID",
    "UNKNOWN",
}

PRIORITY_TOKENS = {"HIGH", "MEDIUM", "LOW", "URGENT"}

STOPWORDS = {
    "DI",
    "DAN",
    "DENGAN",
    "DARI",
    "KE",
    "KEPADA",
    "UNTUK",
    "LALU",
    "SEHINGGA",
    "ATAU",
    "JIKA",
    "MAKA",
    "YANG",
    "SAAT",
    "MEREKA",
    "ADALAH",
    "SUDAH",
    "PADA",
    "TAPI",
    "MELALUI",
    "PAKAI",
    "TERSEBUT",
    "INI",
    "ITU",
}

HUMAN_TO_VOCAB = {
    "BACA": "READ",
    "READ": "READ",
    "BUKA": "OPEN",
    "OPEN": "OPEN",
    "LIHAT": "READ",
    "TINJAU": "READ",
    "BUAT": "CREATE",
    "BUATKAN": "CREATE",
    "BICAR": "READ",
    "BIKIN": "CREATE",
    "JALANKAN": "RUN",
    "EKSEKUSI": "RUN",
    "EXECUTE": "RUN",
    "START": "RUN",
    "RUN": "RUN",
    "CARI": "SEARCH",
    "TEMUKAN": "SEARCH",
    "SEARCH": "SEARCH",
    "FIND": "SEARCH",
    "ANALISIS": "ANALYZE",
    "ANALISA": "ANALYZE",
    "ANALYZE": "ANALYZE",
    "CEK": "CHECK",
    "PERIKSA": "CHECK",
    "CHECK": "CHECK",
    "LOOKUP": "SEARCH",
    "VALIDASI": "VALIDATE",
    "VERIFY": "VERIFY",
    "VERIFIKASI": "VERIFY",
    "CHECKS": "CHECK",
    "FIX": "FIX",
    "SELESAI": "END",
    "PERBAIKI": "FIX",
    "REPAIR": "FIX",
    "KOREKSI": "FIX",
    "BANDINGKAN": "COMPARE",
    "COMPARE": "COMPARE",
    "SAMBUNG": "CONNECT",
    "HUBUNGKAN": "CONNECT",
    "TUNGGU": "WAIT",
    "ULANGI": "RETRY",
    "KIRIM": "SEND",
    "KIRIMKAN": "SEND",
    "TERIMA": "RECEIVE",
    "HAPUS": "DELETE",
    "HAPUSKAN": "DELETE",
    "SIMPAN": "SAVE",
    "SIMPANKAN": "SAVE",
    "EDIT": "EDIT",
    "UBAH": "EDIT",
    "UBAHKAN": "EDIT",
    "EKSTRAK": "EXTRACT",
    "EKSTRAKSI": "EXTRACT",
    "AMBIL": "EXTRACT",
    "KONVERSI": "CONVERT",
    "GABUNG": "MERGE",
    "PISAH": "SPLIT",
    "SALIN": "COPY",
    "PINDAH": "MOVE",
    "PEMANTAUAN": "MONITOR",
    "RUTE": "ROUTE",
    "LAPOR": "REPORT",
    "LAPORAN": "REPORT",
    "MULAI": "START",
    "BERHENTI": "STOP",
    "HENTI": "STOP",
    "LANJUTKAN": "RESUME",
    "TUTUP": "CLOSE",
    "CLOSED": "CLOSE",
    "KONEKSI": "CONNECT",
    "SINKRON": "SYNC",
    "SINKRONKAN": "SYNC",
    "HASIL": "OUTPUT",
    "DATA": "DATA",
    "TEKS": "TEXT",
    "DOKUMEN": "DOCUMENT",
    "DOK": "DOCUMENT",
    "GAMBAR": "IMAGE",
    "AUDIO": "AUDIO",
    "VIDEO": "VIDEO",
    "KODE": "CODE",
    "DATABASE": "DATABASE",
    "WEB": "WEB",
    "MEMORI": "MEMORY",
    "AGEN": "AGENT",
    "PENGGUNA": "USER",
    "SISTEM": "SYSTEM",
    "MODEL": "MODEL",
    "FILE": "FILE",
    "FOLDER": "FILE",
    "DIRECTORY": "FILE",
    "DIR": "FILE",
    "TARGET": "TARGET",
    "MODE": "STATE",
    "ERROR": "ERROR",
    "KESALAHAN": "ERROR",
    "WARNING": "WARNING",
    "SELESAIAN": "DONE",
    "GAGAL": "FAILED",
    "BERHASIL": "VALID",
    "VALID": "VALID",
    "SAFETY": "SAFE",
    "AMAN": "SAFE",
    "TIDAKAMAN": "UNSAFE",
    "TIDAK": "UNSAFE",
    "TINGGI": "HIGH",
    "SANGAT": "HIGH",
    "SEDANG": "MEDIUM",
    "RENDANG": "MEDIUM",
    "RENDAH": "LOW",
    "URGEN": "URGENT",
    "SEGERA": "URGENT",
    "CEPAT": "URGENT",
    "PENDALIAN": "STATE",
    "STATUS": "STATE",
    "PUNYA": "TOOL",
    "TOOL": "TOOL",
    "ALAT": "TOOL",
    "PYTHON": "PYTHON",
    "PY": "PYTHON",
    "PYTON": "PYTHON",
    "JAVASCRIPT": "JAVASCRIPT",
    "JS": "JAVASCRIPT",
    "TYPESCRIPT": "TYPESCRIPT",
    "TS": "TYPESCRIPT",
    "JAVA": "JAVA",
    "C#": "CSHARP",
    "C-SHARP": "CSHARP",
    "CSHARP": "CSHARP",
    "CPP": "CPP",
    "C++": "CPP",
    "CPLUSPLUS": "CPP",
    "GOLANG": "GO",
    "GO": "GO",
    "RUST": "RUST",
    "PHP": "PHP",
    "SQL": "SQL",
    "RUBY": "RUBY",
    "SWIFT": "SWIFT",
    "KOTLIN": "KOTLIN",
    "R": "R",
    "NOTEPAD": "TOOL",
    "WINDOWS": "TOOL",
}


def load_vocab(vocab_path: Optional[Path | str] = None) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    path = Path(vocab_path) if vocab_path else DEFAULT_VOCAB_PATH
    if not path.exists():
        raise FileNotFoundError(f"Vocabulary not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        entries = json.load(f)

    by_name = {entry["name"].upper(): entry for entry in entries}
    by_id = {entry["id"]: entry for entry in entries}
    return by_name, by_id


def _clean_token(raw: str) -> str:
    return re.sub(r"[^A-Z0-9-]", "", re.sub(r"_", "-", raw.upper()))


def _normalize_numeric_token(raw: str) -> Optional[str]:
    if not raw:
        return None
    if re.fullmatch(r"\d+", raw):
        padded = raw.zfill(3)
        return padded if 1 <= int(padded) <= 999 else None
    return None


def _tokenize(text: str) -> List[str]:
    return [chunk for chunk in re.split(r"\s+", text.strip()) if chunk]


def _tokenize_human(text: str) -> List[str]:
    normalized = re.sub(r"\bC\s*\+\+\b", "C++", text.upper())
    normalized = re.sub(r"\bC\s*#\b", "C#", normalized)
    return [token for token in re.findall(r"[A-Z0-9#\+]+", normalized) if token]


def _resolve_token(
    token: str,
    by_name: Dict[str, Dict[str, Any]],
    by_id: Dict[str, Dict[str, Any]],
) -> Tuple[Optional[str], Optional[Dict[str, Any]], bool]:
    normalized = _clean_token(token)
    if not normalized:
        return None, None, True

    numeric = _normalize_numeric_token(normalized)
    if numeric and numeric in by_id:
        return by_id[numeric]["name"], by_id[numeric], True

    if normalized in by_name:
        return normalized, by_name[normalized], False

    return normalized, None, numeric is not None


def _is_action(entry: Dict[str, Any]) -> bool:
    primary_class = entry.get("primary_class")
    if primary_class in {"ACTION", "CONTROL"}:
        return True
    return entry.get("secondary_class") == "ACTION"


def _is_object(entry: Dict[str, Any]) -> bool:
    return entry.get("primary_class") == "OBJECT" or entry.get("secondary_class") == "OBJECT"


def _is_state(entry: Dict[str, Any]) -> bool:
    return entry.get("primary_class") == "STATE" or entry.get("secondary_class") == "STATE"


def _is_meta(entry: Dict[str, Any]) -> bool:
    return entry.get("primary_class") == "META"


def parse_symbolic(
    text: str,
    *,
    vocab_path: Optional[Path | str] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    by_name, by_id = load_vocab(vocab_path)
    tokens = _tokenize(text)

    parsed: Dict[str, Any] = {
        "version": version,
        "actions": [],
        "object": None,
        "target": None,
        "state": None,
        "priority": None,
        "confidence": None,
        "destination": None,
        "end": False,
        "errors": [],
    }

    i = 0
    while i < len(tokens):
        raw = tokens[i]
        name, entry, was_numeric = _resolve_token(raw, by_name, by_id)
        if entry is None:
            parsed["errors"].append({"code": "UNKNOWN_OPCODE", "value": raw})
            i += 1
            continue

        name = name.upper()
        if name == "END":
            parsed["end"] = True
            i += 1
            continue

        if name == "STATE" and parsed["object"] is None:
            parsed["object"] = name
            i += 1
            continue

        if name == "TARGET" and i + 1 < len(tokens):
            next_name, next_entry, _ = _resolve_token(tokens[i + 1], by_name, by_id)
            if next_entry is not None:
                parsed["target"] = next_name.upper()
            i += 2
            continue

        if _is_action(entry):
            parsed["actions"].append(name)
            i += 1
            continue

        if name in PRIORITY_TOKENS:
            parsed["priority"] = name
            i += 1
            continue

        if name == "CONFIDENCE":
            parsed["confidence"] = None
            if i + 1 < len(tokens):
                next_raw = tokens[i + 1]
                next_num = None
                try:
                    next_num = float(next_raw)
                except ValueError:
                    normalized = _clean_token(next_raw)
                    if normalized.isdigit():
                        next_num = float(normalized)
                if next_num is not None:
                    confidence = next_num
                    if confidence > 1:
                        confidence = confidence / 100.0
                    parsed["confidence"] = max(0.0, min(1.0, confidence))
                    i += 1
            i += 1
            continue

        if _is_object(entry):
            if parsed["object"] is None:
                parsed["object"] = name
            elif parsed["destination"] is None:
                parsed["destination"] = name
            i += 1
            continue

        if _is_state(entry) or name in STATE_TOKENS or name in TARGET_STATE_TOKENS:
            if name in TARGET_STATE_TOKENS and parsed["target"] is None:
                parsed["target"] = name
            elif parsed["state"] is None and name in {"READY", "ACTIVE", "IDLE", "BUSY", "DONE", "FAILED"}:
                parsed["state"] = name
            elif parsed["state"] is None:
                parsed["state"] = name
            i += 1
            continue

        if _is_meta(entry) and name in {"TRUE", "FALSE"}:
            if parsed["state"] is None:
                parsed["state"] = name
            i += 1
            continue

        if was_numeric and name:
            parsed["errors"].append({"code": "UNMAPPED_NUMERIC", "value": raw})

        i += 1

    if require_end and not parsed["end"]:
        parsed["errors"].append({"code": "END_MISSING", "value": "END"})

    return parsed


def parse_numeric(
    text: str,
    *,
    vocab_path: Optional[Path | str] = None,
    require_end: bool = False,
    version: str = VERSION,
) -> Dict[str, Any]:
    by_name, by_id = load_vocab(vocab_path)
    symbolic_tokens = []
    seen_error = False

    for raw in _tokenize(text):
        normalized = _clean_token(raw)
        if not normalized:
            continue
        if normalized.isdigit():
            token_id = normalized.zfill(3)
            if token_id in by_id:
                symbolic_tokens.append(by_id[token_id]["name"])
            else:
                seen_error = True
                break
        else:
            symbolic_tokens.append(normalized)

    if seen_error:
        return parse_symbolic(
            " ".join([raw for raw in _tokenize(text) if raw]),
            vocab_path=vocab_path,
            require_end=require_end,
            version=version,
        )

    return parse_symbolic(" ".join(symbolic_tokens), vocab_path=vocab_path, require_end=require_end, version=version)


def parse_human_instruction(
    text: str,
    *,
    vocab_path: Optional[Path | str] = None,
    require_end: bool = False,
    include_end: bool = True,
    version: str = VERSION,
) -> Dict[str, Any]:
    by_name, _ = load_vocab(vocab_path)
    tokens = _tokenize_human(text)

    symbolic_tokens: List[str] = []
    for token in tokens:
        if token in STOPWORDS:
            continue

        candidate = HUMAN_TO_VOCAB.get(token, token)
        if candidate in by_name:
            symbolic_tokens.append(candidate)
            continue

        if candidate in STOPWORDS or not candidate:
            continue

        normalized = _clean_token(candidate)
        if normalized in by_name and normalized not in STOPWORDS:
            symbolic_tokens.append(normalized)

    if include_end and (not symbolic_tokens or symbolic_tokens[-1] != "END"):
        symbolic_tokens.append("END")

    symbolic = " ".join(symbolic_tokens)
    return parse_symbolic(
        symbolic,
        vocab_path=vocab_path,
        require_end=require_end,
        version=version,
    )
