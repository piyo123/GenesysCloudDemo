import os

class env_vars:
    def __init__(self):
        self.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
        self.AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.AZURE_OPENAI_VOICE = os.getenv("AZURE_OPENAI_VOICE", "alloy") # alloy/echo/fable/onyx/nova/shimmer
        self.AZURE_OPENAI_VAD_TYPE = os.getenv("AZURE_OPENAI_VAD_TYPE" ,"server_vad") # server_vad or semantic_vad https://learn.microsoft.com/en-us/azure/ai-foundry/openai/how-to/realtime-audio#voice-activity-detection-vad-and-the-audio-buffer
        self.AZURE_OPENAI_TEMPERATURE = float(os.getenv("AZURE_OPENAI_TEMPERATURE", 0.8))
        self.AZURE_OPENAI_VAD_SENSITIVITY = float(os.getenv("AZURE_OPENAI_VAD_SENSITIVITY", 0.8))
        self.AZURE_OPENAI_PREFIX_PADDING_MS = int(os.getenv("AZURE_OPENAI_PREFIX_PADDING_MS", 300))
        self.AZURE_OPENAI_SILENCE_DURATION_MS = int(os.getenv("AZURE_OPENAI_SILENCE_DURATION_MS", 1000))
        self.AZURE_OPENAI_CREATE_RESPONSE = os.getenv("AZURE_OPENAI_CREATE_RESPONSE", "true").lower() == "true"
        self.AZURE_OPENAI_INTERRUPT_RESPONSE = os.getenv("AZURE_OPENAI_INTERRUPT_RESPONSE", "true").lower() == "true"
        self.AZURE_OPENAI_INSTRUCTIONS = os.getenv("AZURE_OPENAI_INSTRUCTIONS", "")
        self.AZURE_OPENAI_FIRST_UTTERANCE_OF_USER = os.getenv("AZURE_OPENAI_FIRST_UTTERANCE_OF_USER")
        self.CHUNK_SIZE_BYTES = int(os.getenv("CHUNK_SIZE_BYTES", 2000))
        self.SEND_TO_GENESYS_DURATION_MS = int(os.getenv("SEND_TO_GENESYS_DURATION_MS", 200))
        self.ECHO_MODE = os.getenv("ECHO_MODE", "false").lower() == "true"

        self._APP_VERSION = "0.170"

    @property
    def APP_VERSION(self):
        return self._APP_VERSION

env = env_vars()
