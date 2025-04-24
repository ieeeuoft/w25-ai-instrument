import numpy as np
import soundfile as sf
import sounddevice as sd
import rtmidi
import threading

data, samplerate = sf.read("C Major Piano.wav")
original_note = 60

# Convert mono to stereo if needed
if len(data.shape) == 1:
    data = np.column_stack((data, data))  # Duplicate mono channel to create stereo

print(data.shape)

# Keep track of active voices
active_voices = []
voices_lock = threading.Lock()

# Basic pitch shift via naive resampling
def pitch_shift(sample, semitones):
    factor = 2 ** (semitones / 12.0)
    indices = np.round(np.arange(0, len(sample), factor)).astype(int)
    indices = indices[indices < len(sample)]
    return sample[indices]

# Voice class to track each note
class Voice:
    def __init__(self, note, sample):
        self.note = note
        self.sample = sample
        self.position = 0

    def get_samples(self, frames):
        end = self.position + frames
        chunk = self.sample[self.position:end]
        self.position = end
        return chunk

    def is_done(self):
        return self.position >= len(self.sample)

# Stream callback to mix all voices
def audio_callback(outdata, frames, time, status):
    global active_voices
    mix = np.zeros((frames, data.shape[1]), dtype=np.float32)

    with voices_lock:
        for voice in active_voices[:]:
            chunk = voice.get_samples(frames)
            if len(chunk) < frames:
                # Pad with zeros if needed
                chunk = np.pad(chunk, ((0, frames - len(chunk)), (0, 0)))
            mix += chunk
            if voice.is_done():
                active_voices.remove(voice)

    outdata[:] = mix

# Set up audio stream
stream = sd.OutputStream(channels=data.shape[1], samplerate=samplerate, callback=audio_callback)
stream.start()

# Handle MIDI input
def midi_callback(message_data, time_stamp):
    message, delta_time = message_data
    status = message[0] & 0xF0
    note = message[1]
    velocity = message[2]

    if status == 0x90 and velocity > 0:
        semitone_shift = note - original_note
        shifted = pitch_shift(data, semitone_shift).astype(np.float32)
        voice = Voice(note, shifted)
        with voices_lock:
            active_voices.append(voice)

# MIDI input setup
midiin = rtmidi.MidiIn()
ports = midiin.get_ports()
if ports:
    midiin.open_port(0)
else:
    midiin.open_virtual_port("Polyphonic Piano")
midiin.set_callback(midi_callback)

# Keep app alive
print("Playing... Ctrl+C to stop.")
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting.")
    stream.stop()
    stream.close()
    midiin.close_port()
