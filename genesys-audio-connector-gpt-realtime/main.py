import asyncio
import websockets
from environvars import env
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection
from websockets.http11 import Request, Response
from handlers.audio_connector_ws_handler import audio_connector_ws_handler

# health check
async def process_request(conn: ServerConnection, request: Request):
	print("HTTP health cehck.")
	if (request.headers.get("Upgrade") or "").lower() != "websocket": 
		body = await get_app_info()
		return conn.respond(
			200,
			body
		)
	return None

# main
async def main():
	async with websockets.serve(
		audio_connector_ws_handler,
		"0.0.0.0",
		8000,
		process_request=process_request
	) as server:
		for socket in server.sockets:
			host, port = socket.getsockname()[:2]
			print(f"[STARTUP INFO] Audio Connector WebSocket server started, listening on wss://{host}:{port}")
			print(f"[STARTUP INFO] For health check and environment variables, access https://appurl/")
			print(f"[STARTUP INFO] Application version: {env.APP_VERSION}")

		await asyncio.Future()

# output environment variables on health check page
async def get_app_info():
	return f"Web App is working. App version is {env.APP_VERSION}.\n" \
			f" AZURE_OPENAI_ENDPOINT: {env.AZURE_OPENAI_ENDPOINT}\n" \
			f" AZURE_OPENAI_API_VERSION: {env.AZURE_OPENAI_API_VERSION}\n" \
			f" AZURE_OPENAI_DEPLOYMENT: {env.AZURE_OPENAI_DEPLOYMENT}\n" \
			f" AZURE_OPENAI_VOICE: {env.AZURE_OPENAI_VOICE}\n" \
			f" AZURE_OPENAI_VAD_TYPE: {env.AZURE_OPENAI_VAD_TYPE}\n" \
			f" AZURE_OPENAI_VAD_SENSITIVITY: {env.AZURE_OPENAI_VAD_SENSITIVITY}\n" \
			f" AZURE_OPENAI_PREFIX_PADDING_MS: {env.AZURE_OPENAI_PREFIX_PADDING_MS}\n" \
			f" AZURE_OPENAI_SILENCE_DURATION_MS: {env.AZURE_OPENAI_SILENCE_DURATION_MS}\n" \
			f" AZURE_OPENAI_CREATE_RESPONSE: {env.AZURE_OPENAI_CREATE_RESPONSE}\n" \
			f" AZURE_OPENAI_INTERRUPT_RESPONSE: {env.AZURE_OPENAI_INTERRUPT_RESPONSE}\n" \
			f" AZURE_OPENAI_INSTRUCTIONS: {env.AZURE_OPENAI_INSTRUCTIONS}\n" \
			f" AZURE_OPENAI_FIRST_UTTERANCE_OF_USER: {env.AZURE_OPENAI_FIRST_UTTERANCE_OF_USER}\n" \
			f" CHUNK_SIZE_BYTES: {env.CHUNK_SIZE_BYTES}\n" \
			f" SEND_TO_GENESYS_DURATION_MS: {env.SEND_TO_GENESYS_DURATION_MS}\n" \
			f" ECHO_MODE: {env.ECHO_MODE}\n"

# main entry point	
if __name__ == "__main__":
	asyncio.run(main())
