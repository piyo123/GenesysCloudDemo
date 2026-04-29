# Genesys Cloud Demo

## Bot Transcription Connector for "Ask for Slot"
This solution implements [Genesys Bot Transcription Connector][] feature and enables BYO-ASR (Bring Your Own Automatic Speech Recognition) for the ["Ask for Slot" action][rc-ask-for-slot-action], which allows a bot built with Architect in Genesys Cloud to collect information from a caller in a Bot Flow.

Bot Transcription Connector is built on top of [Genesys Audio Connector][], which sends the caller's voice to a specified web application for processing or integration with other bots. Genesys Audio Connector itself is built on [Genesys Audiohook][], which streams audio data from all participants in an interaction, whereas Audio Connector streams only the caller's voice.

You can find the specifications for Genesys Audiohook, Audio Connector, and Bot Transcription Connector [here][audiohook-spec].

In this example, I used OpenAI's [gpt-realtime][] in transcription-only mode, although gpt-realtime is originally a speech-to-speech model.

You can listen to sample conversation [here][sample-page]

**Initial implementation: April 2026*

> [!IMPORTANT]
> **Security Notice**  
> This sample code does not include validation of incoming requests using a client secret.
> In a production environment, you should always configure a Secret Value in the Genesys Cloud integration settings and implement request validation.
> This is essential to verify the authenticity of the connection source and to prevent impersonation or tampering of requests.
>
> For detailed guidance, see:
> - https://developer.genesys.cloud/devapps/audiohook/security#client-authentication
> - https://developer.genesys.cloud/devapps/audiohook/session-walkthrough#establishing-connection

[gpt-realtime]: https://openai.com/index/introducing-gpt-realtime/
[Genesys Bot Transcription Connector]: https://help.genesys.cloud/articles/configure-and-activate-the-bot-transcription-connector-integration/
[Genesys Audio Connector]: https://help.genesys.cloud/articles/about-audio-connector/
[Genesys Audiohook]: https://help.genesys.cloud/articles/about-audiohook-monitor/
[audiohook-spec]: https://developer.genesys.cloud/devapps/audiohook/
[rc-ask-for-slot-action]: https://help.genesys.cloud/articles/ask-for-slot-action/
[sample-page]: https://gsolar.z11.web.core.windows.net/tools/genesys-bot-transcription-connector-ask-for-slot.html