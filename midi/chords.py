import soundfile as sf
import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

chord_data = None
chord_position = 0

def shift_pitch(data, semitones):
    factor = 2 ** (semitones / 12.0)
    return resample_poly(data, int(len(data) * factor), len(data))

def callback(outdata, frames, time, status):
    global chord_data, chord_position

    if chord_data is None:
        outdata.fill(0)
        return

    end = chord_position + frames
    chunk = chord_data[chord_position:end]

    # Pad if chunk is too short
    if len(chunk) < frames:
        chunk = np.pad(chunk, ((0, frames - len(chunk)), (0, 0)), mode='constant')
        chord_data = None  # stop playback after this
        chord_position = 0
    else:
        chord_position = end

    outdata[:] = chunk

def get_chord(chord, base_data):
    note_to_semitones = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
    notes = chord.split(",")
    samples = []

    for note in notes:
        semitone = note_to_semitones[note.strip()]
        shifted = shift_pitch(base_data, semitone)
        samples.append(shifted)

    max_len = max([s.shape[0] for s in samples])
    aligned = [
        np.pad(s, ((0, max_len - s.shape[0]), (0, 0)), mode='constant')
        for s in samples
    ]
    mix = sum(aligned)

    # Normalize to avoid clipping
    max_amp = np.max(np.abs(mix))
    if max_amp > 1.0:
        mix /= max_amp

    return mix.astype(np.float32)

# Load the base sample
data, samplerate = sf.read("C Major Piano.wav")
if data.ndim == 1:
    data = data[:, np.newaxis]  # convert mono to (n, 1)

# Start audio stream
stream = sd.OutputStream(samplerate=samplerate, channels=data.shape[1], blocksize=512, callback=callback)
stream.start()

# Example: Trigger a chord
chord_data = get_chord("C,E,G", data.copy())
chord_position = 0

print("Chord triggered! Non-blocking playback. Ctrl+C to exit.")
try:
    while True:
        pass  # keep program alive
except KeyboardInterrupt:
    stream.stop()
    stream.close()
    print("Stopped.")


