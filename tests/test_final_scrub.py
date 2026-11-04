import sys
import pathlib
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "scripts"))
import final_scrub
from final_scrub import visible_text


def test_visible_text_ignores_invisible_format_chars(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("설비를​ 점검했습니다.‍", encoding="utf-8")
    b.write_text("설비를 점검했습니다.", encoding="utf-8")
    assert visible_text(a) == visible_text(b)


def test_visible_text_detects_real_change(tmp_path):
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("설비를 점검했습니다.", encoding="utf-8")
    b.write_text("설비를 보수했습니다.", encoding="utf-8")
    assert visible_text(a) != visible_text(b)


def test_visible_text_reads_docx_body(tmp_path):
    p = tmp_path / "x.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr(
            "word/document.xml",
            '<w:document><w:p><w:r><w:t xml:space="preserve">가 &amp; 나</w:t></w:r></w:p></w:document>',
        )
    assert visible_text(p) == "가 & 나"


def test_missing_tool_returns_install_hint(tmp_path, monkeypatch, capsys):
    (tmp_path / "output").mkdir()
    monkeypatch.setattr(
        sys, "argv", ["final_scrub.py", str(tmp_path), "--tool-dir", str(tmp_path / "none")]
    )
    assert final_scrub.main() == 2
    assert final_scrub.PINNED_COMMIT in capsys.readouterr().out
