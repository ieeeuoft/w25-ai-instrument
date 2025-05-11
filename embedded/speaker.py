import sounddevice as sd
import soundfile as sf
import numpy as np
from scipy import signal

def play_audio(mp3_path, volume_increase=1):
    # Set the desired audio device
    device_name = "USBAudio2.0"  # Name of the USB audio device
    device_info = sd.query_devices(device_name, 'output')
    device_id = device_info['index']
    device_sample_rate = device_info['default_samplerate']

    # Load the MP3 file
    data, sample_rate = sf.read(mp3_path, dtype='float32')

    # Resample if necessary
    if sample_rate != device_sample_rate:
        print(f"Resampling from {sample_rate} to {device_sample_rate}")
        number_of_samples = int(round(len(data) * float(device_sample_rate) / sample_rate))
        data = signal.resample(data, number_of_samples)
        sample_rate = device_sample_rate

    # Increase the volume (optional)
    data = data * volume_increase

    max_val = np.max(np.abs(data))
    target_max = 0.1 #decided for this specific device and where clipping occurs
    if max_val > 0:
        data = (data / max_val) * target_max
        
    if len(data.shape) == 1:
        data = np.stack((data, data), axis=1)

    try:
        # Play the audio using the specified device
        sd.play(data, samplerate=sample_rate, device=device_id)
        sd.wait()
        print("Audio played successfully")
    except sd.PortAudioError as e:
        print(f"Error playing audio: {e}")
        print(f"Supported sample rates for this device: {device_sample_rate}")
        
if __name__ == "__main__":
    play_audio("midi/C Major Piano.wav", volume_increase=0.3)