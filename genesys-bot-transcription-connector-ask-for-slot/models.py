import websockets
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict
from openai.resources.realtime.realtime import AsyncRealtimeConnection

@dataclass
class kazSession:
    genesysConversationId: str | None = None
    bot_transcription_connector_ws: websockets.ServerConnection | None = None
    serverSequence: int = 1
    clientSequence: int | None = None
    sessionId: str | None = None
    speechDetected: bool = False
    transcriptionCompleted: bool = False
    transriptionData: Dict | None = None
    send_data_to_openai_task: asyncio.Task | None = None
    openai_connection: AsyncRealtimeConnection | None = None
    openai_ws_event_handle_task: asyncio.Task | None = None
    openai_new_conversation: bool = True


