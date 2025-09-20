import asyncio
import websockets
import base64
from environvars import env
from openai import AsyncAzureOpenAI
from models import kazSession
from SessionManager import session_manager
from openai.resources.realtime.realtime import AsyncRealtimeConnection

####################################################################
# get or create websocket connection to OpenAI
####################################################################
async def get_or_create_openai_connection(genesysConversationId: str) -> AsyncRealtimeConnection:
    
    print("[OPENAI] ********* get_or_create_openai_connection started ************")

    try:
        # check if websocket connection to OpenAI already exists
        session = session_manager.get_or_create(genesysConversationId) # session corresponding genesys conversation id should exists
        if session.openai_connection is None:

            print("[OPENAI] CREATE NEW OPENAI CONNECTION")

            client = AsyncAzureOpenAI(
                azure_endpoint = env.AZURE_OPENAI_ENDPOINT,
                azure_deployment = env.AZURE_OPENAI_DEPLOYMENT,
                api_key = env.AZURE_OPENAI_API_KEY,
                api_version = env.AZURE_OPENAI_API_VERSION,
            )

            # create connection
            context_manager = client.realtime.connect(model=f"{env.AZURE_OPENAI_DEPLOYMENT}")
            connection = await context_manager.__aenter__()

            # configuration
            await connection.session.update(
                session = { 
                    "voice": env.AZURE_OPENAI_VOICE, 
                    "modalities": ["text", "audio"], 
                    "input_audio_format": "g711_ulaw",  # audio format of data from Genesys Cloud
                    "output_audio_format": "g711_ulaw", # audio format of data sent to Genesys Cloud (options: g711_ulaw/g711_alaw/pcm16)
                    "temperature": env.AZURE_OPENAI_TEMPERATURE,
                    "turn_detection": {
                        "type": env.AZURE_OPENAI_VAD_TYPE,                                   # server_vad or semantic_vad https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio#voice-activity-detection-vad-and-the-audio-buffer
                        "threshold": env.AZURE_OPENAI_VAD_SENSITIVITY,                       # Voice detection sensitivity (0.0 - 1.0)
                        "prefix_padding_ms": env.AZURE_OPENAI_PREFIX_PADDING_MS,             # Amount of audio to keep before speech starts (ms)
                        "silence_duration_ms": env.AZURE_OPENAI_SILENCE_DURATION_MS,         # Duration considered as silence (ms)
                        "create_response": env.AZURE_OPENAI_CREATE_RESPONSE,                 # Automatically generate response on detection (True/False)
                        "interrupt_response": env.AZURE_OPENAI_INTERRUPT_RESPONSE            # Allow interrupts (True/False)
                    },
                    "tools": [], # MCP, etc. https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio#mcp-server-support
                    "instructions": env.AZURE_OPENAI_INSTRUCTIONS
                }
            )

            print("[OEPNAI] CONNECTED")
            
        else:
            # get existing connection 
            print("[OPENAI] FOUND EXISTING OPENAI CONNECTION")
            connection = session.openai_connection
    
        return connection

    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[OPENAI CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[OPENAI ERROR & CLOSED] {e.code}:{e.reason}")
        return None
    #finally:

####################################################################    
# send aduio/text data to OpenAI
####################################################################
async def send_data_to_openai(session: kazSession, audiodata: bytes):

    connection = session.openai_connection

    if connection is None: return

    # send message        
    try:
        # Send user's input to OpenAI
        # Create response (only the first time)
        # Afterwards, no need to create response explicitly if create_response is True
        if session.openai_new_conversation:
            await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": env.AZURE_OPENAI_FIRST_UTTERANCE_OF_USER}],
                }
            )
            await connection.response.create()
            session.openai_new_conversation = False
        else:
            b64 = base64.b64encode(audiodata).decode("ascii") 
            await connection.input_audio_buffer.append(audio = b64) 

    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[OPENAI CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[OPENAI ERROR & CLOSED] {e.code}:{e.reason}")
        return
    #finally:

####################################################################
# WebSocket Event Handler for OpenAI
####################################################################
async def openai_ws_event_handler(session: kazSession):

    connection = session.openai_connection

    if connection is None: return

    print("[OPENAI] ********* openai_ws_event_handler started ************")

    try:
        # handle websocket events
        async for event in connection:
            if event.type == "response.audio.delta": ### important: generated in chunks of 2000 bytes
                audio_bytes = base64.b64decode(event.delta)

                # Send back to Genesys Cloud - only enqueue data
                for i in range(0, len(audio_bytes), env.CHUNK_SIZE_BYTES):
                    chunk = audio_bytes[i : i + env.CHUNK_SIZE_BYTES]
                    await session.audio_tobe_sent_to_genesys.put(chunk)
                
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, {len(audio_bytes)} bytes of audio data. QUEUE SIZE: {session.audio_tobe_sent_to_genesys.qsize()}")

            # elif event.type == "response.audio.done":
            #     print(f"[OPENAI RECEIVED EVENT] event type: {event.type}")
            # elif event.type == "response.audio_transcript.delta":
            #     print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, Received data: {event.delta}")
            elif event.type == "response.audio_transcript.done":
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, Received data: {event.transcript}")
            elif event.type == "response.done":
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}")
            elif event.type == "error":
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, Received data: {event}")
                break
            # else:
            #     print(f"[OPENAI RECEIVED EVENT] event type: {event.type}")
    
    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[OPENAI CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[OPENAI ERROR & CLOSED] {e.code}:{e.reason}")
        return
    #finally:
