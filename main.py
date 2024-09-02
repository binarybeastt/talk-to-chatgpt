from signal import SIGINT, SIGTERM
import asyncio
from dotenv import load_dotenv
import sys

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
    Microphone,
)

from chatbot import init_chat, get_response 
from deepgram_synthesis import text_to_speech

load_dotenv()

is_finals = []

# Initialize chat session
chat = init_chat()

async def main():
    try:
        loop = asyncio.get_event_loop()

        if sys.platform != "win32":
            for signal in (SIGTERM, SIGINT):
                loop.add_signal_handler(
                    signal,
                    lambda: asyncio.create_task(
                        shutdown(signal, loop, dg_connection, microphone)
                    ),
                )

        config: DeepgramClientOptions = DeepgramClientOptions(
            options={"keepalive": "true"}
        )
        deepgram: DeepgramClient = DeepgramClient("", config)
        dg_connection = deepgram.listen.asyncwebsocket.v("1")

        async def on_open(self, open, **kwargs):
            print("Connection Open")

        async def on_message(self, result, **kwargs):
            global is_finals
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) == 0:
                return
            if result.is_final:
                is_finals.append(sentence)
                if result.speech_final:
                    utterance = " ".join(is_finals)
                    print(f"Speech Final: {utterance}")
                    is_finals = []

                    response = await get_response(chat, utterance)  # Call to the chatbot
                    print(f"GPT Response: {response}")  # Print the chatbot's response

                    # Mute microphone before playing speech
                    microphone.mute()
                    await text_to_speech({"text": response})
                    # Unmute microphone after playing speech
                    microphone.unmute()

                else:
                    print(f"Is Final: {sentence}")
            else:
                print(f"Interim Results: {sentence}")

        async def on_metadata(self, metadata, **kwargs):
            print(f"Metadata: {metadata}")

        async def on_speech_started(self, speech_started, **kwargs):
            print("Speech Started")

        async def on_utterance_end(self, utterance_end, **kwargs):
            global is_finals
            if len(is_finals) > 0:
                utterance = " ".join(is_finals)
                print(f"Utterance End: {utterance}")
                is_finals = []

        async def on_close(self, close, **kwargs):
            print("Connection Closed")

        async def on_error(self, error, **kwargs):
            print(f"Handled Error: {error}")

        async def on_unhandled(self, unhandled, **kwargs):
            print(f"Unhandled Websocket Message: {unhandled}")

        dg_connection.on(LiveTranscriptionEvents.Open, on_open)
        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        dg_connection.on(LiveTranscriptionEvents.Metadata, on_metadata)
        dg_connection.on(LiveTranscriptionEvents.SpeechStarted, on_speech_started)
        dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)
        dg_connection.on(LiveTranscriptionEvents.Close, on_close)
        dg_connection.on(LiveTranscriptionEvents.Error, on_error)
        dg_connection.on(LiveTranscriptionEvents.Unhandled, on_unhandled)

        options: LiveOptions = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300,
        )

        addons = {"no_delay": "true"}

        print("\n\nStart talking! Press Ctrl+C to stop...\n")
        if await dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return

        microphone = Microphone(dg_connection.send)
        microphone.start()

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            microphone.finish()
            await dg_connection.finish()

        print("Finished")

    except Exception as e:
        print(f"Could not open socket: {e}")
        return

async def shutdown(signal, loop, dg_connection, microphone):
    print(f"Received exit signal {signal.name}...")
    microphone.finish()
    await dg_connection.finish()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    print(f"Cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    print("Shutdown complete.")

asyncio.run(main())
