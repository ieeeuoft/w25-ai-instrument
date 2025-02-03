import rtmidi
import soundfile as sf
from playsound import playsound
import librosa

sample_path = 'Cymatics - KEYS Flying - C.wav'
sound, sr = librosa.load(sample_path)

def monitor_midi():
    midi_in = rtmidi.MidiIn()
    midi_out = rtmidi.MidiOut()
    midi_in.open_port(0)
    midi_out.open_port(0)
    while True:
        msg = midi_in.get_message()
        if msg:
            if msg[0][1] == 60 and msg[0][2] != 0:
                playsound('Cymatics - Heater Kick 26.wav')
            print(msg)
            
def save_sample(sample, sr):
    sf.write('output.wav', sample, sr)

def play_sample(pitch):
    sample = librosa.effects.pitch_shift(sound, sr=sr, n_steps=pitch)
    save_sample(sample, sr)
    playsound('output.wav', sr)
    
    

play_sample(12)
play_sample(-12)