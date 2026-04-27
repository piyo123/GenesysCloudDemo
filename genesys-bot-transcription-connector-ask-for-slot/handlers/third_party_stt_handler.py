import asyncio
import websockets
import base64
import uuid
from environvars import env
from openai import AsyncOpenAI, AsyncAzureOpenAI
from models import kazSession
from SessionManager import session_manager
from openai.resources.realtime.realtime import AsyncRealtimeConnection

####################################################################
# get or create websocket connection to OpenAI
####################################################################
async def get_or_create_openai_connection(genesysConversationId: str) -> AsyncRealtimeConnection:
    
    print("[OPENAI] ********* get_or_create_openai_connection started ************")

    try:
        # check if websocket connected to openai already exists
        session = session_manager.get_or_create(genesysConversationId) # session corresponding genesys conversation id must exists
        if session.openai_connection is None:

            print("[OPENAI] CREATE NEW OPENAI CONNECTION")

            client = AsyncAzureOpenAI(
                azure_endpoint = env.AZURE_OPENAI_ENDPOINT,
                azure_deployment = "gpt-realtime",
                api_key = env.AZURE_OPENAI_API_KEY,
                api_version = "2024-10-01-preview"
            )

            # create websocket connection (model paramter == deployment name of the model on Microsoft Foundry)
            context_manager = client.realtime.connect(model="gpt-realtime")
            connection = await context_manager.__aenter__()

            # configuration
            await connection.session.update(
                session = {
                    "input_audio_format": "g711_ulaw",
                    "modalities": ["text"],
                    "input_audio_transcription": {
                        "model": "gpt-realtime",
                        "language": env.TRANSCRIPTION_LANGUAGE # ja, en , etc.
                    },
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "silence_duration_ms": 1500,
                        "prefix_padding_ms": 500
                    },
                    "instructions": "Do not answer. Only transcribe the user's speech."
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
        if isinstance(audiodata, bytes):
            #print("[OPENAI] SENDING USER'S UTTERANCE TO OPENAI")
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
            if event.type == "conversation.item.input_audio_transcription.completed":
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, Received data: {event.transcript}")
                session.transcriptionCompleted = True
                session.transriptionData = event.transcript
            #elif event.type == "conversation.item.input_audio_transcription.failed":
                #print(f"[OPENAI TRANSCRIPTION FAILED] raw_event={event}")
                #print(f"[OPENAI TRANSCRIPTION FAILED] error_attr={getattr(event, 'error', None)}")
            elif event.type == "error":
                print(f"[OPENAI RECEIVED EVENT] event type: {event.type}, Received data: {event}")
                break
            else:
                 print(f"[OPENAI RECEIVED EVENT] event type: {event.type}")
    
    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 1000:
            print(f"[OPENAI CLOSED] Audio Connector WebSocket Disconnected: genesysConversationId={session.genesysConversationId}, {e.code}:{e.reason}") 
        else:
            print(f"[OPENAI ERROR & CLOSED] {e.code}:{e.reason}")
        return
    #finally:

""""
Event Type (gpt-4o-transcribe)
[OPENAI RECEIVED EVENT] event type: session.created
[OPENAI RECEIVED EVENT] event type: session.updated
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.speech_started
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.speech_stopped
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.committed
[OPENAI RECEIVED EVENT] event type: conversation.item.created
[OPENAI RECEIVED EVENT] event type: response.created
[OPENAI RECEIVED EVENT] event type: conversation.item.input_audio_transcription.failed
[OPENAI RECEIVED EVENT] event type: response.output_item.added
[OPENAI RECEIVED EVENT] event type: response.content_part.added
[OPENAI RECEIVED EVENT] event type: response.audio_transcript.delta
[OPENAI RECEIVED EVENT] event type: response.audio.done
[OPENAI RECEIVED EVENT] event type: response.audio_transcript.done, Received data: Hi there! How can
[OPENAI RECEIVED EVENT] event type: response.content_part.done
[OPENAI RECEIVED EVENT] event type: response.output_item.done
[OPENAI RECEIVED EVENT] event type: response.done

EVENT LIST (gpt-realtime)
[OPENAI RECEIVED EVENT] event type: session.created
[OPENAI RECEIVED EVENT] event type: session.updated
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.speech_started
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.speech_stopped
[OPENAI RECEIVED EVENT] event type: input_audio_buffer.committed
[OPENAI RECEIVED EVENT] event type: conversation.item.created
[OPENAI RECEIVED EVENT] event type: response.created
[OPENAI RECEIVED EVENT] event type: response.output_item.added
[OPENAI RECEIVED EVENT] event type: response.content_part.added
[OPENAI RECEIVED EVENT] event type: response.text.delta
[OPENAI RECEIVED EVENT] event type: response.text.done
[OPENAI RECEIVED EVENT] event type: response.content_part.done
[OPENAI RECEIVED EVENT] event type: response.output_item.done
[OPENAI RECEIVED EVENT] event type: response.done
[OPENAI RECEIVED EVENT] event type: conversation.item.input_audio_transcription.completed
"""

####################################################################
# Create Json to be sent back to Genesys Cloud
####################################################################
async def create_json_to_send_back(session: kazSession):

    retJson = {
        "version": "2",
        "type": "event",
        "seq": session.serverSequence,
        "clientseq": session.clientSequence,
        "id": session.sessionId,
        "parameters": {
            "entities": [
                {
                    "type": "transcript",
                    "data": {
                        "id": str(uuid.uuid4()),
                        "channelId": 1,
                        "isFinal": True,
                        "offset": "PT0.0S",  # DUMMY
                        "duration": "PT0.0S", # DUMMY
                        "alternatives": [
                            {
                                "confidence": 1.00,
                                "languages": ["ja-JP", "en-US"],
                                "interpretations": [
                                    {
                                        "type": "display",
                                        "transcript": session.transriptionData,
                                        "tokens": [
                                            { # set dummy data as 'tokens' entity is mandatory
                                                "type": "word",
                                                "value": "DUMMY",
                                                "confidence": 0.0,
                                                "offset": "PT123.4S",
                                                "duration": "PT0.6S",
                                                "language": "ja-JP"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }

    return retJson

####################################################################
# stub functions
####################################################################
async def exec_transcription_dummy(session: kazSession, audiodata: bytes):
    await asyncio.sleep(10)
    session.transcriptionCompleted = True

async def returnTranscriptionData_DUMMY(session: kazSession, clientSeq, id):

    retJson = {
        "version": "2",
        "type": "event",
        "seq": session.serverSequence,
        "clientseq": clientSeq,
        "id": id,
        "parameters": {
            "entities": [
                {
                    "type": "transcript",
                    "data": {
                        "id": "802095c6-80d2-4dbe-8a9b-57af2d094f53",
                        "channelId": 1,
                        "isFinal": True,
                        "offset": "PT123.4S",
                        "duration": "PT6.5S",
                        "alternatives": [
                            {
                                "confidence": 0.98,
                                "languages": ["ja-JP"],
                                "interpretations": [
                                    {
                                        "type": "display",
                                        "transcript": "今日はジェネシスに、お電話いただきありがとうございます。",
                                        "tokens": [
                                            {
                                            "type": "word",
                                            "value": "今日",
                                            "confidence": 0.9410744,
                                            "offset": "PT123.4S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "は",
                                            "confidence": 0.9009254,
                                            "offset": "PT124.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "ジェネシス",
                                            "confidence": 0.9321196,
                                            "offset": "PT125.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "に",
                                            "confidence": 0.90830886,
                                            "offset": "PT125.7S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "お",
                                            "confidence": 0.8385644,
                                            "offset": "PT126.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "電話",
                                            "confidence": 0.96603715,
                                            "offset": "PT127.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "いただき",
                                            "confidence": 0.96109676,
                                            "offset": "PT127.8S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "ありがとう",
                                            "confidence": 0.97822165,
                                            "offset": "PT129.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            },
                                            {
                                            "type": "word",
                                            "value": "ございます",
                                            "confidence": 0.9490999,
                                            "offset": "PT130.2S",
                                            "duration": "PT0.6S",
                                            "language": "ja-JP"
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }

    return retJson
