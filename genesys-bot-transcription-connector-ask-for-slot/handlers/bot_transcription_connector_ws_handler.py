import json
import asyncio
import websockets
import asyncio
from models import kazSession
from environvars import env
from websockets.asyncio.server import ServerConnection
from SessionManager import session_manager
from handlers.third_party_stt_handler import get_or_create_openai_connection, send_data_to_openai, openai_ws_event_handler, create_json_to_send_back
from functools import partial
from websockets.exceptions import ConnectionClosed

####################################################################
# Genesys Bot Transcription Connector (Ask for Slot)
# WebSocket Evnet Handler
####################################################################
async def bot_transcription_connector_ws_handler(ws: ServerConnection):

    #############################################
    # connect
    #############################################

    print(f"ws handler started.path={ws.request.path}, connection id={ws.id}")

    # Bot Transcription Connector からの WebSocket 接続は /svc のみ受け付ける
    #if not ws.request.path.endswith(f"/svc/{env.BOT_TRANSCRIPTION_CONNECTOR_ID}"):
    if not ws.request.path.endswith(f"/svc"):
        await ws.close()
        print("Invalid request path")
        return

    session: kazSession = None

    print(f"[CONNECTED] Bot Transcription Connector WebSocket Connected.")

    #############################################
    # message and close events
    #############################################
    try:
        # message events
        async for message in ws:

            # Audio format sent from Genesys Cloud: G.711 mu-law (Sampling Rate = 8kHz, 8bits/sample, monoral, 64kbps)
            # Audio binary fragment sent from Genesys Cloud: 1600 Bytes per 200ms
            if isinstance(message, bytes):
                
                length = len(message)
                print(f"[MESSAGE] From Genesys Cloud. {session.genesysConversationId}: Binary Data ({length} Bytes)")

                # speech detected
                if not session.speechDetected: # first time
                    # create return JSON
                    resJson = {
                        "version": "2",
                        "type": "event",
                        "seq": session.serverSequence,
                        "clientseq": mJson["seq"],
                        "id": mJson["id"],
                        "parameters": {
                            "entities": [
                                {
                                    "type": "speech_started",
                                    "data": {}
                                }
                            ]
                        }
                    }

                    # respond
                    print(f"[RESPONSE] To Genesys Cloud. Speech Detected. {json.dumps(resJson)}")
                    await ws.send(json.dumps(resJson))

                    # count up sequence
                    session.serverSequence += 1

                    # update session status
                    session.speechDetected = True

                # send audio data to openai
                await send_data_to_openai(session, message)

                # give transcription data back to Genesys Cloud
                if session.transcriptionCompleted:
                    resJson = await create_json_to_send_back(session)
                    print(f"[RESPONSE - TRANSCRIPTION] To Genesys Cloud. {json.dumps(resJson)}")
                    await ws.send(json.dumps(resJson, ensure_ascii=False))
                    session.serverSequence += 1

            else: # Text
                
                # parse message
                mJson = json.loads(message)
                messageType = mJson["type"]

                print(f"[MESSAGE] From Genesys Cloud. messageType={messageType}, message={message}")

                if messageType == "open":

                    # Get genesysConversationId from initial message (open) from Genesys Cloud
                    genesysConversationId = str(mJson["parameters"]["conversationId"])

                    # session management
                    session = session_manager.get_or_create(genesysConversationId)
                    if session.bot_transcription_connector_ws is None:
                        session.bot_transcription_connector_ws = ws
                        session.sessionId = mJson["id"]

                    # connect to openai and create openai task
                    openai_connection = await get_or_create_openai_connection(genesysConversationId)
                    session.openai_connection = openai_connection
                    session.send_data_to_openai_task = asyncio.create_task(send_data_to_openai(session, message))
                    session.send_data_to_openai_task.add_done_callback(lambda t: print(f"[OPENAI] send_data_to_openai exit. Exception: {t.exception()}"))
                    session.openai_ws_event_handle_task = asyncio.create_task(openai_ws_event_handler(session))
                    session.openai_ws_event_handle_task.add_done_callback(lambda t: print(f"[OPENAI] openai_ws_event_handler exit. Exception: {t.exception()}"))

                    # create return JSON
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

                elif messageType == "barge_in":
                    print("barge_in. not implemented yet.")

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
                
                # update sequence
                session.serverSequence += 1
                session.clientSequence = mJson["seq"]

                # respond
                print(f"[RESPONSE] To Genesys Cloud. {json.dumps(resJson)}")
                await ws.send(json.dumps(resJson))

    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[CLOSED] Bot Transcription Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[ERROR & CLOSED] Bot Transcription Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        return
    finally: # closed event
        if "session" in locals():
            print(f"[CLOSED] Bot Transcription Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}")
            session_manager.remove(genesysConversationId)