#!/usr/bin/env python3

import pyaudio
import wave
import sys
import time

def test_microphone(device_name):
    # Initialize PyAudio
    p = pyaudio.PyAudio()
    
    device_found = False
    
    # Print available audio devices
    print("\nAvailable Audio Input Devices:")
    for i in range(p.get_device_count()):
        dev_info = p.get_device_info_by_index(i)
        if dev_info['maxInputChannels'] > 0:  # Only show input devices
            print(f"Device {i}: {dev_info['name']}")
            if dev_info['name'] == device_name:
                device_name = i
                device_found = True
                break
            
    print(p.get_default_input_device_info())
    
    # Get default input device info
    if device_found is False:
        device_name = None
        default_input = p.get_default_input_device_info()
        print(f"\nUsing default input device: {default_input['name']}")
    else:
        default_input = p.get_device_info_by_index(device_name)
        print(f"\nUsing input device: {default_input['name']}")
        
    # print(p.get_device_info_by_index(device_name))
        
    # Set recording parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 48000
    RECORD_SECONDS = 5
    
    try:
        # Open audio stream
        stream = p.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       input_device_index=device_name,
                       frames_per_buffer=CHUNK)
        
        print("Recording 5 seconds of audio...")
        
        # Record audio
        frames = []
        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            frames.append(data)
            
        print("Finished recording")
        
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        
        # Save the recorded data as a WAV file
        wf = wave.open("test_microphone.wav", 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print("Saved audio to test_microphone.wav")
        return True
        
    except Exception as e:
        print(f"Error recording audio: {e}")
        return False
    finally:
        # Terminate PyAudio
        p.terminate()
        
        
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

if __name__ == "__main__":
    success = record_audio(seconds=5, output_filename="output.wav")
    sys.exit(0 if success else 1)