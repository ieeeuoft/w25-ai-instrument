from midi.midi2 import monitor_midi
from text_to_filename import text_to_filename
from pynput import keyboard
import threading
import time

class KeyMonitor:
    def __init__(self):
        self.key_pressed = False
        self.listener = None

    def on_press(self, key):
        try:
            if key.char == 'u':
                self.key_pressed = True
                return False  # Stop listener
        except AttributeError:
            pass
        return True  # Continue listener

    def start(self):
        self.key_pressed = False
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()

def main():
    key_monitor = KeyMonitor()
    
    while True:
        # Get initial input
        text = input('Enter a description of the sound you want to load: ')
        filename = text_to_filename(text, 'samples.csv')
        
        # Start MIDI monitoring in a separate thread
        midi_thread = threading.Thread(target=monitor_midi, args=('samples/' + filename,))
        midi_thread.start()
        
        print("Monitoring MIDI input. Press 'u' to change sample.")
        
        # Start keyboard monitoring
        key_monitor.start()
        
        # Wait for key press or MIDI thread to finish
        while not key_monitor.key_pressed and midi_thread.is_alive():
            time.sleep(0.1)
        
        # Stop the current MIDI monitoring
        midi_thread.join(timeout=0.1)  # Give it a small timeout to clean up
        key_monitor.stop()
        
        if key_monitor.key_pressed:
            print("\nChanging sample...")
            continue

if __name__ == "__main__":
    main()
    