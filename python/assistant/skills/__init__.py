"""Skill = ham nhan (assistant, user, intent/action) va tra ve danh sach Delivery."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..cards import Card


@dataclass
class Delivery:
    """Mot tin tro ly gui cho mot nguoi. Channel layer se render theo kenh."""
    user_id: str
    text: str
    card: Card | None = None
    skill: str = ""
    ref: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
