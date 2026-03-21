# Genesys Cloud Demo

## Audio Connector -> gpt-realtime
This solution implements [Genesys Audio Connector](https://help.genesys.cloud/articles/about-audio-connector/) feature to offload conversations to OpenAI gpt-realtime, using WebSocket, although gpt-realtime supports both WebRTC (RTP) and WebSocket.

**Initial implementation: September 2025*

You can listen to sample conversation in Japanese [here](https://gsolar.kazumadachi.com/tools/genesys-audio-connector-gpt-realtime.html).

> [!IMPORTANT]
> **Security Notice**  
> This sample code does not include validation of incoming requests using a client secret.
> In a production environment, you should always configure a Secret Value in the Genesys Cloud integration settings and implement request validation.
> This is essential to verify the authenticity of the connection source and to prevent impersonation or tampering of requests.
>
> For detailed guidance, see:
> - https://developer.genesys.cloud/devapps/audiohook/security#client-authentication
> - https://developer.genesys.cloud/devapps/audiohook/session-walkthrough#establishing-connection
