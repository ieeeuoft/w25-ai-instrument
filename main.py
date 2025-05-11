import os
import wave
import time
import ast
import subprocess
import requests
import numpy as np
import pandas as pd
import pyaudio
import whisper
from midi.speaker import play_audio
from sentence_transformers import SentenceTransformer
from pedalboard import Pedalboard, Chorus, Reverb
import embedded.get_reading as get_reading
import soundfile as sf
import librosa


# -------------------------------
# CONFIGURATION
# -------------------------------
RECORD_SECONDS = 8              # Total duration to record (in seconds)
SAMPLE_RATE = 16000              # Whisper prefers 16kHz
CHANNELS = 1                     # Mono recording
CHUNK_SIZE = 1024                # Number of frames per buffer
AUDIO_FORMAT = pyaudio.paInt16   # Audio format

WAVE_OUTPUT_FILENAME = "temp_chunk.wav"    # Temporary audio file
TRANSCRIPT_FILE = "transcript.txt"         # File to save transcription
SOUNDS_CSV = "sounds.csv"                  # CSV file with sound metadata and embeddings
TEMP_MP3_FILENAME = "temp_sound.mp3"       # Temporary sound preview file

# Local path to the SentenceTransformer model (update as needed)
SENTENCE_MODEL_PATH = '/home/athavan/w25-ai-instrument/whisper_embeddings/all-MiniLM-L6-v2'

# -------------------------------
# RECORDING FUNCTION
# -------------------------------
def record_audio(filename, record_seconds=15):
    """
    Records audio for a given duration and saves it to a WAV file.
    """
    p = pyaudio.PyAudio()
    stream = p.open(format=AUDIO_FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK_SIZE)
    print(f"Recording audio for {record_seconds} seconds...")
    frames = []
    num_frames = int(SAMPLE_RATE / CHUNK_SIZE * record_seconds)
    for _ in range(num_frames):
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        frames.append(data)
    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(AUDIO_FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    print(f"Audio saved to {filename}.")

# -------------------------------
# TRANSCRIPTION FUNCTION
# -------------------------------
def transcribe_audio(audio_filename, transcript_filename):
    """
    Uses the Whisper model to transcribe the given audio file.
    Writes the transcription text to transcript_filename.
    """
    print("Loading Whisper model...")
    model = whisper.load_model("tiny")
    print("Transcribing audio...")
    result = model.transcribe(audio_filename)
    text = result.get("text", "").strip()
    print("Transcription:", text)

    with open(transcript_filename, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Transcription written to {transcript_filename}.")
    return text

# -------------------------------
# EMBEDDING AND MATCHING FUNCTIONS
# -------------------------------
def cosine_similarity(vec1, vec2):
    """Compute cosine similarity between two vectors."""
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def load_dataset(csv_filename):
    """
    Load the sounds dataset from a CSV.
    The CSV must have an 'embedding' column with string representations of a list.
    """
    df = pd.read_csv(csv_filename)
    df['embedding'] = df['embedding'].apply(ast.literal_eval)
    return df

def get_query_text(filename):
    """Reads the query text from a file."""
    with open(filename, 'r', encoding='utf-8') as f:
        return f.read().strip()

def compute_query_embedding(query, model):
    """Compute the embedding vector for the query text."""
    return model.encode(query)

def find_best_match(query_embedding, df):
    """
    Compare the query embedding against all embeddings in the DataFrame,
    and return the row with the highest cosine similarity.
    """
    similarities = []
    for _, row in df.iterrows():
        sound_embedding = np.array(row['embedding'])
        sim = cosine_similarity(query_embedding, sound_embedding)
        similarities.append(sim)
    df['similarity'] = similarities
    df_sorted = df.sort_values(by='similarity', ascending=False)
    return df_sorted.iloc[0]

# -------------------------------
# SOUND PLAYBACK FUNCTIONS
# -------------------------------
def download_sound(url, filename):
    """
    Downloads the sound file from the URL and saves it locally.
    """
    print(f"Downloading sound from {url} ...")
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, 'wb') as f:
        f.write(response.content)
    print(f"Downloaded sound saved as {filename}.")

def play_sound(filename):
    sound, sr = librosa.load(filename)
    r1, r2 = get_reading.get_reading()
    r2 = r2 / 3.3
    r1 = r1 / 3.3
    pedalboard = Pedalboard([Reverb(room_size=r2), Chorus(mix=r1)])
    sound = pedalboard(sound, sr)
    sf.write("play.wav", sound, sr)
    #play_audio("play.wav", volume_increase=4)
    """
    Plays the sound file using an external player (here, mpv).
    """
    print(f"Playing sound: {filename}")
    try: 
        play_audio("play.wav", volume_increase=4)
        #subprocess.run(["mpv", filename], check=True)
    except subprocess.CalledProcessError as e:
        print("Error playing sound:", e)

# -------------------------------
# MAIN SCRIPT
# -------------------------------
def main():
    # Record audio for 15 seconds.
    record_audio(WAVE_OUTPUT_FILENAME, RECORD_SECONDS)

    # Transcribe the recorded audio using Whisper.
    # transcribe_audio(WAVE_OUTPUT_FILENAME, TRANSCRIPT_FILE)
    # if os.path.exists(WAVE_OUTPUT_FILENAME):
    #     os.remove(WAVE_OUTPUT_FILENAME)

    # # Create embeddings for the transcription.
    # print("Loading sentence transformer model...")
    # sentence_model = SentenceTransformer(SENTENCE_MODEL_PATH)
    # print("Sentence model loaded.")
    # query_text = get_query_text(TRANSCRIPT_FILE)
    # if not query_text:
    #     print("The transcript is empty. Exiting.")
    #     return
    # query_embedding = compute_query_embedding(query_text, sentence_model)

    # # Compare the query embedding with embeddings from sounds.csv.
    # print(f"Loading dataset from {SOUNDS_CSV} ...")
    # df = load_dataset(SOUNDS_CSV)
    # best_match = find_best_match(query_embedding, df)
    # print("\nBest Matching Sound:")
    # print("ID:", best_match['id'])
    # print("Name:", best_match['name'])
    # print("Description:", best_match['description'])
    # print("Preview URL:", best_match['preview'])
    # print("Similarity Score:", best_match['similarity'])

    # # Download and play the most similar sound.
    # preview_url = best_match['preview']
    # download_sound(preview_url, TEMP_MP3_FILENAME)
    # play_sound(TEMP_MP3_FILENAME)
    # if os.path.exists(TEMP_MP3_FILENAME):
    #     os.remove(TEMP_MP3_FILENAME)
    # print("Done.")

if __name__ == '__main__':
    main()
