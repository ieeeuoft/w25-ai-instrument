import rtmidi
import soundfile as sf
import sounddevice as sd
import librosa
import time
import threading
import numpy as np
from pedalboard import Pedalboard, Chorus, Reverb

sample_path = 'C Major Piano.wav'
sound, sr = librosa.load(sample_path)

reverb_board = Pedalboard([Reverb(room_size=0.25)])
chorus_board = Pedalboard([Chorus()])

# Add global variables to track current stream and playback
current_stream = None
current_thread = None
stop_flag = False
CHUNK_SIZE = 1024  # Process audio in smaller chunks
FADE_TIME = 5  # 30ms fade out
last_write_time = 0
wait_time = 0

def apply_pedalboard(audio, sr, pedalboard):
    return pedalboard(audio, sr)

def apply_fade(audio, fade_samples, fade_out=False):
    """Apply linear fade in/out to audio chunk"""
    fade = np.linspace(1, 0, fade_samples) if fade_out else np.linspace(0, 1, fade_samples)
    return audio * fade

def monitor_midi():
    midi_in = rtmidi.MidiIn()
    midi_out = rtmidi.MidiOut()
    print(midi_in.get_ports())
    if midi_in.get_port_count() > 0:
        midi_in.open_port(1)
        midi_out.open_port(1)
        print('listening')
        while True:
            msg = midi_in.get_message()
            if msg:
                print(msg)
            if msg and msg[0][0] == 144 and msg[0][2] != 0:
				print('yes')
                print(msg)
                play_sample(msg[0][1] - 60)

def play_audio(y, sr):
    """ Play audio in real-time with interruption support """
    global current_stream, current_thread, stop_flag
    
    # Stop any currently playing audio
    if current_stream is not None:
        stop_flag = True  # Signal the current thread to stop
        # time.sleep(wait_time)
        print('stopping stream')
        time.sleep(wait_time)
        current_stream.stop()
        current_stream = None
        if current_thread is not None:
            current_thread.join()
            
        # while current_stream.active:
        #     print(time.time() - last_write_time)
        #     # Wait until the latency period has passed after the last write
        #     if time.time() - last_write_time > 10:
        #         break
        #     time.sleep(0.1)  # Small sleep to prevent busy waiting
    
    stop_flag = False
    print('playing')
    
    # Create and start new stream
    current_stream = sd.OutputStream(samplerate=sr, channels=1)
    current_stream.start()
    
    # Start playback in a separate thread
    def audio_thread():
        global wait_time, last_write_time
        try:
            # Process audio in chunks
            pos = 0
            fade_samples = int(FADE_TIME * sr)
            
            while pos < len(y):
                chunk = y[pos:pos + CHUNK_SIZE]
                if len(chunk) == 0:
                    break
                
                    
                # Apply fade out if stopping
                if stop_flag:
                    fade_chunk = chunk[:fade_samples] if len(chunk) > fade_samples else chunk
                    chunk = apply_fade(fade_chunk, len(fade_chunk), fade_out=True)
                    wait_time = len(chunk) / sr + current_stream.latency
                    print('wait time', wait_time)
                    last_write_time = time.time()
                    current_stream.write(chunk)
                    break
                
                current_stream.write(chunk)
                pos += CHUNK_SIZE
                
        except Exception as e:
            print(f"Audio playback error: {e}")
    
    current_thread = threading.Thread(target=audio_thread)
    current_thread.start()

def save_sample(sample, sr):
    sf.write('output.wav', sample, sr)

def play_sample(pitch):
    print('changing pitch')
    sample = librosa.effects.pitch_shift(sound, sr=sr, n_steps=pitch)
    play_audio(sample, sr)
    # save_sample(sample, sr)
    # playsound('output.wav', sr)
    
def play_sample_with_pedalboard(pitch, pedalboard):
    sample = librosa.effects.pitch_shift(sound, sr=sr, n_steps=pitch)
    sample = apply_pedalboard(sample, sr, pedalboard)
    play_audio(sample, sr)
    
   
# play_sample(0)
# time.sleep(2)
# play_sample_with_pedalboard(0, chorus_board)
# time.sleep(2)
# play_sample_with_pedalboard(0, reverb_board)
monitor_midi()
# play_sample(12)
# print('hello')
# time.sleep(0.5)
# play_sample(0)
