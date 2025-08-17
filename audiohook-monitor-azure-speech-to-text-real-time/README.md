# Genesys Cloud Demo

## Audiohook Monitor -> Azure AI Speech-to-Text voice transcription in real-time
This solution uses [Genesys AudioHook](https://developer.genesys.cloud/devapps/audiohook/) to send incoming voice from Genesys Cloud to the Azure Web App and transcribes conversations in real time.
Genesys Cloud and the Web App communicate via WebSocket, and the Web App calls Azure AI Speech service through HTTP REST APIs.

**Initial implementation: August 2024*

![Architecture](https://gsolar.kazumadachi.com/tools/img/audiohookmonitor-azure-ai-speech-to-text-architecture.png)
See the demonstration video [here](https://gsolar.kazumadachi.com/tools/audiohookmonitor_azureaispeech_stt.html).
