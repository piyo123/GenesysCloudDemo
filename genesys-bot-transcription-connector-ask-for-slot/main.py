import asyncio
import websockets
from environvars import env
from http import HTTPStatus
from websockets.asyncio.server import ServerConnection
from websockets.http11 import Request, Response
from handlers.bot_transcription_connector_ws_handler import bot_transcription_connector_ws_handler

# health check
async def process_request(conn: ServerConnection, request: Request):
	if (request.headers.get("Upgrade") or "").lower() != "websocket":
		print("HTTP health cehck.") 
		body = await get_app_info()
		return conn.respond(
			200,
			body
		)
	return None

async def main():
	async with websockets.serve(					# / でも /svc でもすべてのパスで受け付ける。svcに絞っているのは、bot_transcription_connector_ws_handler.py 
		bot_transcription_connector_ws_handler,
		"0.0.0.0",
		8000,
		process_request=process_request
	) as server:
		for socket in server.sockets:
			host, port = socket.getsockname()[:2]
			print(f"[STARTUP INFO] Bot Transcription Connector for Ask For Slot WebSocket server started, listening on wss://{host}:{port}")
			print(f"[STARTUP INFO] For health check and environment variables, access https://appurl/")
			print(f"[STARTUP INFO] Application version: {env.APP_VERSION}")
			print(f"[STARTUP INFO] TRANSCRIPTION_LANGUAGE: {env.TRANSCRIPTION_LANGUAGE}")

		await asyncio.Future()  # サーバーが終了しないように待機

async def get_app_info():
	return f"Web App is working. App version is {env.APP_VERSION}.\n"

# main.py が実行されたとき
if __name__ == "__main__":
	asyncio.run(main())
