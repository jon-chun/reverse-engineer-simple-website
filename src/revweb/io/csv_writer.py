from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class CsvSpec:
    path: Path
    fieldnames: list[str]


class StreamingCsvWriter:
    def __init__(self, spec: CsvSpec):
        self.spec = spec
        self._file = None
        self._writer: csv.DictWriter | None = None
        self._opened = False

    def open(self) -> None:
        self.spec.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.spec.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.spec.fieldnames)
        self._writer.writeheader()
        self._opened = True

    def write_row(self, row: dict[str, Any]) -> None:
        if not self._opened:
            self.open()
        assert self._writer is not None
        self._writer.writerow({k: row.get(k, "") for k in self.spec.fieldnames})

    def close(self) -> None:
        if self._file:
            self._file.close()
        self._opened = False
