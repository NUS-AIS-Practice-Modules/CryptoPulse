import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from datetime import datetime, timezone
from shared.types import Conversation, ChatMessage


class ConversationStore:
    def __init__(self) -> None:
        self._store: dict[str, Conversation] = {}

    def get_or_create(self, conv_id: str) -> Conversation:
        if conv_id not in self._store:
            self._store[conv_id] = Conversation(id=conv_id)
        return self._store[conv_id]

    def append_turn(self, conv_id: str, user_content: str, assistant_content: str) -> None:
        conv = self.get_or_create(conv_id)
        conv.messages.append(ChatMessage(role="user", content=user_content, timestamp=datetime.now(timezone.utc)))
        conv.messages.append(ChatMessage(role="assistant", content=assistant_content, timestamp=datetime.now(timezone.utc)))

    def get_recent_messages(self, conv_id: str, n: int) -> list[dict]:
        conv = self._store.get(conv_id)
        if not conv:
            return []
        # n turns = n*2 messages (user + assistant per turn)
        recent = conv.messages[-(n * 2):]
        return [{"role": m.role, "content": m.content} for m in recent]


conversation_store = ConversationStore()
