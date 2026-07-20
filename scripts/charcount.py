"""한국어 글자수 계산 — 공백 포함/제외 모두 출력. 채용 포털 기준 차이 대응."""
import re
import sys

CLAIM_RE = re.compile(r"<!--c:[^>]*-->")
HEADING_RE = re.compile(r"^#+ .*$", re.MULTILINE)


def _clean(text: str) -> str:
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
    parts = re.split(r"^## (문항 \d+\..*)$", md_text, flags=re.MULTILINE)
    out = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1]))
    return out


def main(path: str) -> int:
    md = open(path, encoding="utf-8").read()
    qs = split_questions(md) or [("전체", md)]
    print(f"{'문항':<30}{'공백포함':>10}{'공백제외':>10}")
    for title, body in qs:
        c = count_section(body)
        print(f"{title:<30}{c['with_spaces']:>10}{c['without_spaces']:>10}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
