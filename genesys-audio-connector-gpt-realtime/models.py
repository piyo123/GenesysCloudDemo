import websockets
import asyncio
from dataclasses import dataclass
from typing import Optional
from openai import AsyncAzureOpenAI
from openai.resources.realtime.realtime import AsyncRealtimeConnection

@dataclass
class kazSession:
    genesysConversationId: str
    audio_connector_ws: Optional[websockets.ServerConnection] = None
    serverSequence: Optional[int] = 1
    audio_tobe_sent_to_genesys: Optional[asyncio.Queue] = None
    send_audio_to_genesys_task: Optional[asyncio.Task] = None
    send_data_to_openai_task: Optional[asyncio.Task] = None
    openai_connection: Optional[AsyncRealtimeConnection] = None
    openai_ws_event_handle_task: Optional[asyncio.Task] = None
    openai_new_conversation: Optional[bool] = True
