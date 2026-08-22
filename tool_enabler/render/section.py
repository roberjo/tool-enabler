"""Idempotently write a generated block into a possibly-existing file,
bracketed by markers, without touching any hand-written content around it.
"""

from __future__ import annotations

from pathlib import Path

BEGIN = "<!-- BEGIN TOOL-ENABLER (generated — do not edit by hand; run `tool-enabler build` to regenerate) -->"
END = "<!-- END TOOL-ENABLER -->"


def upsert_section(path: Path, body: str) -> bool:
    """Insert or replace the tool-enabler managed block in `path`.

    Returns True if the file's on-disk content changed.
    """
    block = f"{BEGIN}\n{body.rstrip()}\n{END}\n"

    if path.exists():
        original = path.read_text()
        start = original.find(BEGIN)
        end = original.find(END)
        if start != -1 and end != -1:
            new_content = original[:start] + block + original[end + len(END):].lstrip("\n")
        elif original.strip():
            new_content = original.rstrip("\n") + "\n\n" + block
        else:
            new_content = block
    else:
        new_content = block

    if path.exists() and path.read_text() == new_content:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new_content)
    return True
