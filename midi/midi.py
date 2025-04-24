import rtmidi
import soundfile as sf
import sounddevice as sd
import librosa
import time
import threading
import numpy as np
from pedalboard import Pedalboard, Chorus, Reverb, Delay, Distortion
import curses
import sys
import os

# Add parent directory to the import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from get_reading import get_reading


sample_path = 'C Major Piano.wav'
sound, sr = librosa.load(sample_path)

reverb_board = Pedalboard([Distortion(drive_db=20)])
chorus_board = Pedalboard([Chorus()])

# Add global variables to track current stream and playback
current_stream = None
current_thread = None
stop_flag = False
CHUNK_SIZE = 1024  # Process audio in smaller chunks
FADE_TIME = 5  # 30ms fade out
last_write_time = 0
wait_time = 0

# Add these to the global variables
active_samples = []
samples_lock = threading.Lock()

# When creating the audio data, convert to float32 immediately
sound = sound.astype(np.float32)  # Convert the entire array once at the beginning

# Add to global variables
current_channel = 0  # 0 = left, 1 = right

def get_pedalboard():
    r1, r2 = 1, 1
    r2 = r2 / 3.3
    r1 = r1 / 3.3
    print("reverb", r2)
    print("chorus", r1)
    pedalboard = Pedalboard([Reverb(room_size=r2), Chorus(mix=r1)])
    return pedalboard

def apply_pedalboard(audio, sr, pedalboard):
    return pedalboard(audio, sr)

def apply_fade(audio, fade_samples, fade_out=True):
    fade = np.linspace(1, 0, fade_samples) if fade_out else np.linspace(0, 1, fade_samples)
    return audio[:fade_samples] * fade

def play_audio(sample, sample_rate, fade_duration=0.5):
    global current_stream, current_thread, stop_flag, current_channel

    # Ensure sample is float32
    sample = np.asarray(sample, dtype=np.float32)

    # Stop the current audio with a fade-out
    if current_stream is not None and current_stream.active:
        stop_flag = True
        current_thread.join(timeout=fade_duration + 0.1)

    # Reset the stop flag for the new audio
    stop_flag = False

    # Calculate fade samples
    fade_samples = int(fade_duration * sample_rate)

    def audio_thread():
        pos = 0
        CHUNK_SIZE = 1024

        while pos < len(sample):
            mono_chunk = sample[pos:pos + CHUNK_SIZE]
            if len(mono_chunk) == 0:
                break

            # Create stereo chunk with zeros in the other channel
            stereo_chunk = np.zeros((len(mono_chunk), 2), dtype=np.float32)
            if current_channel == 0:
                stereo_chunk[:, 0] = mono_chunk  # Left channel
            else:
                stereo_chunk[:, 1] = mono_chunk  # Right channel

            # Apply fade out if stopping
            if stop_flag:
                fade_chunk = stereo_chunk[:fade_samples] if len(stereo_chunk) > fade_samples else stereo_chunk
                fade = np.linspace(1, 0, len(fade_chunk), dtype=np.float32)  # Ensure fade is float32
                fade_chunk = fade_chunk * fade[:, np.newaxis]  # Apply fade to both channels
                current_stream.write(fade_chunk)
                break

            current_stream.write(stereo_chunk)
            pos += CHUNK_SIZE

    # Create a new stream with 2 channels
    current_stream = sd.OutputStream(
        samplerate=sample_rate,
        channels=2,
        dtype=np.float32
    )

    # Start the stream
    current_stream.start()

    # Start the audio thread
    current_thread = threading.Thread(target=audio_thread)
    current_thread.start()

    # Toggle channel for next call
    current_channel = 1 - current_channel  # Alternates between 0 and 1

def monitor_midi():
    midi_in = rtmidi.MidiIn()
    midi_out = rtmidi.MidiOut()
    if midi_in.get_port_count() > 0:
        midi_in.open_port(0)
        midi_out.open_port(0)
        print('listening')
        while True:
            msg = midi_in.get_message()
            if msg and msg[0][0] == 144 and msg[0][2] != 0:
                print(msg)
                play_sample(msg[0][1] - 60)



def save_sample(sample, sr):
    sf.write('output.wav', sample, sr)

def play_sample(pitch):
    print('changing pitch')
    sample = librosa.effects.pitch_shift(sound, sr=sr, n_steps=pitch)
    play_audio(sample, sr)
    # save_sample(sample, sr)
    # playsound('output.wav', sr)
    
def play_sample_with_pedalboard(pitch):
    sample = librosa.effects.pitch_shift(sound, sr=sr, n_steps=pitch)
    pedalboard = get_pedalboard()
    sample = apply_pedalboard(sample, sr, pedalboard)
    play_audio(sample, sr)
    
   
def keys(stdscr):
    stdscr.nodelay(True)  # Don't block waiting for key press
    stdscr.clear()
    stdscr.addstr("Press keys A-H. Ctrl+C to quit.\n")

    key_map = {'a': 0, 's': 1, 'd': 2, 'f': 3, 'g': 4, 'h': 5}

    while True:
        key = stdscr.getch()
        if key != -1:
            try:
                char = chr(key)
                if char in 'asdfgh':
                    stdscr.addstr(f"You pressed: {char.upper()}\n")
                    pitch_shift = key_map[char]  # Map 'a' to 0, 's' to 1, etc.
                    play_sample_with_pedalboard(pitch_shift)
                    stdscr.refresh()
            except:
                pass


while True:
    curses.wrapper(keys)
# monitor_midi()
# play_sample(12)
# print('hello')
# time.sleep(0.5)
# play_sample(0)