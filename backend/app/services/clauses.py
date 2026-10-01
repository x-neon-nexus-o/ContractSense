"""Conservative clause segmentation; page numbers are preserved when available."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass
class Clause:
    id: str
    title: str
    text: str
    page: int

    def as_dict(self):
        return asdict(self)


# Only the section/article/clause keywords are case-insensitive. The bare
# all-caps alternative intentionally remains case-sensitive so ordinary prose
# is not promoted to headings merely because it starts with a capital letter.
_HEADING = re.compile(
    r"^\s*(?:(?i:section|article|clause)\s+[\w.-]+|\d{1,3}(?:\.\d{1,3}){0,4}[.)]?\s+[^\n]{2,120}|[A-Z][A-Z0-9 /&,'()-]{5,90})\s*$"
)


def segment_clauses(pages: list[dict], max_chars: int = 3600) -> list[Clause]:
    blocks: list[tuple[int, str, str]] = []
    for page_data in pages:
        page = int(page_data.get("page", 1))
        raw = str(page_data.get("text", ""))
        lines = [re.sub(r"\s+", " ", x).strip() for x in raw.splitlines()]
        lines = [x for x in lines if x]
        if not lines:
            continue
        current_title = ""
        current: list[str] = []
        for line in lines:
            if _HEADING.match(line) and len(line) <= 125:
                if current:
                    blocks.append((page, current_title, " ".join(current)))
                current_title = line.strip(" .")
                current = []
                continue
            if current and len(" ".join(current)) + len(line) > max_chars:
                blocks.append((page, current_title, " ".join(current)))
                current = []
            current.append(line)
        if current:
            blocks.append((page, current_title, " ".join(current)))

    # If a long page had no headings, paragraph-aware segmentation is a better fallback.
    if len(blocks) <= 1:
        text = "\n".join(str(p.get("text", "")) for p in pages)
        paragraphs = [re.sub(r"\s+", " ", p).strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        blocks = []
        buffer = ""
        page = 1
        for para in paragraphs:
            if len(buffer) + len(para) > max_chars and buffer:
                blocks.append((page, "", buffer))
                buffer = ""
            buffer = f"{buffer} {para}".strip()
        if buffer:
            blocks.append((page, "", buffer))

    output: list[Clause] = []
    for i, (page, title, text) in enumerate(blocks, start=1):
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 35:
            continue
        output.append(Clause(id=f"clause-{i:04d}", title=title[:160], text=text[:max_chars], page=page))
    if not output:
        text = re.sub(r"\s+", " ", " ".join(str(p.get("text", "")) for p in pages)).strip()
        if text:
            output = [Clause(id="clause-0001", title="Document text", text=text[:max_chars], page=1)]
    return output[:500]
