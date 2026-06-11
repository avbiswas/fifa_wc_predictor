from __future__ import annotations

import os
import re

from dotenv import load_dotenv

from .paths import ROOT


def load_env() -> None:
    load_dotenv(ROOT / ".env")
    envrc = ROOT / ".envrc"
    if not envrc.exists():
        return
    for line in envrc.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\s*export\s+([A-Za-z_][A-Za-z0-9_]*)=(.*)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        os.environ.setdefault(key, value.strip().strip("\"'"))
