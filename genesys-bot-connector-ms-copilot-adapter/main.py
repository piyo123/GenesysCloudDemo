from fastapi import FastAPI, Request
import os
import uvicorn
import httpx
import CosmosDBUtil
import asyncio

app = FastAPI()
httpClient: httpx.AsyncClient | None = None

APP_VERSION = "X.X"
DIRECT_LINE_ENDPOINT_GET_TOKEN_AND_START_CONVERSATION = "https://directline.botframework.com/v3/directline/conversations"
DIRECT_LINE_ENDPOINT_POST_MESSAGE = "https://directline.botframework.com/v3/directline/conversations/$$msCopilotConversationId$$/activities"
DIRECT_LINE_ENDPOINT_RETRIEVE_MESSAGE = "https://directline.botframework.com/v3/directline/conversations/$$msCopilotConversationId$$/activities?watermark=$$msCopilotWatermark$$"
COPILOT_SECRET = os.getenv("COPILOT_SECRET")
RETRIEVE_MAX_ATTEMPT = 30

if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', port=8000)

@app.get("/")
async def root(request: Request):
    return f"This site is working. Version is {APP_VERSION}."

@app.post("/botconnectorsvc")
async def handler(request: Request):
    body = await request.json()
    
    #################################################
    # Call Microsoft Copilot via DirectLine
    #################################################

    # Initialize
    httpClient = httpx.AsyncClient()

    if "genesysConversationId" in body:
        genesysConversationId = body['genesysConversationId']

        # 既存の Copilot セッションを検索
        conversationData = await CosmosDBUtil.get_conversation_data(genesysConversationId)

        if conversationData is None: # 既存セッションなし
            print("CREATE NEW MS COPILOT SESSION")

            # Get token and start conversation
            response = await httpClient.post(
                DIRECT_LINE_ENDPOINT_GET_TOKEN_AND_START_CONVERSATION,
                json = {},
                headers = {
                    "Authorization": f"Bearer {COPILOT_SECRET}"
                }
            )
            responseJson = response.json()
            msCopilotConversationId = responseJson['conversationId']
            msCopilotWatermark = "0"
            token = responseJson['token'] # 今回は使わない

            # Send Message to Copilot (DirectLineで呼ぶとユーザーから何か言わないとなぜか最初の挨拶をしてくれない) 
            response = await sendMessageToCopilot(httpClient, msCopilotConversationId, "こんにちは") 
            msCopilotWatermark = response.json()['id'].split('|')[1]

        else: # 既存のCopilotセッションあり
            print("FOUND EXISTING MS COPILOT SESSION")
            msCopilotConversationId = conversationData['msCopilotConversationId'] 
            msCopilotWatermark = conversationData['msCopilotWatermark']

            # Send Message to Copilot
            if "botId" in body and "text" in body["inputMessage"]:
                message2send = body['inputMessage']['text']
                response = await sendMessageToCopilot(httpClient, msCopilotConversationId, message2send)
                msCopilotWatermark = response.json()['id'].split('|')[1]
    
    print(f"********** genesysConversationId = {genesysConversationId}, msCopilotConversationId = {msCopilotConversationId} **********")   

    # Retrieve message from Copilot (Polling)
    response = await getMessageFromCopilot(httpClient, msCopilotConversationId, msCopilotWatermark)
    responseJson = response.json()
    print(responseJson)

    if "activities" in responseJson and len(responseJson['activities']) > 0 and "watermark" in responseJson:      
        messageFromCopilot = responseJson['activities'][0]['text']
    else:
        messageFromCopilot = "Microsoft Copilot からのメッセージ取得に失敗しました。"

    # Cosmos DB Insert or Update
    await CosmosDBUtil.upsert_conversation_data(genesysConversationId, msCopilotConversationId, msCopilotWatermark)
    
    # Bot Connector へ返却する JSON 作成
    data = {
        "replymessages": [
            {
                "type": "Text",
                "text": messageFromCopilot
            }
        ],
        "botState": "COMPLETE", # COMPLETE, MOREDATA, FAILED
        "intent": "Order", # Genesys Bot Connector は1ターン完結で、インテントとスロットを埋める処理だけをオフロードする設計になっているので、今回Genesys Architect側で登録した「Order」を固定で返す。
        "confident": 1
    }

    # Bot Connector へ返却
    return data


# Copilot へ メッセージを送信
async def sendMessageToCopilot(httpClient, msCopilotConversationId, message):
    print(f"SENDING MESSAGE '{message}' TO COPILOT")
    response = await httpClient.post(
        DIRECT_LINE_ENDPOINT_POST_MESSAGE.replace("$$msCopilotConversationId$$", msCopilotConversationId),
        json = {
            "locale": "ja-jp",
            "type": "message",
            "from": {
                "id": "user1"
            },
            "text": message
        },
        headers = {
            #"Authorization": f"Bearer {token}" サーバーサイドなのでSecretで。Refresh token の実装するのを省略するため。
            "Authorization": f"Bearer {COPILOT_SECRET}"
        }
    )
    print(response.json())
    return response

# Copilot からメッセージ取得
async def getMessageFromCopilot(httpClient, msCopilotConversationId, msCopilotWatermark):
    count = 0
    while True:
        print(f"RETRIEVING MESSAGE FROM COPILOT - POLLING ATTEMPT {count}")
        count += 1
        await asyncio.sleep(1)
        response = await httpClient.get(
        DIRECT_LINE_ENDPOINT_RETRIEVE_MESSAGE.replace("$$msCopilotConversationId$$", msCopilotConversationId).replace("$$msCopilotWatermark$$", msCopilotWatermark),
            headers = {
                #"Authorization": f"Bearer {token}" サーバーサイドなのでSecretで。Refresh token の実装するのを省略するため。
                "Authorization": f"Bearer {COPILOT_SECRET}"
            }
        )
        responseJson = response.json()
        if "activities" in responseJson and len(responseJson['activities']) > 0:
            break
        elif count > RETRIEVE_MAX_ATTEMPT: # 予防線
            break
    
    return response

### Bot Connector から送られてくる JSON
"""
{
    'botId': 'adabot1', 
    'botVersion': '0.1', 
    'botSessionId': 'f9888cf5-98e2-45c5-9d2f-d8f2dfcecee8', 
    'inputMessage': {
        'type': 'Text', 
        'text': 'あだち'
    }, 
    'languageCode': 'ja-jp', 
    'botSessionTimeout': 4320, 
    'chatBot': {
        'id': '22DEE904-52F5-45A9-97EB-C50CA6141DBE', 
        'name': 'adabot1'
    }, 
    'genesysConversationId': '8c562a4d-c68c-4a8f-8d4d-6bc3e3cf3f27'
}
"""

### Bot Connector に返す最小限のJSON
"""
{ 
  "replymessages": [ 
    {  
      "type": "Text",  
      "text": "aiueo"  
    },
    "botState": "MOREDATA",
    "intent": "Order", # Genesys Bot Connector は1ターン完結で、インテントとスロットを埋める処理だけをオフロードする設計になっているので、今回Genesys Architect側で登録した「Order」を固定で返す。
    "confident": 1
  ] 
} 
"""
