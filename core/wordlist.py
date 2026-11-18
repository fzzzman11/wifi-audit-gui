"""Generación y guardado de diccionarios personalizados.

Dado un conjunto de palabras base y una serie de reglas (mayúsculas, números,
años, leet…), se construye un diccionario de texto con un límite máximo de
palabras. Los archivos se guardan en ``DICTIONARIES_DIR`` para que la pantalla
de análisis pueda reutilizarlos como wordlist de aircrack-ng.
"""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from .constants import DICTIONARIES_DIR

RULE_LABELS = {
    "original": "Palabras originales",
    "capitalize": "Inicial mayúscula",
    "upper": "Todo en mayúsculas",
    "leet": "Sustitución leet (a→4, e→3…)",
    "years": "Añadir años",
    "numbers": "Añadir números",
    "symbols": "Añadir símbolos",
}

_LEET_MAP = str.maketrans(
    {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5"}
)


def _year_suffixes() -> list[str]:
    current = datetime.now().year
    return [str(year) for year in range(current - 35, current + 1)]


def _number_suffixes() -> list[str]:
    suffixes: list[str] = []
    for number in range(100):
        suffixes.append(str(number))
        suffixes.append(f"{number:02d}")
    suffixes.extend(("123", "1234", "12345"))
    return suffixes


_SYMBOLS = ("!", "?", "@", "#", "*", "!!", "123!", "2024!")


def clean_words(raw: str) -> list[str]:
    """extrae palabras no vacías y elimina repetidos sin perder el orden."""
    words: list[str] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        word = line.strip()
        if not word:
            continue
        key = word.casefold()
        if key in seen:
            continue
        seen.add(key)
        words.append(word)
    return words


def _candidates(word: str, rule: str) -> list[str]:
    if rule == "original":
        return [word]
    if rule == "capitalize":
        return [word.capitalize()]
    if rule == "upper":
        return [word.upper()]
    if rule == "leet":
        return [word.translate(_LEET_MAP), word.capitalize().translate(_LEET_MAP)]
    if rule == "years":
        return [f"{word}{suffix}" for suffix in _year_suffixes()]
    if rule == "numbers":
        return [f"{word}{suffix}" for suffix in _number_suffixes()]
    if rule == "symbols":
        return [f"{word}{suffix}" for suffix in _SYMBOLS]
    return []


def generate_words(
    base_words: list[str],
    rules: dict[str, bool],
    max_words: int,
    progress: Callable[[int, int], None] | None = None,
    stop_check: Callable[[], bool] | None = None,
) -> list[str]:
    """Genera variantes en capas y respeta el límite ``max_words``.

    Se procesa una regla para todas las palabras antes de pasar a la siguiente,
    de modo que con límites bajos aparecen primero las formas básicas de todas
    las palabras introducidas.
    """
    limit = max(1, int(max_words))
    active = [rule for rule in RULE_LABELS if rules.get(rule, False)]
    if "original" not in active:
        active.insert(0, "original")

    words: list[str] = []
    seen: set[str] = set()
    total_layers = len(active)

    def add(candidate: str) -> bool:
        if not candidate or candidate in seen or len(words) >= limit:
            return len(words) < limit
        seen.add(candidate)
        words.append(candidate)
        return True

    for index, rule in enumerate(active, 1):
        for base in base_words:
            if stop_check and stop_check():
                return words
            for candidate in _candidates(base, rule):
                if not add(candidate):
                    if progress:
                        progress(index, total_layers)
                    return words
        if progress:
            progress(index, total_layers)
    return words


def safe_filename(name: str) -> str:
    """Convierte un nombre libre en un nombre de archivo seguro."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", name.strip()).strip("_")
    return cleaned or "diccionario"


def wordlist_path(name: str) -> Path:
    return DICTIONARIES_DIR / f"{safe_filename(name)}.txt"


def save_wordlist(
    name: str,
    words: list[str],
    base_words: list[str],
    rules: dict[str, bool],
    max_words: int,
) -> Path:
    """Escribe el diccionario y un archivo JSON con sus metadatos."""
    DICTIONARIES_DIR.mkdir(parents=True, exist_ok=True)
    stem = safe_filename(name)
    txt_path = DICTIONARIES_DIR / f"{stem}.txt"
    txt_path.write_text("\n".join(words) + "\n", encoding="utf-8")

    metadata = {
        "name": name.strip() or stem,
        "created": datetime.now().isoformat(timespec="seconds"),
        "count": len(words),
        "max_words": int(max_words),
        "base_words": base_words,
        "rules": {key: bool(value) for key, value in rules.items()},
    }
    txt_path.with_suffix(".json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return txt_path


def _count_words(path: Path) -> int:
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            return sum(1 for line in handle if line.strip())
    except OSError:
        return 0


def list_wordlists() -> list[dict]:
    """Devuelve los diccionarios guardados, ordenados por fecha de creación."""
    if not DICTIONARIES_DIR.is_dir():
        return []

    items: list[dict] = []
    for path in DICTIONARIES_DIR.glob("*.txt"):
        metadata: dict = {}
        try:
            metadata = json.loads(
                path.with_suffix(".json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            pass

        items.append(
            {
                "path": str(path),
                "name": metadata.get("name") or path.stem,
                "count": metadata.get("count") or _count_words(path),
                "created": metadata.get("created", ""),
                "base_words": metadata.get("base_words", []),
                "rules": metadata.get("rules", {}),
            }
        )
    items.sort(key=lambda item: (item["created"], item["name"]), reverse=True)
    return items


def delete_wordlist(path: str | Path) -> None:
    """Borra un diccionario y sus metadatos, solo dentro de DICTIONARIES_DIR."""
    target = Path(path).resolve()
    if target.parent != DICTIONARIES_DIR.resolve():
        raise ValueError("El archivo no pertenece a la carpeta de diccionarios.")
    target.unlink(missing_ok=True)
    target.with_suffix(".json").unlink(missing_ok=True)


class WordlistWorker(QThread):
    """Genera y guarda el diccionario en segundo plano."""

    progress = pyqtSignal(int, int)  # capa actual, capas totales
    log = pyqtSignal(str)
    finished_generated = pyqtSignal(str, int)  # ruta, número de palabras
    error = pyqtSignal(str)

    def __init__(
        self,
        name: str,
        base_words: list[str],
        rules: dict[str, bool],
        max_words: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.name = name
        self.base_words = base_words
        self.rules = rules
        self.max_words = max_words
        self._stop_event = threading.Event()

    def request_stop(self) -> None:
        self._stop_event.set()

    def _report_progress(self, done: int, total: int) -> None:
        if not self._stop_event.is_set():
            self.progress.emit(done, total)

    def run(self) -> None:
        try:
            words = generate_words(
                self.base_words,
                self.rules,
                self.max_words,
                progress=self._report_progress,
                stop_check=self._stop_event.is_set,
            )
            if self._stop_event.is_set():
                self.log.emit("Generación cancelada.")
                return
            path = save_wordlist(
                self.name, words, self.base_words, self.rules, self.max_words
            )
            self.log.emit(
                f"Guardado {path.name} con {len(words):,} palabras."
            )
            self.finished_generated.emit(str(path), len(words))
        except OSError as exc:
            self.error.emit(f"No se pudo guardar el diccionario: {exc}")
        except Exception as exc:
            self.error.emit(f"Error al generar el diccionario: {exc}")
