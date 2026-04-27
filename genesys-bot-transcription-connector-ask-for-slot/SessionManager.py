# 本来は Redis などで管理するべきだが、簡単のためメモリ上で管理する。（単一サーバー）

import asyncio
from typing import Dict
from models import kazSession

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, kazSession] = {}

    def get_or_create(self, genesysConversationId: str) -> kazSession:
        if genesysConversationId not in self.sessions:
            self.sessions[genesysConversationId] = kazSession(genesysConversationId = genesysConversationId)
        return self.sessions[genesysConversationId]

    def remove(self, genesysConversationId: str):
        if genesysConversationId in self.sessions:
            del self.sessions[genesysConversationId]

session_manager = SessionManager() # share within entire app
