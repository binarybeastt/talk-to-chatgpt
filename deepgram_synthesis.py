import asyncio
from dotenv import load_dotenv
import logging
from deepgram.utils import verboselogs
from pydub import AudioSegment
from pydub.playback import play
import io
import os

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    SpeakOptions,
)

load_dotenv()

# SPEAK_TEXT = {"text": "My name is Bolarinwa, how are you today?"}


async def text_to_speech(SPEAK_TEXT):
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
    config: DeepgramClientOptions = DeepgramClientOptions(
        options={"keepalive": "true"}
    )
    deepgram: DeepgramClient = DeepgramClient(deepgram_api_key, config)
    options = SpeakOptions(
        model="aura-asteria-en",
    )

    response = await deepgram.speak.asyncrest.v("1").stream_raw(SPEAK_TEXT, options)

    print(f"Response: {response}")
    for header in response.headers:
        print(f"{header}: {response.headers[header]}")

    audio_data = bytearray()
    async for data in response.aiter_bytes():
        audio_data.extend(data)

    await response.aclose()
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
    play(audio_segment)

