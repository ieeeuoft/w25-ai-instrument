import pyaudio
import wave
import whisper
import time

def record_audio(seconds=30, output_filename="output.wav"):
    """Record audio from default microphone for a given duration."""
    # Audio recording parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print(f"Recording for {seconds} seconds...")
    frames = []

    for _ in range(0, int(RATE / CHUNK * seconds)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    wf = wave.open(output_filename, "wb")
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    print(f"Audio saved to {output_filename}")

def transcribe_audio(filename="/home/athavan/Downloads/output.wav", model_size="tiny"):
    """Transcribe audio file using OpenAI Whisper."""
    print(f"Loading Whisper '{model_size}' model...")
    model = whisper.load_model(model_size)

    print("Transcribing audio...")
    start_time = time.time()
    result = model.transcribe(filename)
    end_time = time.time()

    print("Transcription completed.")
    print(f"Time taken: {round(end_time - start_time, 2)} seconds")
    print("Transcribed text:")
    print(result["text"])

if __name__ == "__main__":
    # Step 1: Record for 30 seconds and save
    record_audio(seconds=30, output_filename="/home/athavan/Downloads/output.wav")

    # Step 2: Transcribe the saved file using Whisper tiny model
    transcribe_audio(filename="/home/athavan/Downloads/output.wav", model_size="tiny")
