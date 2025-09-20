# Ideally managed by Redis or similar, but since this is a single server, using in-memory storage for simplicity.

import asyncio
from typing import Dict
from models import kazSession

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, kazSession] = {}

    def get_or_create(self, genesysConversationId: str) -> kazSession:
        if genesysConversationId not in self.sessions:
            self.sessions[genesysConversationId] = kazSession(genesysConversationId = genesysConversationId)
            self.sessions[genesysConversationId].audio_tobe_sent_to_genesys = asyncio.Queue()
        return self.sessions[genesysConversationId]

    def remove(self, genesysConversationId: str):
        if genesysConversationId in self.sessions:
            del self.sessions[genesysConversationId]

session_manager = SessionManager() # shared across the entire app
