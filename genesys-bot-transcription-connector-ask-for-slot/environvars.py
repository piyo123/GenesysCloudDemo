import os
from dotenv import load_dotenv

class env_vars:
    def __init__(self):
        self.load()
        self.AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
        self.TRANSCRIPTION_LANGUAGE = os.getenv("TRANSCRIPTION_LANGUAGE")
        self._APP_VERSION = "0.01"

    def load(self):
        load_dotenv(override=False)

    @property
    def APP_VERSION(self):
        return self._APP_VERSION

env = env_vars()
