import json
import asyncio
import websockets
import asyncio
from models import kazSession
from environvars import env
from websockets.asyncio.server import ServerConnection
from handlers.openai_ws_handler import get_or_create_openai_connection, send_data_to_openai, openai_ws_event_handler
from SessionManager import session_manager
from functools import partial
from websockets.exceptions import ConnectionClosed

AUDIO_CONNECTOR_ID = "kazumaadachiaudioconnector1"

####################################################################
# WebSocket Evnet Handler
####################################################################
async def audio_connector_ws_handler(ws: ServerConnection): 

    #############################################
    # connect
    #############################################

    print(f"ws handler started.path={ws.request.path}")

    # Audio Connector からの WebSocket 接続は /svc のみ受け付ける
    if not ws.request.path.endswith(f"/svc/{AUDIO_CONNECTOR_ID}"):
        await ws.close()
        return

    print(f"[CONNECTED] Audio Connector WebSocket Connected.")

    #############################################
    # handle messages
    #############################################
    try:
        # message events
        async for message in ws:

            if isinstance(message, bytes): # Audio Binary 1600 bytes per 200ms
                
                length = len(message)
                print(f"[MESSAGE] From Genesys Cloud. {session.genesysConversationId}: Binary Data ({length} Bytes)")

                if env.ECHO_MODE: # ECHO MODE
                    for i in range(0, len(message), env.CHUNK_SIZE_BYTES): # Only works when sending 1600 bytes every 200 ms
                        chunk = message[i : i + env.CHUNK_SIZE_BYTES]
                        await session.audio_tobe_sent_to_genesys.put(chunk)

                else: # NORMAL MODE       
                    await send_data_to_openai(session, message)

            else: # Text
                
                # parse message
                mJson = json.loads(message)
                messageType = mJson["type"]

                print(f"[MESSAGE] From Genesys Cloud. messageType={messageType}, message={message}")

                if messageType == "open":

                    # get genesysConversationId from the initial "open" message sent by Genesys Cloud
                    genesysConversationId = str(mJson["parameters"]["conversationId"])

                    # session management
                    session = session_manager.get_or_create(genesysConversationId)
                    if session.audio_connector_ws is None:
                        session.audio_connector_ws = ws

                    # register task to send audio to Genesys Cloud
                    if env.ECHO_MODE:
                        print("** REGISTERED AUDIO SENDER TASK FOR ECHO MODE")
                        session.send_audio_to_genesys_task = asyncio.create_task(audio_sender_to_genesyscloud(session, True))
                    else:
                        session.send_audio_to_genesys_task = asyncio.create_task(audio_sender_to_genesyscloud(session, False))
                    
                    # connect to OpenAI and create tasks
                    openai_connection = await get_or_create_openai_connection(genesysConversationId)
                    session.openai_connection = openai_connection
                    session.send_data_to_openai_task = asyncio.create_task(send_data_to_openai(session, message))
                    session.send_data_to_openai_task.add_done_callback(lambda t: print(f"[OPENAI] send_data_to_openai exit. Exception: {t.exception()}"))
                    session.openai_ws_event_handle_task = asyncio.create_task(openai_ws_event_handler(session))
                    session.openai_ws_event_handle_task.add_done_callback(lambda t: print(f"[OPENAI] openai_ws_event_handler exit. Exception: {t.exception()}"))

                    resJson = {
                        "version": "2",
                        "type": "opened",
                        "seq": session.serverSequence,
                        "clientseq": mJson["seq"],
                        "id": mJson["id"],
                        "parameters": {
                            "startPaused": False,
                            "media": [
                                {
                                    "type": "audio",
                                    "format": "PCMU",
                                    "channels": ["external"],
                                    "rate": 8000
                                }
                            ]
                        }
                    }
                
                elif messageType == "playback_started":
                    continue
                elif messageType == "playback_completed":
                    continue

                elif messageType == "ping":
                    resJson = {
                        "version": "2",
                        "type": "pong",
                        "seq": session.serverSequence,
                        "clientseq": mJson["seq"],
                        "id": mJson["id"],
                        "parameters": {}
                    }

                elif messageType == "close":
                    resJson = {
                        "version": "2",
                        "type": "closed",
                        "seq": session.serverSequence,
                        "clientseq": mJson["seq"],
                        "id": mJson["id"],
                        "parameters": {}
                    }

                elif messageType == "error":
                    acErrorCode = mJson["parameters"]["code"]
                    acErrorMsg = mJson["parameters"]["message"]
                    print(f"[ERROR] Audio Connector error code:{acErrorCode}, error message:{acErrorMsg}")
                
                # count up sequence
                session.serverSequence += 1

                # respond
                print(f"[RESPONSE] To Genesys Cloud. {json.dumps(resJson)}")
                await ws.send(json.dumps(resJson))

    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[ERROR & CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        return
    finally: # closed event
        print(f"[CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}")
        if session.openai_connection is not None: await session.openai_connection.close()
        if "session" in locals():
            session_manager.remove(genesysConversationId)

####################################################################
# send audio to Genesys Cloud
####################################################################
async def audio_sender_to_genesyscloud(session: kazSession, echoMode: bool):
    
    if echoMode: # Works only with this values
        CHUNK_SIZE = 1600   # bytes
        SEND_DURATION = 200 / 1000 # 200 millisecond in sec
        LOGGING_DURATION = SEND_DURATION * 5 # second
    else: # best: CHUNK_SIZE = 2000, SEND_DURATION == 200ms
        CHUNK_SIZE = env.CHUNK_SIZE_BYTES # bytes
        SEND_DURATION = env.SEND_TO_GENESYS_DURATION_MS / 1000 # millisecond
        LOGGING_DURATION = SEND_DURATION * 5 # second

    print(f"[AUDIO CONNECTOR] STARTED SENDING AUDIO TO GENESYS CLOUD. CHUNK SIZE:{CHUNK_SIZE} bytes, Initial size of queue: {session.audio_tobe_sent_to_genesys.qsize()}")

    counter = 0
    ws = session.audio_connector_ws
    try:
        while True:

            try:
                chunk = await asyncio.wait_for(session.audio_tobe_sent_to_genesys.get(), timeout=SEND_DURATION)
            except asyncio.TimeoutError:
                continue
            
            if len(chunk) > 0:
                try:
                    await ws.send(chunk)
                except ConnectionClosed as e:
                    print(f"[AUDIO CONNECTOR] WebScocket closed during send: {e}")
                    break

                await asyncio.sleep(SEND_DURATION)
                counter += SEND_DURATION

                if counter >= LOGGING_DURATION:
                    print(f"[AUDIO CONNECTOR] SENDING AUDIO DATA TO GENESYS: CHUNK SIZE:{CHUNK_SIZE} bytes, QUEUE SIZE:{session.audio_tobe_sent_to_genesys.qsize()}")
                    counter = 0

    except Exception as e:
        print(f"[AUDIO CONNECTOR] SENDING TO GENESYS ERROR: {e}")
