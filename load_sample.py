from midi.midi2 import monitor_midi, monitor_stop_flag
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
    midi_thread = None
    global monitor_stop_flag
    
    while True:
        try:
            # Get initial input
            text = input('Enter a description of the sound you want to load: ')
            filename = text_to_filename(text, 'samples.csv')
            
            # Stop any existing MIDI thread
            if midi_thread and midi_thread.is_alive():
                monitor_stop_flag = True  # Signal the thread to stop
                midi_thread.join(timeout=1.0)  # Wait for it to stop
                if midi_thread.is_alive():
                    print("Warning: Previous MIDI thread did not stop cleanly")
            
            # Reset stop flag and start new MIDI monitoring
            monitor_stop_flag = False
            midi_thread = threading.Thread(target=monitor_midi, args=('samples/' + filename,))
            midi_thread.daemon = True  # Make thread daemon so it exits when main program exits
            midi_thread.start()
            
            print("Monitoring MIDI input. Press 'u' to change sample.")
            
            # Start keyboard monitoring
            key_monitor.start()
            
            # Wait for key press or MIDI thread to finish
            while not key_monitor.key_pressed and midi_thread.is_alive():
                time.sleep(0.1)
            
            # Stop the current MIDI monitoring
            if key_monitor.key_pressed:
                print("\nChanging sample...")
                monitor_stop_flag = True  # Signal the thread to stop
                midi_thread.join(timeout=0.5)  # Wait for it to stop
                midi_thread = None
                filename = None
                continue
                
        except KeyboardInterrupt:
            if midi_thread and midi_thread.is_alive():
                monitor_stop_flag = True  # Signal the thread to stop
                midi_thread.join(timeout=0.5)
            
            key_monitor.stop()
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
    