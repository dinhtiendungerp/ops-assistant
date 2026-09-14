"""The (card) tro ly gui: mot model, hai cach render.
  to_adaptive_card(): JSON Adaptive Card 1.5 cho Teams (Action.Execute -> bot nhan verb + data)
  Web demo render tu dict nay bang JS o static/index.html
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Action:
    id: str              # verb: approve, edit, reject, ship, ...
    label: str
    style: str = "default"   # default | positive | destructive
    payload: dict[str, Any] = field(default_factory=dict)
    needs_input: str | None = None   # ten field nhap them (vi du "quantity", "reason")


@dataclass
class Card:
    title: str
    body: str = ""
    facts: list[tuple[str, str]] = field(default_factory=list)
    actions: list[Action] = field(default_factory=list)
    ref: str = ""
    kind: str = "proposal"   # proposal | info | question | brief
    # Lien ket mo thang trang Business Central da loc san (label, url). Tu 14/09/2026, theo UC10 cua RFP ("dashboard
    # links"): moi con so tro ly noi phai mo duoc cho goc trong BC de doi chieu.
    links: list[tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "ref": self.ref, "title": self.title, "body": self.body,
            "facts": [{"label": l, "value": v} for l, v in self.facts],
            "actions": [{"id": a.id, "label": a.label, "style": a.style, "payload": a.payload, "needs_input": a.needs_input} for a in self.actions],
            "links": [{"label": l, "url": u} for l, u in self.links if u],
        }

    def to_adaptive_card(self) -> dict[str, Any]:
        body: list[dict[str, Any]] = [{"type": "TextBlock", "text": self.title, "weight": "Bolder", "size": "Medium", "wrap": True}]
        if self.body:
            body.append({"type": "TextBlock", "text": self.body, "wrap": True})
        if self.facts:
            body.append({"type": "FactSet", "facts": [{"title": l, "value": v} for l, v in self.facts]})
        actions = []
        for a in self.actions:
            if a.needs_input:
                body.append({"type": "Input.Text", "id": f"{a.id}_{a.needs_input}", "placeholder": a.needs_input})
            actions.append({"type": "Action.Execute", "verb": a.id, "title": a.label,
                            "style": a.style if a.style != "default" else "default", "data": {"ref": self.ref, **a.payload}})
        actions += [{"type": "Action.OpenUrl", "title": l, "url": u} for l, u in self.links if u]
        return {"type": "AdaptiveCard", "$schema": "http://adaptivecards.io/schemas/adaptive-card.json", "version": "1.5",
                "body": body, "actions": actions}


def fmt_qty(q: float) -> str:
    return f"{int(q)}" if float(q).is_integer() else f"{q:.1f}"


def fmt_vnd(v: float) -> str:
    """Gia tri theo don vi tien cua company, kieu Viet: cham ngan cach nghin, phay thap phan.
    Khong ghi ten don vi vi company NWV dung gia von kieu Cronus (mot mon tu 0,45 den 7,5),
    khong phai dong Viet Nam. Ten ham giu nguyen de khong phai sua moi cho goi."""
    s = f"{v:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return s[:-3] if s.endswith(",00") else s
