from text_to_filename import text_to_filename
from pynput import keyboard
import threading
import time
import zmq

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
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)  # Changed to PUSH socket
    socket.connect("tcp://localhost:5556")  # Connect to a different port for PUSH/PULL
    
    print("Sample loader started. Waiting for input...")
    
    while True:
        try:
            # Get initial input
            text = input('Enter a description of the sound you want to load: ')
            filename = text_to_filename(text, 'samples.csv')
            full_path = 'samples/' + filename
            
            # Send file change message
            file_change_msg = ((255, full_path), 0)  # Type 255 for file change
            socket.send_pyobj(file_change_msg)
            print(f"Sent file change message for: {full_path}")
            
            print("Monitoring MIDI input. Press 'u' to change sample.")
            
            # Start keyboard monitoring
            key_monitor.start()
            
            # Wait for key press
            while not key_monitor.key_pressed:
                time.sleep(0.1)
            
            # Reset for next sample
            if key_monitor.key_pressed:
                print("\nChanging sample...")
                continue
                
        except KeyboardInterrupt:
            key_monitor.stop()
            socket.close()
            context.term()
            print("Exiting...")
            break

if __name__ == "__main__":
    main()
    