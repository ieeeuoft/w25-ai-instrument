import sounddevice as sd
import numpy as np
import soundfile as sf
from scipy.signal import resample
import threading
import time
import zmq
from midi.effectboard import EffectBoard
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:5555")
socket.setsockopt_string(zmq.SUBSCRIBE, '')

# Initialize with default sample
data, sr = sf.read("samples/C Major Piano.wav")
active_notes = {}

# Release fade (in seconds)
RELEASE_TIME = 0.5
BLOCK_SIZE = 512

if data.ndim == 1:
    data = data[:, np.newaxis]  # convert mono to (n, 1)
    
def midi_note_to_semitone(note, base_note=60):
    return note - base_note  # Assuming sample was recorded at MIDI note 60 (C4)

def load_sample(filename):
    global data, sr
    try:
        data, sr = sf.read(filename)
        print(f"Raw loaded sample shape: {data.shape}, Sample rate: {sr}")
        
        # Convert stereo to mono by averaging channels
        if data.ndim > 1:
            data = np.mean(data, axis=1)  # Average channels to mono
            print(f"Converted stereo to mono")
            
        data = data[:, np.newaxis]  # Ensure 2D shape (n_samples, 1)
        print(f"Final sample shape: {data.shape}")
        print(f"Loaded new sample: {filename}")
        return True
    except Exception as e:
        print(f"Error loading sample {filename}: {e}")
        return False
    
def pitch_shift(audio_data, semitones):
    ratio = 2 ** (semitones / 12)
    new_length = int(len(audio_data) / ratio)

    if audio_data.ndim == 1:
        shifted = resample(audio_data, new_length)
    else:
        shifted = np.zeros((new_length, audio_data.shape[1]))
        for ch in range(audio_data.shape[1]):
            shifted[:, ch] = resample(audio_data[:, ch], new_length)
    
    # Normalize the output to prevent clipping
    max_amplitude = np.max(np.abs(shifted))
    if max_amplitude > 0:
        shifted = shifted / max_amplitude * 0.7  # Scale to 70% of maximum to leave headroom
    return shifted

def limit_audio(audio_data, threshold=0.8):
    """
    Apply simple limiting to audio data to prevent clipping.
    
    Args:
        audio_data (np.ndarray): Input audio data
        threshold (float): Amplitude threshold (0.0 to 1.0)
        
    Returns:
        np.ndarray: Limited audio data
    """
    max_amplitude = np.max(np.abs(audio_data))
    if max_amplitude > threshold:
        return audio_data * (threshold / max_amplitude)
    return audio_data

def create_pedalboard():
    board = EffectBoard()
    board.add_reverb(room_size=0.8, wet_level=0.3, dry_level=0.7)
    board.add_delay(delay_seconds=0.5, feedback=0.3, mix=0.5)
    board.add_distortion(drive_db=20)
    return board

class SamplePlayer(threading.Thread):
    def __init__(self, audio_data, use_pedalboard=True):
        super().__init__()
        self.audio_data = audio_data
        self.playing = True
        self.stream = sd.OutputStream(samplerate=sr, channels=1, callback=self.callback, blocksize=BLOCK_SIZE)  # Smaller frame size
        self.pointer = 0
        self.lock = threading.Lock()
        self.fade = []
        self.fade_time = 0
        self.pedalboard = create_pedalboard() if use_pedalboard else None
    def run(self):
        self.stream.start()
        while self.stream.active:
            time.sleep(0.01)

    def stop(self):
        with self.lock:
            self.playing = False
            
    def callback(self, outdata, frames, time_info, status):
        with self.lock:
            if not self.playing:
                # Apply release fade
                release_samples = int(RELEASE_TIME * sr)
                if len(self.fade) == 0:
                    fade = np.linspace(1, 0, num=min(release_samples, max(len(self.audio_data) - self.pointer, 0)))
                    self.fade = fade
                if self.pointer < len(self.audio_data) and self.fade_time < RELEASE_TIME:
                    remaining = self.audio_data[self.pointer:self.pointer + frames]
                    
                    # Ensure remaining is mono before applying fade
                    if remaining.ndim > 1:
                        remaining = np.mean(remaining, axis=1)
                        remaining = remaining[:, np.newaxis]
                    
                    remaining = remaining * self.fade[:min(len(self.fade), frames)]
                    remaining = remaining[:, 0]  # Convert to 1D for output
                    outdata[:len(remaining), 0] = remaining
                    outdata[len(remaining):, 0].fill(0)
                    self.pointer += frames
                    self.fade = self.fade[frames:]
                    self.fade_time += frames / sr
                else:
                    print("finished fading")
                    outdata.fill(0)
                    self.fade = []
                    raise sd.CallbackStop()
                return

            if self.pointer >= len(self.audio_data):
                outdata.fill(0)
                raise sd.CallbackStop()
            
            chunk = self.audio_data[self.pointer:self.pointer + frames]
            if chunk.ndim == 1:
                chunk = chunk[:, np.newaxis]
                
            if self.pedalboard:
                chunk = self.pedalboard.apply(chunk, sr)
            
            # Apply limiting using the new function
            chunk = limit_audio(chunk, threshold=0.8)
            # print("chunk.shape", chunk.shape)
            # print("outdata.shape", outdata.shape)
            # print(chunk)
            # if chunk.shape[1] == 2:
            #     chunk = chunk[:, 0:1]
            # print("chunk.shape", chunk.shape)
            outdata[:len(chunk)] = chunk
            if len(chunk) < frames:
                outdata[len(chunk):] = 0

            self.pointer += frames

print("Sampler started. Waiting for MIDI messages...")
while True:
    try:
        msg = socket.recv_pyobj()
        print("Received message", msg)
        
        # Check if this is a file change message (type 255)
        if isinstance(msg, tuple) and len(msg) > 0 and msg[0][0] == 255:
            filename = msg[0][1]  # The filename is in the second byte
            if load_sample(filename):
                # Stop all currently playing notes
                for note, player in list(active_notes.items()):
                    player.stop()
                    del active_notes[note]
            continue
            
        # Handle regular MIDI messages (type 144)
        if isinstance(msg, tuple) and len(msg) > 0 and msg[0][0] == 144:
            print("Received MIDI", msg)
            note = msg[0][1]
            velocity = msg[0][2]
            if velocity > 0:
                semitone = midi_note_to_semitone(note)
                # If note exists, stop it first
                if note in active_notes:
                    active_notes[note].stop()
                    del active_notes[note]
                # Create new player
                player = SamplePlayer(pitch_shift(data, semitone), use_pedalboard=False)
                active_notes[note] = player
                active_notes[note].start()
            elif velocity == 0 and note in active_notes:
                active_notes[note].stop()
                # Don't delete from active_notes here - let the fade complete first
            
    except zmq.ZMQError:
        pass
    except KeyboardInterrupt:
        break