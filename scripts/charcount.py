"""한국어 글자수 계산 — 공백 포함/제외 모두 출력. 채용 포털 기준 차이 대응."""

import re
import sys
from pathlib import Path

CLAIM_RE = re.compile(r"<!--\s*c\s*:[\s\S]*?-->", re.IGNORECASE)
HEADING_RE = re.compile(r"^#+ .*$", re.MULTILINE)


def _clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = CLAIM_RE.sub("", text)
    text = HEADING_RE.sub("", text)
    return text.strip()


def count_section(text: str) -> dict:
    t = _clean(text)
    no_newline = t.replace("\n", "")
    return {
        "with_spaces": len(no_newline),
        "without_spaces": len(re.sub(r"\s", "", t)),
    }


def split_questions(md_text: str) -> list:
    md_text = md_text.replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(
        r"^## ((?:Q-\d{2,}\b|문항 \d+\.|Question \d+\.).*)$", md_text, flags=re.MULTILINE
    )
    out = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1]))
    return out


def main(path: str) -> int:
    md = Path(path).read_text(encoding="utf-8")
    qs = split_questions(md) or [("전체", md)]
    print(f"{'문항':<30}{'공백포함':>10}{'공백제외':>10}")
    for title, body in qs:
        c = count_section(body)
        print(f"{title:<30}{c['with_spaces']:>10}{c['without_spaces']:>10}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))


def count_units(text, unit, newline_policy="exclude"):
    """Approximate counts; portal counter is authoritative."""
    if newline_policy not in {"exclude", "include"}:
        raise ValueError("Invalid newline policy")
    clean = _clean(text)
    if unit == "words":
        return len(clean.split())
    if newline_policy == "exclude":
        clean = clean.replace("\n", "")
    if unit == "characters_with_spaces":
        return len(clean)
    if unit == "characters_without_spaces":
        return len(re.sub(r"\s", "", clean))
    if unit == "utf8_bytes":
        return len(clean.encode("utf-8"))
    if unit == "utf16_units":
        return len(clean.encode("utf-16-le")) // 2
    raise ValueError(f"Unsupported length unit: {unit}")
