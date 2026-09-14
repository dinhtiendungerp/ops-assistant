"""Kenh Teams: khung Bot Framework. CHUA CHAY, can Azure Bot registration.

Can gi de chay:
  pip install botbuilder-core botbuilder-integration-aiohttp botbuilder-schema
  Azure: tao Azure Bot (single tenant), lay MicrosoftAppId / MicrosoftAppPassword / MicrosoftAppTenantId,
         Messaging endpoint = https://<host>/api/messages, bat channel Teams.
  Teams app manifest: bot id = MicrosoftAppId, scope personal + team.
  SSO cho danh tinh nguoi duyet: cau hinh OAuth connection tren Azure Bot (Entra), bot goi
  GetUserToken -> doi lay token BC bang on-behalf-of (scope https://api.businesscentral.dynamics.com/.default),
  roi BCGateway.approve(...) chay voi token do thay vi token app. (TODO trong gateway.approve)

Cach map: activity.text -> Assistant.handle_message ; Action.Execute (invoke adaptiveCard/action) -> Assistant.handle_action.
Delivery -> proactive message toi user theo conversation reference da luu khi user lan dau nhan tin.
"""
from __future__ import annotations

import logging
from typing import Any

from ..core import Assistant
from ..skills import Delivery

log = logging.getLogger("teams")

try:  # thu vien tuy chon
    from botbuilder.core import ActivityHandler, MessageFactory, TurnContext  # type: ignore
    from botbuilder.schema import Activity, Attachment, ConversationReference  # type: ignore
    HAVE_BOTBUILDER = True
except Exception:  # pragma: no cover
    HAVE_BOTBUILDER = False


class TeamsChannel:
    """Giu conversation reference theo user de gui proactive."""

    def __init__(self, assistant: Assistant):
        self.asst = assistant
        self.refs: dict[str, Any] = {}          # user_id -> ConversationReference
        self.aad_to_user: dict[str, str] = {}   # aadObjectId -> user_id (tu bang identity_map)

    def resolve_user(self, aad_object_id: str, display_name: str) -> str:
        """Map tai khoan Teams -> user cua tro ly. POC: theo bang users (bc_user hoac display name)."""
        if aad_object_id in self.aad_to_user:
            return self.aad_to_user[aad_object_id]
        for u in self.asst.mem.users():
            if u["display_name"].split(" (")[0].lower() in display_name.lower():
                self.aad_to_user[aad_object_id] = u["user_id"]
                return u["user_id"]
        return aad_object_id

    @staticmethod
    def to_attachment(d: Delivery) -> dict[str, Any]:
        return {"contentType": "application/vnd.microsoft.card.adaptive", "content": d.card.to_adaptive_card()} if d.card else {}


if HAVE_BOTBUILDER:

    class OpsAssistantBot(ActivityHandler):  # pragma: no cover - can Azure Bot de chay
        def __init__(self, channel: TeamsChannel):
            self.ch = channel

        async def on_message_activity(self, turn_context: TurnContext):
            uid = self.ch.resolve_user(turn_context.activity.from_property.aad_object_id, turn_context.activity.from_property.name)
            self.ch.refs[uid] = TurnContext.get_conversation_reference(turn_context.activity)
            out = self.ch.asst.handle_message(uid, turn_context.activity.text or "")
            await self._deliver(turn_context, uid, out)

        async def on_invoke_activity(self, turn_context: TurnContext):
            # Action.Execute tu Adaptive Card: activity.name == "adaptiveCard/action", value = {"action": {"verb", "data"}}
            v = turn_context.activity.value or {}
            action = v.get("action", {})
            uid = self.ch.resolve_user(turn_context.activity.from_property.aad_object_id, turn_context.activity.from_property.name)
            data = dict(action.get("data", {}))
            ref = data.pop("ref", "")
            # input fields cua card den trong v["action"]["data"] hoac v["inputs"] tuy client; gop ca hai
            for k, val in (v.get("inputs") or {}).items():
                data[k.split("_", 1)[-1]] = val
            out = self.ch.asst.handle_action(uid, action.get("verb", ""), ref, data)
            await self._deliver(turn_context, uid, out)
            return self._invoke_response()

        async def _deliver(self, turn_context: TurnContext, current_uid: str, out: list[Delivery]):
            for d in out:
                msg = MessageFactory.attachment(Attachment(**self.ch.to_attachment(d))) if d.card else MessageFactory.text(d.text)
                if d.user_id == current_uid:
                    await turn_context.send_activity(msg)
                elif d.user_id in self.ch.refs:
                    async def _send(ctx: TurnContext, m=msg):
                        await ctx.send_activity(m)
                    await turn_context.adapter.continue_conversation(self.ch.refs[d.user_id], _send, bot_app_id=turn_context.adapter.settings.app_id)
                else:
                    log.warning("Khong co conversation reference cho %s; tin bi giu lai trong inbox", d.user_id)

        @staticmethod
        def _invoke_response():
            from botbuilder.schema import InvokeResponse  # type: ignore
            return InvokeResponse(status=200, body={"statusCode": 200, "type": "application/vnd.microsoft.activity.message", "value": "OK"})
