#!/usr/bin/env python3
"""Linter AL toi thieu, chay khi khong co AL compiler va khong co symbol tu sandbox.

Khong thay the duoc AL compiler. No chi bat cac loi thuong gap ma doc bang mat de sot:
  1. Lech begin/end, ngoac nhon, ngoac tron
  2. Trung id object, trung id va ten field trong cung table, trung value trong cung enum
  3. Object id nam ngoai idRanges khai bao trong app.json
  4. Tham chieu toi object ten NWV... chua duoc khai bao o dau
  5. Dung ::GiaTri cua enum minh tu dinh nghia ma gia tri do khong ton tai
  6. Dung ten field tren bien record kieu table cua minh ma field do khong ton tai
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RECORD_METHODS = {
    "init", "insert", "modify", "delete", "deleteall", "get", "getrecordonce", "getbysystemid",
    "find", "findset", "findfirst", "findlast", "next", "reset", "setrange", "setfilter",
    "setcurrentkey", "count", "countapprox", "isempty", "calcfields", "calcsums", "setloadfields",
    "validate", "testfield", "fieldactive", "fieldname", "fieldcaption", "fieldno", "fielderror",
    "recordid", "systemid", "tablename", "tablecaption", "getfilter", "getfilters", "getview",
    "setview", "copy", "copyfilter", "copyfilters", "setrecfilter", "modifyall", "rename",
    "transferfields", "setascending", "ascending", "changecompany", "currentcompany", "mark",
    "markedonly", "clearmarks", "setposition", "getposition", "hasfilter", "filtergroup",
    "readpermission", "writepermission", "addlink", "locktable", "setautocalcfields",
    "deleteallexceptheader", "getascending", "issuesuspended", "readisolation", "securityfiltering",
}

OBJ = re.compile(r'^\s*(table|page|codeunit|enum|permissionset|report|query|xmlport|profile|'
                 r'pageextension|tableextension|enumextension|interface|controladdin|entitlement)\s+'
                 r'(\d+)?\s*"?([^"\r\n{]+?)"?\s*(?:extends\s+"?([^"\r\n{]+?)"?)?\s*$', re.I | re.M)
FIELD = re.compile(r'^\s*field\((\d+);\s*("?)([^;"]+)\2\s*;\s*([^)]+)\)', re.M)
ENUMVAL = re.compile(r'^\s*value\((\d+);\s*("?)([^;")]+)\2\s*\)', re.M)
VARDECL = re.compile(r'^\s*(\w+)\s*:\s*Record\s+("([^"]+)"|(\w+))\s*(?:temporary)?\s*;', re.M | re.I)
QUOTED = re.compile(r'"([^"\n]+)"')


def strip_noise(src: str) -> str:
    """Bo comment va noi dung chuoi, giu do dai dong de bao so dong dung."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "'":                      # chuoi AL
            out.append(" ")
            i += 1
            while i < n:
                if src[i] == "'":
                    if i + 1 < n and src[i + 1] == "'":
                        out.append("  ")
                        i += 2
                        continue
                    break
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            out.append(" ")
            i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "/":
            while i < n and src[i] != "\n":
                out.append(" ")
                i += 1
        elif c == "/" and i + 1 < n and src[i + 1] == "*":
            while i < n and not (src[i] == "*" and i + 1 < n and src[i + 1] == "/"):
                out.append("\n" if src[i] == "\n" else " ")
                i += 1
            out.append("  ")
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def check_balance(path: Path, clean: str, errs: list[str]) -> None:
    for open_t, close_t, label in (("{", "}", "ngoặc nhọn"), ("(", ")", "ngoặc tròn")):
        d = clean.count(open_t) - clean.count(close_t)
        if d:
            errs.append(f"{path.name}: lệch {label}, thừa {abs(d)} dấu {open_t if d > 0 else close_t}")
    toks = re.findall(r"\b(begin|end|case|repeat|until)\b", clean, re.I)
    depth = 0
    for t in toks:
        t = t.lower()
        if t in ("begin", "case"):
            depth += 1
        elif t == "end":
            depth -= 1
            if depth < 0:
                errs.append(f"{path.name}: có 'end' thừa, không khớp begin hoặc case")
                depth = 0
    if depth:
        errs.append(f"{path.name}: thiếu {depth} 'end' để đóng begin hoặc case")


def main(roots: list[str]) -> int:
    errs: list[str] = []
    warns: list[str] = []
    objects: dict[tuple[str, str], Path] = {}          # (loai, ten) -> file
    obj_ids: dict[tuple[str, int], Path] = {}
    table_fields: dict[str, set[str]] = {}
    enum_values: dict[str, set[str]] = {}
    files: list[tuple[Path, str, str]] = []            # path, raw, clean
    ranges: dict[Path, list[tuple[int, int]]] = {}

    for root in roots:
        rp = Path(root)
        for app in rp.rglob("app.json"):
            cfg = json.loads(app.read_text(encoding="utf-8"))
            ranges[app.parent] = [(r["from"], r["to"]) for r in cfg.get("idRanges", [])]
        for f in sorted(rp.rglob("*.al")):
            raw = f.read_text(encoding="utf-8")
            files.append((f, raw, strip_noise(raw)))

    for path, raw, clean in files:
        check_balance(path, clean, errs)

        marks = [(m.start(), m) for m in OBJ.finditer(clean)]
        for idx, (start, m) in enumerate(marks):
            kind, oid, name, _ext = m.groups()
            end = marks[idx + 1][0] if idx + 1 < len(marks) else len(clean)
            body = clean[start:end]
            kind = kind.lower()
            name = (name or "").strip()
            key = (kind, name.lower())
            if key in objects:
                errs.append(f"{path.name}: trùng tên object {kind} \"{name}\" với {objects[key].name}")
            objects[key] = path
            if oid:
                idk = (kind, int(oid))
                if idk in obj_ids:
                    errs.append(f"{path.name}: trùng id {kind} {oid} với {obj_ids[idk].name}")
                obj_ids[idk] = path
                owner = next((p for p in ranges if p in path.parents), None)
                if owner and ranges[owner] and not any(a <= int(oid) <= b for a, b in ranges[owner]):
                    errs.append(f"{path.name}: id {oid} nằm ngoài idRanges khai báo trong app.json")

            if kind == "table":
                ids, names = defaultdict(int), defaultdict(int)
                for fid, _q, fname, _typ in FIELD.findall(body):
                    ids[int(fid)] += 1
                    names[fname.strip().lower()] += 1
                for fid, c in ids.items():
                    if c > 1:
                        errs.append(f"{path.name}: table \"{name}\" có {c} field cùng id {fid}")
                for fname, c in names.items():
                    if c > 1:
                        errs.append(f"{path.name}: table \"{name}\" có {c} field cùng tên {fname}")
                table_fields[name.lower()] = {f.strip().lower() for _i, _q, f, _t in FIELD.findall(body)}
            if kind == "enum":
                vids, vnames = defaultdict(int), defaultdict(int)
                for vid, _q, vname in ENUMVAL.findall(body):
                    vids[int(vid)] += 1
                    vnames[vname.strip().lower()] += 1
                for vid, c in vids.items():
                    if c > 1:
                        errs.append(f"{path.name}: enum \"{name}\" có {c} value cùng id {vid}")
                for vname, c in vnames.items():
                    if c > 1:
                        errs.append(f"{path.name}: enum \"{name}\" có {c} value cùng tên {vname}")
                enum_values[name.lower()] = {v.strip().lower() for _i, _q, v in ENUMVAL.findall(body)}

    declared = {n for _k, n in objects}

    for path, raw, clean in files:
        # tham chieu object NWV chua khai bao
        for q in set(QUOTED.findall(clean)):
            if q.upper().startswith("NWV ") and q.lower() not in declared:
                errs.append(f"{path.name}: nhắc tới object \"{q}\" mà không thấy khai báo ở đâu")

        # ten field tren bien record kieu table cua minh
        for var, _all, qname, bare in VARDECL.findall(clean):
            tname = (qname or bare or "").strip().lower()
            if tname not in table_fields:
                continue
            known = table_fields[tname]
            for m in re.finditer(rf'\b{re.escape(var)}\.("([^"\n]+)"|([A-Za-z_]\w*))', clean):
                fname = (m.group(2) or m.group(3) or "").strip().lower()
                if not fname or fname in known:
                    continue
                if fname in RECORD_METHODS:
                    continue
                errs.append(f"{path.name}: biến {var} kiểu \"{tname}\" dùng field {m.group(1)} không có trong table")

        # gia tri enum cua minh
        for ename, vals in enum_values.items():
            for m in re.finditer(r'::("([^"\n]+)"|([A-Za-z_]\w*))', clean):
                pass  # xu ly ben duoi theo bien
        for var, _all, qname, bare in re.findall(r'^\s*(\w+)\s*:\s*Enum\s+("([^"]+)"|(\w+))\s*;', clean, re.M | re.I):
            en = (qname or bare or "").strip().lower()
            if en not in enum_values:
                continue
            for m in re.finditer(rf'\b{re.escape(var)}::("([^"\n]+)"|([A-Za-z_]\w*))', clean):
                v = (m.group(2) or m.group(3) or "").strip().lower()
                if v not in enum_values[en]:
                    errs.append(f"{path.name}: enum \"{en}\" không có giá trị {m.group(1)}")

    print(f"Đã quét {len(files)} file AL, {len(objects)} object.")
    for w in warns:
        print("  cảnh báo:", w)
    if errs:
        print(f"\n{len(errs)} vấn đề:")
        for e in errs:
            print("  -", e)
        return 1
    print("Không thấy vấn đề nào trong phạm vi linter kiểm được.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or ["."]))
