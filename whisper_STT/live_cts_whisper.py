import pyaudio
import wave
import whisper
import threading
import queue
import time
import os

# --------------------------------
# CONFIGURATION
# --------------------------------
CHUNK_DURATION = 10         # seconds for each audio chunk
SAMPLE_RATE = 16000         # Whisper prefers 16kHz
CHANNELS = 1                # Mono
CHUNK_SIZE = 1024           # Frames per buffer
AUDIO_FORMAT = pyaudio.paInt16

OUTPUT_FOLDER = "./chunks"   # Folder to temporarily store chunk WAVs
TRANSCRIPT_FILE = "transcript.txt"  # File to store transcribed text

# Global stop event to signal threads to quit
stop_event = threading.Event()


def record_chunks(q: queue.Queue):
    """
    Continuously records audio in CHUNK_DURATION-second chunks.
    For each chunk, saves a unique WAV file and puts the filename on the queue.
    """
    p = pyaudio.PyAudio()

    stream = p.open(format=AUDIO_FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)

    chunk_counter = 0
    print("[Recorder] Started recording chunks. Press Ctrl+C to stop.")

    try:
        while not stop_event.is_set():
            frames = []
            # Record exactly CHUNK_DURATION seconds
            for _ in range(0, int(SAMPLE_RATE / CHUNK_SIZE * CHUNK_DURATION)):
                if stop_event.is_set():
                    break
                data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                frames.append(data)

            if not frames:
                break  # if we got no frames, probably stopping

            chunk_filename = os.path.join(OUTPUT_FOLDER, f"chunk_{chunk_counter}.wav")

            # Save the chunk to a WAV file
            with wave.open(chunk_filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(AUDIO_FORMAT))
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b''.join(frames))

            print(f"[Recorder] Wrote chunk: {chunk_filename}")
            q.put(chunk_filename)  # Put the file on the queue for transcription

            chunk_counter += 1

    finally:
        print("[Recorder] Stopping microphone...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("[Recorder] Microphone closed.")


def transcribe_chunks(q: queue.Queue, model):
    """
    Pulls chunk filenames from the queue, transcribes them with Whisper,
    prints the text, and then deletes the WAV file.
    Also appends the text to TRANSCRIPT_FILE.
    """
    # Open the transcript file in append mode
    # so each new chunk’s text is added at the end.
    with open(TRANSCRIPT_FILE, 'a', encoding='utf-8') as transcript_f:
        while not stop_event.is_set() or not q.empty():
            try:
                chunk_filename = q.get(timeout=1)  # Wait for a chunk up to 1 second
            except:
                # If queue is empty and stop_event not set, keep waiting
                continue

            print(f"[Transcriber] Transcribing {chunk_filename}...")

            result = model.transcribe(chunk_filename)
            text = result.get("text", "").strip()

            # Print to console
            print(f"{chunk_filename}: {text}\n")

            # Write to transcript file
            transcript_f.write(f"{chunk_filename}: {text}\n")
            transcript_f.flush()  # Make sure it's written to disk immediately

            # Delete the chunk file to save space
            if os.path.exists(chunk_filename):
                os.remove(chunk_filename)
                print(f"[Transcriber] Deleted {chunk_filename}.")

            q.task_done()

        print("[Transcriber] No more chunks to process. Exiting thread.")


def main():
    # Make sure output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)

    # If desired, remove old transcript file or append to it
    if os.path.exists(TRANSCRIPT_FILE):
        print(f"[Main] Warning: {TRANSCRIPT_FILE} already exists. New transcripts will be appended.\n")

    # Prepare the queue that will hold chunk filenames
    chunk_queue = queue.Queue()

    # Load the Whisper 'tiny' model once
    print("[Main] Loading Whisper tiny model...")
    model = whisper.load_model("tiny")
    print("[Main] Model loaded.")

    # Create threads
    recorder_thread = threading.Thread(target=record_chunks, args=(chunk_queue,), daemon=True)
    transcriber_thread = threading.Thread(target=transcribe_chunks, args=(chunk_queue, model), daemon=True)

    # Start threads
    recorder_thread.start()
    transcriber_thread.start()

    try:
        # Keep main alive until Ctrl+C
        while recorder_thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\n[Main] Ctrl+C detected, stopping...")
        stop_event.set()

    # Wait for the recorder thread to finish
    recorder_thread.join()

    # Wait until all queued chunks are transcribed
    chunk_queue.join()

    # Then transcriber thread can exit
    transcriber_thread.join()

    print("[Main] All done. Exiting.")


if __name__ == "__main__":
    main()
