import soundfile as sf
import sounddevice as sd
import numpy as np
import signal

# Your audio effect function (replace with pedalboard if needed)
def effect_chain(input_block, sample_rate):
    gain = 0.8
    delayed = np.roll(input_block, 2000)
    return gain * input_block + 0.3 * delayed

# Graceful interrupt
stop_flag = False
def handle_interrupt(signum, frame):
    global stop_flag
    stop_flag = True
signal.signal(signal.SIGINT, handle_interrupt)

# Audio file setup
filename = 'C Major Piano.wav'
block_size = 1024

with sf.SoundFile(filename) as f:
    samplerate = f.samplerate
    channels = f.channels

    # Create an output stream
    with sd.OutputStream(
        samplerate=samplerate,
        channels=channels,
        blocksize=block_size,
        dtype='float32'
    ) as stream:

        print("Streaming... Press Ctrl+C to stop.")
        while not stop_flag and f.tell() < len(f):
            block = f.read(block_size, dtype='float32')

            # Handle end-of-file (padding if block is too short)
            if len(block) < block_size:
                block = np.pad(block, ((0, block_size - len(block)), (0, 0)), mode='constant')

            # Apply your effect
            # if channels == 1:
            #     block = block[:, 0]  # Flatten for mono
            processed = effect_chain(block, samplerate)

            # Make sure shape matches output stream
            if channels == 1:
                stream.write(processed.reshape(-1, 1))
            else:
                stream.write(processed)
