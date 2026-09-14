"""Dong goi ban giao UI, doc thang tu cho that.

Vi sao co file nay: truoc day `docs/ui-handoff/files/` giu mot BAN SAO cua `index.html`,
`web.py` va cac anh. Ngay 13/09/2026 Dung sua anh trong thu muc do roi thac mac sao web khong
doi, vi web doc `python/assistant/static/`. Bo ban sao di, moi lan can gui thi dung script nay
dong goi lai tu cho that.

    python tools/goi_ui_handoff.py
"""
from __future__ import annotations

import pathlib
import zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
RA = ROOT / "docs" / "ui-handoff" / "Marou-UI-handoff.zip"

# {ten trong goi: duong dan that}
NOI_DUNG = {
    "README.md": ROOT / "docs" / "ui-handoff" / "README.md",
    "api-mau.json": ROOT / "docs" / "ui-handoff" / "api-mau.json",
    "files/index.html": ROOT / "python" / "assistant" / "static" / "index.html",
    "files/web.py": ROOT / "python" / "assistant" / "channels" / "web.py",
}
for p in sorted((ROOT / "python" / "assistant" / "static").glob("mascot*.png")):
    NOI_DUNG[f"files/{p.name}"] = p


def main() -> None:
    thieu = [str(v) for v in NOI_DUNG.values() if not v.exists()]
    if thieu:
        raise SystemExit("Thieu tep: " + ", ".join(thieu))
    RA.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(RA, "w", zipfile.ZIP_DEFLATED) as z:
        for ten, duong in NOI_DUNG.items():
            z.write(duong, ten)
            print(f"  {ten:28s} <- {duong.relative_to(ROOT)}")
    print(f"\n{RA.relative_to(ROOT)}  {RA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
